# Monster Generator - the 2-CALL BIRTH: spark -> voice (numeric-core)
# Call 1 (spark) is everything code needs: identity words for stats
# (derive_stats), a temperament for battle policies, and a look for card
# art. Call 2 (voice) is everything TALK needs: traits, speech style, a
# want, a battle line. Depth beyond that (taxonomy chains, ecology,
# inner life, secrets, backstory) is NOT generated at birth - it accrues
# in play (progressive-depth initiative). The monster row is saved after
# spark and announced, then completed by voice (generation_stage:
# blueprint -> complete), emitting events the frontend streams.
# Normalization here guards LLM output, not our own code.

import random

from backend.core.events import emit_monster_created, emit_monster_updated
from backend.game.monster import cmdts_data
from backend.game.utils import build_and_generate
from backend.models.monster import Monster

WILDS_LOCATION_CONTEXT = "The untamed wilds of the realm, far from any charted place"

# ===== PUBLIC ENTRY POINTS (signatures stable for workflows) =====


def generate_base_monster():
    """Generate a complete monster of the open wilds (spark + voice)"""
    return _generate_monster_chain(WILDS_LOCATION_CONTEXT)


def generate_contextual_monster(location: dict):
    """Generate a complete monster that belongs to a specific dungeon
    location (and to the active expedition's theme, when a run is on)"""
    from backend.game.dungeon.run_context import themed_location_context

    return _generate_monster_chain(themed_location_context(location))


def _generate_monster_chain(location_context: str):
    monster = generate_monster_spark(location_context)
    monster = generate_monster_voice(monster)
    return monster


# ===== CALL 1: SPARK (identity words + look; code derives the stats) =====


def generate_monster_spark(location_context: str = WILDS_LOCATION_CONTEXT) -> Monster:
    """One call for everything CODE consumes: role/size words feed
    derive_stats, temperament feeds battle policies, the look feeds card
    art. Saves the monster (generation_stage='blueprint') and announces
    it to the game world."""

    rarity = cmdts_data.roll_rarity()

    spark_raw = build_and_generate(
        'monster_spark',
        'monster_generation',
        {
            'location_context': location_context,
            'rarity': rarity,
            'role_options': cmdts_data.options_line(cmdts_data.PARTY_ROLES),
            'size_options': cmdts_data.options_line(cmdts_data.SIZE_CLASSES),
            'temperament_options': cmdts_data.options_line(cmdts_data.TEMPERAMENTS),
            'sapience_options': cmdts_data.options_line(cmdts_data.SAPIENCE_LEVELS),
            'element_options': cmdts_data.options_line(cmdts_data.ELEMENTS),
        },
    )
    spark = _normalize_spark(spark_raw)

    stats = cmdts_data.derive_stats(spark['party_role'], rarity, spark['size_class'])

    monster = Monster(
        name=spark['name'],
        species=spark['species'],
        # The look serves as the first player-facing description too;
        # richer prose accrues in play, never at birth
        description=spark['look'],
        backstory=None,
        max_health=stats['health'],
        current_health=stats['health'],
        attack=stats['attack'],
        defense=stats['defense'],
        speed=stats['speed'],
        personality_traits=[],
        rarity=rarity,
        party_role=spark['party_role'],
        temperament=spark['temperament'],
        generation_stage='blueprint',
        # Minimal shapes: only the fields downstream prompts/art read.
        # Lineage chains and full ecology are progressive-depth material.
        taxonomy={
            'species': spark['species'],
            'race_label': spark['race_label'],
            'type_label': spark['race_label'],
        },
        class_taxonomy=[],
        ecology={
            'size_class': spark['size_class'],
            'sapience': spark['sapience'],
            'communication': spark['communication'],
            'elemental_affinities': spark['elements'],
        },
        persona=None,
        appearance={
            'visual_description': spark['look'],
            'primary_colors': spark['colors'],
            'distinguishing_features': [],
        },
        card_art_path=None,
    )
    monster.save()

    # Reload with relationships, then announce
    monster = Monster.get_monster_by_id(monster.id)
    emit_monster_created(monster.to_dict())

    return monster


# ===== CALL 2: VOICE (what talk, negotiation, and chat run on) =====


