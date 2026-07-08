# Numeric Core — Ability Schema v2 + 2-Call Birth — Plan

**Status:** IMPLEMENTED (2026-07-08) — NC-M1..M3 landed, all verified
live against the local model (see Live validation below). Plan locked
per the 2026-07-08 delegation (Aaron pre-approved Claude's
recommendations).
**Branch:** `feature/numeric-core` — one milestone commit per milestone,
prefix `NC-M#`.
**Parent:** [local-first-pivot.md](local-first-pivot.md) — this is child
initiative 2. Initiative 3 (math battle engine) consumes everything
built here.

The pivot's core move: the LLM authors content and parameters at BIRTH;
code alone resolves runtime outcomes. This initiative gives abilities
numbers (via tier words) and shrinks the 6-call monster birth to 2
calls — without touching the battle loop (that's initiative 3). The
referee keeps running through this whole initiative; it just starts
reading structured ability words instead of interpreting free prose,
which should *improve* its calibration immediately.

## Locked decisions

1. **Ability schema v2** — everything enum-picked except name and flavor:
   - `name` ≤ 40 chars
   - `flavor` ONE sentence ≤ 120 chars — display only, never parsed
     (stored in the existing `description` column; no frontend break)
   - `ability_type` attack|defense|support|special|movement|utility (existing)
   - `element` from `cmdts_data.ELEMENTS`, or none (NULL)
   - `power` tier word: feeble|modest|potent|mighty|legendary
   - `cost_pool` stamina|mana (default by type: `ABILITY_POOL_BY_TYPE`)
   - `cost` tier word: none|minor|moderate|heavy (the EXISTING
     `RESOURCE_DELTAS` words — referee and pools already speak them)
   - `target` self|ally|enemy|all_enemies|all_allies
   - `effect` ONE keyword: damage|guard|heal|restore|haste|slow|drain|rally
2. **Numbers live in `battle/constants.py`** next to the ladders they
   replace (per the pivot doc): `POWER_TIERS` (word → multiplier, for
   initiative 3), `ABILITY_EFFECTS` (keyword → gloss now, implementation
   in initiative 3), `ABILITY_TARGETS`, `ABILITY_COST_TIERS`.
   Rebalancing = editing constants, never regenerating content.
3. **v2 columns are nullable.** Legacy abilities (no tier words) keep
   working — prompt renderers fall back to prose-only lines. Migration
   is New Game; no backfill.
4. **`generate_initial_abilities` is deleted.** It was already dead —
   every call site (monster workflows, player workflow, all three
   dungeon handlers) calls `generate_ability` twice. The template, its
   budget entry, and its test row go.
5. **Births are spark + voice (2 calls), replacing the 5-stage chain.**
   - Call 1 `monster_spark`: name, species/race label, element(s),
     party_role, size_class, temperament, sapience, visual one-liner +
     primary colors. Code then rolls rarity and derives stats
     (existing `derive_stats`) — enough for card art and battle.
   - Call 2 `monster_voice`: 2–3 personality traits, speech_style, one
     want (`core_wish`), battle_line — enough for talk/negotiation/chat
     to stay in character.
   - Taxonomy chain, ecology detail, inner life, secret, backstory are
     NOT generated at birth — they accrue in play (initiative 4) or
     stay API-repo-only. Columns stay; new births write minimal shapes.
6. **`temperament` is a monster column** (new, String(20)):
   aggressive|cunning|protective|craven|stoic|mischievous — picked at
   spark, unused by code until initiative 3's enemy-action policies
   (prompts may read it immediately as flavor).
7. **Public generator entry points keep their signatures**
   (`generate_base_monster`, `generate_contextual_monster`,
   `generate_ability(monster, growth_context)`) so workflows, dungeon
   handlers, growth, returning, and evolution don't change call sites.
   Workflow step names are untouched (frontend contract).
8. **Schema changes ship with migration scripts** per the
   `add_affinity_column.py` precedent, plus `tests/harness.py` PATCH
   entries so the test DB self-heals. `reset_db.py`/New Game remains
   the clean path.
9. **Player creation stays as-is** (pivot verdict: keep) — but the
   player monster's abilities go v2 automatically via the shared
   `generate_ability` path.

## Milestones

- **NC-M1 — Ability schema v2.** Constants in `battle/constants.py`;
  nullable columns on `abilities` (+ migration script + harness patch);
  `generate_ability` template rewritten to enum-pick JSON with
  normalization (`normalize_choice` per field, silent fallbacks);
  one ability-line renderer used by monster context blocks so every
  prompt shows the structured words; `generate_initial_abilities`
  deleted everywhere; budgets updated; suites green.
- **NC-M2 — 2-call birth.** `monster_spark` + `monster_voice` templates
  (budget class `structured`); `generator.py` rewritten around the
  2-call chain (public signatures stable); `temperament` column (+
  migration + harness patch); minimal taxonomy/ecology/persona/
  appearance shapes documented in `cmdts_data.py`; card art fed from
  spark's visuals; the five 5-stage templates deleted; budgets/tests
  updated; suites green.
- **NC-M3 — Alignment + close-out.** Growth/returning/evolution ability
  paths verified on v2; eval replay sanity pass on the new templates
  against the live local model; `docs/architecture.md` (generation
  section) + `docs/tuning.md` (new knobs: tier maps, temperament) +
  `docs/api/data-models.md` ability shape updated; both plan docs
  truthful; suites green.

## Verification checklist

- [x] `python -m pytest` green at every milestone commit (17 suites)
- [x] `ruff check backend setup tools` clean; file-size ceiling respected
- [x] New templates parse clean against the live local model — validated
      through REAL play rather than replay (see Deviations): eval report
      over the live window shows `monster_spark` 4/4, `monster_voice`
      4/4, `generate_ability` 8/8 — zero failed/retry/parse-fail rows
- [x] Fresh monsters birth with 2 calls: monster 71 "Rustle" (Caprifolia
      Sprite — mischievous, bestial, nature+air, full look/colors) and
      three more born in live dungeon play, all with stats, temperament,
      and v2 abilities whose words all landed on their ladders
- [x] Battle runs end-to-end with v2 abilities: a live 2v2 in "The
      Glistening Maw" vs two v2-born enemies (Chymos, Chime) — referee
      resolved attacks and abilities from structured words over 7 turns,
      pools stepped correctly, talk ended it (`yielded` victory +
      CoCaTok). A v2-born monster (Cristol) also carried a full
      in-character dialogue encounter on voice-call data alone

## Live validation (NC-M3, July 8 2026)

Birth cost fell from ~1,263 avg output tokens across 5 calls to ~290
across 2 (spark avg 156, voice avg 134) — a 77% cut per monster, with
zero parse failures in the live window. v2 `generate_ability` averages
83 tokens against its 200 cap.

## Deviations log

- **2026-07-08 — validation via live play instead of eval replay.** The
  replay tool re-runs STORED prompts byte-exact, so it cannot exercise
  NEW template wording. Validation ran as real gameplay instead (a
  monster generation workflow + a dungeon run with births, dialogue,
  and a 2v2 battle), which covers integration too. N=4 per birth
  template rather than the planned N≥5 — accepted; every row parsed.
- **2026-07-08 — `generate_ability` budget class one_liner → structured.**
  The v2 JSON carries 9 fields; 120 tokens was the one-sentence-prose
  cap. Now `structured` with max_tokens 200 (live avg 83).
- **2026-07-08 — ability authoring split into its own module.**
  `monster/ability_generator.py` (the 500-line ceiling + one concept
  per file); `generator.py` re-exports, so call sites and test
  monkeypatches are unchanged.
- **2026-07-08 — `writing_story` workflow step retired.** The frontend
  never keyed off it for the monster workflow (only player creation
  maps step names, and that workflow is untouched); the surviving steps
  keep their old names.
