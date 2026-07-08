# Ability Generator - schema v2: the LLM enum-picks tier words at birth;
# battle/constants.py maps the words to numbers (numeric-core initiative).
# Split out of generator.py (one concept per file): monster BIRTH lives
# there, ability AUTHORING lives here. generator.py re-exports the entry
# points so call sites (workflows, growth, returning, evolution, dungeon
# handlers) keep importing from one place.

from backend.core.events import emit_monster_ability_added
from backend.game.monster import cmdts_data
from backend.models.ability import Ability
from backend.models.monster import Monster


def generate_ability(monster: Monster, growth_context: str = ''):
    """Author ONE new ability for a monster - words from code-owned
    ladders, one flavor sentence, everything normalized before storage"""
    # Generation goes through generator.py's build_and_generate BINDING
    # (not a fresh import) - offline suites stub that exact attribute
    from backend.game.monster import generator

    variables = _build_ability_variables(monster, growth_context)
    parsed_data = generator.build_and_generate('generate_ability', 'ability_generation', variables)

    ability = Ability.create_from_llm_data(monster.id, _normalize_ability_v2(parsed_data))
    ability.save()

    # The monster has a new ability
    emit_monster_ability_added(monster.id, ability.to_dict())

    return ability


def generate_ability_by_id(monster_id):
    monster = Monster.query.get(monster_id)
    return generate_ability(monster)


def _build_ability_variables(monster: Monster, growth_context: str = ''):
    from backend.game.battle import constants as battle_constants
    from backend.game.monster.context_builder import ability_line
    from backend.game.monster.generator import _class_text

    # Format existing abilities (structured words included so the new
    # ability differentiates against what the monster already has)
    existing_abilities = monster.abilities
    abilities_text = (
        "\n".join(f"- {ability_line(ability)}" for ability in existing_abilities)
        if existing_abilities
        else "None (this will be their first ability)"
    )

    persona = monster.persona or {}
    ecology = monster.ecology or {}

    # Growth/return abilities carry the WHY into the prompt; ordinary
    # generation leaves this block empty
    growth_block = (
        f"\n--- Why this ability is being learned NOW ---\n{growth_context}\n"
        if growth_context
        else ''
    )

    effect_options = "\n".join(
        f"- {keyword}: {gloss}" for keyword, gloss in battle_constants.ABILITY_EFFECTS.items()
    )

    return {
        'growth_context': growth_block,
        'monster_name': monster.name,
        'monster_species': monster.species,
        'monster_description': monster.description,
        'monster_personality': ', '.join(monster.personality_traits or []),
        'monster_role': monster.party_role or 'unknown',
        'monster_class': _class_text(monster.class_taxonomy),
        'monster_elements': ', '.join(ecology.get('elemental_affinities') or []) or 'none',
        'monster_wish': persona.get('core_wish', 'unknown'),
        'existing_abilities_text': abilities_text,
        # Option lists straight from the constants so prompt and code
        # can never drift apart
        'type_options': cmdts_data.options_line(battle_constants.ABILITY_TYPES),
        'element_options': cmdts_data.options_line(cmdts_data.ELEMENTS),
        'power_options': cmdts_data.options_line(list(battle_constants.POWER_TIERS)),
        'cost_options': cmdts_data.options_line(battle_constants.ABILITY_COST_TIERS),
        'target_options': cmdts_data.options_line(battle_constants.ABILITY_TARGETS),
        'effect_options': effect_options,
    }


def _normalize_ability_v2(data: dict) -> dict:
    """Snap the LLM's ability pick onto the code-owned ladders. Words the
    model got wrong fall back to sane defaults; the flavor sentence maps
    into the legacy description column (display only, never parsed)."""
    from backend.game.battle import constants as battle_constants
    from backend.game.monster.generator import _clean_str

    ability_type = cmdts_data.normalize_choice(
        data.get('type'), battle_constants.ABILITY_TYPES, 'special'
    )
    default_pool = battle_constants.ABILITY_POOL_BY_TYPE.get(ability_type, 'stamina')
    effect = cmdts_data.normalize_choice(
        data.get('effect'), list(battle_constants.ABILITY_EFFECTS), 'damage'
    )
    # An ability that harms aims at an enemy by default; anything else self
    default_target = 'enemy' if effect in ('damage', 'drain', 'slow') else 'self'

    return {
        'name': _clean_str(data.get('name'), 'Unnamed Ability', 40),
        'description': _clean_str(
            data.get('flavor') or data.get('description'), 'A mysterious power.', 120
        ),
        'type': ability_type,
        'element': cmdts_data.normalize_choice(data.get('element'), cmdts_data.ELEMENTS, None),
        'power': cmdts_data.normalize_choice(
            data.get('power'), list(battle_constants.POWER_TIERS), 'potent'
        ),
        'cost_pool': cmdts_data.normalize_choice(
            data.get('cost_pool'), ['stamina', 'mana'], default_pool
        ),
        'cost': cmdts_data.normalize_choice(
            data.get('cost'), battle_constants.ABILITY_COST_TIERS, 'moderate'
        ),
        'target': cmdts_data.normalize_choice(
            data.get('target'), battle_constants.ABILITY_TARGETS, default_target
        ),
        'effect': effect,
    }
