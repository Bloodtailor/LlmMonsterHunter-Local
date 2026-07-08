# Generation budgets - the ONE place output-length policy lives.
# Every prompt template is mapped to a budget class; the class ceiling
# is the most max_tokens that template may declare. The offline suite
# test_prompt_budgets.py enforces both directions (every template
# mapped, every cap under its ceiling), so a new template cannot ship
# without declaring a class and a cap bump is a deliberate, reviewed
# change - the file-size-ceiling precedent, applied to prompts.
#
# WHY budgets at all: this repo is local-first (docs/plans/
# local-first-pivot.md). On a 7B model every extra token costs latency
# (~15-30 tok/s measured) and long free-prose answers are where small
# models drift. The July 2026 baseline (docs/plans/text-diet.md) showed
# ungoverned caps: 800 tokens for a camp scene averaging 29 seconds,
# 250 for a one-word goal check.

# Class ceilings. Values are MAXIMUMS a template's max_tokens may not
# exceed - individual templates usually sit below them.
BUDGET_CLASSES = {
    # One-word / enum JSON answers ({"next": "..."}, {"answer": "no"})
    'word_answer': 80,
    # A single sentence (or a tiny JSON wrapping one sentence)
    'one_liner': 120,
    # 1-3 sentences of scene text, or small action JSON with a short
    # narration field
    'short_narration': 250,
    # Multi-field JSON authoring (monster stages, items, notices)
    'structured': 450,
    # The deliberate storytelling allowlist - the few moments the game
    # spends real tokens on prose (and the 6-path batch, which is six
    # short entries in one call)
    'storytelling': 550,
}

# Every template, by name (names must match backend/ai/llm/prompts/*.json).
TEMPLATE_CLASS = {
    # --- word answers ---
    'next_turn': 'word_answer',  # replaced by code in the math-battle initiative
    'goal_check': 'word_answer',
    # --- one-liners ---
    'turn_vanity': 'one_liner',
    'camp_spotlight': 'one_liner',
    'camp_restore': 'one_liner',
    'run_goal': 'one_liner',
    'generate_ability': 'one_liner',  # name + ONE-sentence description + type
    # --- short narration ---
    'entry_atmosphere': 'short_narration',
    'random_location': 'short_narration',
    'location_event': 'short_narration',
    'exit_narrative': 'short_narration',
    'exit_path': 'short_narration',
    'arrival_location': 'short_narration',
    'opening_scene': 'short_narration',
    'look_around': 'short_narration',
    'camp_scene': 'short_narration',  # was 800 - the baseline's worst offender
    'sneak_attempt': 'short_narration',
    'ambush_intro': 'short_narration',
    'encounter_vanity': 'short_narration',
    'monster_question': 'short_narration',
    'home_chat_reply': 'short_narration',
    'condense_history': 'short_narration',
    'defeat_reflection': 'short_narration',
    'reunion_scene': 'short_narration',
    'treasure_discovery': 'short_narration',
    'battle_arrival': 'short_narration',
    'battle_intro': 'short_narration',
    'battle_victory': 'short_narration',
    'battle_defeat': 'short_narration',
    'enemy_turn': 'short_narration',  # small action JSON (baseline avg 64 tokens)
    'ally_autonomous_turn': 'short_narration',
    'action_resolution': 'short_narration',  # referee JSON, 2-3 sentence narration
    'freeform_action_resolution': 'short_narration',
    'dungeon_ability_use': 'short_narration',
    'dungeon_item_use': 'short_narration',
    # --- structured JSON ---
    'door_choices': 'structured',
    'expedition_notices': 'structured',
    'monster_blueprint_identity': 'structured',
    'monster_blueprint_ecology': 'structured',
    'monster_inner_life': 'structured',
    'monster_social_self': 'structured',
    'monster_creative_text': 'structured',
    'player_options': 'structured',
    'player_blueprint': 'structured',
    'player_persona': 'structured',
    'player_story': 'structured',
    'generate_initial_abilities': 'structured',
    'evolution_form': 'structured',
    'evolution_persona': 'structured',
    'evolution_abilities': 'structured',
    'returning_transform': 'structured',
    'growth_reflection': 'structured',
    'treasure_item': 'structured',
    'reward_item': 'structured',
    'goal_reward_item': 'structured',
    'victory_cocatok': 'structured',
    'chat_memory_extraction': 'structured',
    # --- storytelling allowlist ---
    'run_chronicle': 'storytelling',
    'evolution_prose': 'storytelling',
    'evolution_narration': 'storytelling',
    'battle_summary': 'storytelling',
    'battle_talk': 'storytelling',  # negotiation is the game's soul - roomy, still capped
    'monster_dialogue_turn': 'storytelling',
    'path_choices': 'storytelling',  # a batch of 6 paths in one call, not one long text
}


def ceiling_for(template_name: str):
    """The max_tokens ceiling for a template, or None when unmapped
    (unmapped is a suite failure, not a silent default - on purpose)"""

    budget_class = TEMPLATE_CLASS.get(template_name)
    return BUDGET_CLASSES.get(budget_class) if budget_class else None