def generate_monster_voice(monster: Monster) -> Monster:
    """One call for everything SOCIAL: traits, speech style, a want, a
    battle line. Advances generation_stage to 'complete'."""

    voice = build_and_generate(
        'monster_voice',
        'monster_generation',
        {'spark_facts': _spark_facts_text(monster)},
    )

    monster.persona = {
        'core_wish': _clean_str(voice.get('want'), 'To find its place in the world'),
        'speech_style': _clean_str(voice.get('speech_style'), ''),
        'battle_line': _clean_str(voice.get('battle_line'), ''),
    }
    monster.personality_traits = _clean_list(voice.get('personality_traits'), ['mysterious'])[:3]
    monster.generation_stage = 'complete'
    monster.save()

    emit_monster_updated(monster.to_dict())
    return monster


def _normalize_spark(data: dict) -> dict:
    """Snap the spark onto curated enums; free-text fields get cleaned"""

    sapience = cmdts_data.normalize_choice(
        data.get('sapience'), cmdts_data.SAPIENCE_LEVELS, 'sapient'
    )
    name = _clean_str(data.get('name'), 'Unnamed Monster', 100)
    return {
        'name': name,
        'species': _clean_str(data.get('species'), f'{name} Kind', 100),
        'race_label': _clean_str(data.get('race_label'), 'Creature', 50),
        'party_role': cmdts_data.normalize_choice(
            data.get('party_role'), cmdts_data.PARTY_ROLES, random.choice(cmdts_data.PARTY_ROLES)
        ),
        'size_class': cmdts_data.normalize_choice(
            data.get('size_class'), cmdts_data.SIZE_CLASSES, 'medium'
        ),
        'temperament': cmdts_data.normalize_choice(
            data.get('temperament'), cmdts_data.TEMPERAMENTS, 'stoic'
        ),
        'sapience': sapience,
        'communication': ['speech'] if sapience in ('sapient', 'erudite') else ['none'],
        'elements': cmdts_data.normalize_multi(data.get('elements'), cmdts_data.ELEMENTS, []),
        'look': _clean_str(data.get('look'), 'A mysterious creature of the deep wilds.'),
        'colors': _clean_list(data.get('colors'), [])[:3],
    }


def _spark_facts_text(monster: Monster) -> str:
    """The spark's established facts as prompt context for the voice call"""

    taxonomy = monster.taxonomy or {}
    ecology = monster.ecology or {}
    elements = ", ".join(ecology.get('elemental_affinities') or []) or 'none'
    return (
        f"Name: {monster.name}\n"
        f"Species: {monster.species} (a {taxonomy.get('race_label') or monster.species})\n"
        f"Rarity: {monster.rarity} | Party role: {monster.party_role} | "
        f"Size: {ecology.get('size_class')} | Temperament: {monster.temperament}\n"
        f"Mind: {ecology.get('sapience')} | Elements: {elements}\n"
        f"Look: {monster.description}"
    )


# ===== ABILITIES AND CARD ART (signatures unchanged) =====

# Card art (generation + prompt composition) lives in card_art.py -
# art is a bonus, never a blocker. Ability authoring (schema v2) lives
# in ability_generator.py; re-exported here so every call site keeps
# one import home. The import sits below the helpers it needs
# (_clean_str, _class_text) to keep the cycle harmless.


# ===== NORMALIZATION (snap LLM output onto curated data) =====


def _clean_str(value, default, max_length=None):
    if isinstance(value, str) and value.strip():
        cleaned = value.strip()
        return cleaned[:max_length] if max_length else cleaned
    return default


def _clean_list(value, default):
    if isinstance(value, str) and value.strip():
        value = [part.strip() for part in value.split(',')]
    if isinstance(value, list):
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if cleaned:
            return cleaned
    return default


def _class_text(class_taxonomy) -> str:
    if not class_taxonomy:
        return 'untrained'
    parts = []
    for entry in class_taxonomy:
        chain = " > ".join(
            p
            for p in (entry.get('domain'), entry.get('discipline'), entry.get('specialization'))
            if p
        )
        parts.append(chain)
    return "; ".join(parts)


# Re-exported ability entry points (see the abilities note above). Sits
# at the bottom so ability_generator's lazy imports of _clean_str /
# _class_text always find them defined.
from backend.game.monster.ability_generator import (  # noqa: E402, F401
    generate_ability,
    generate_ability_by_id,
)
