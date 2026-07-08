# Local-First Pivot — Direction & Master Plan

**Status:** ACTIVE — survey complete; the four direction forks are
LOCKED (see below). Initiative 1 (text diet + eval harness) is IN
PROGRESS — see [text-diet.md](text-diet.md); later children get their
own plan docs as they start.
**Repo/branch:** this doc lives in `LlmMonsterHunter-Local`, the pivot's
home (see Deviations); each child initiative runs on its own
`feature/<initiative>` branch (`feature/text-diet` first).
**Scope note:** this is an UMBRELLA doc — the direction, the survey
evidence, and the question list. It does not replace per-initiative plan
docs; it spawns them.

## The decision (Aaron, July 7 2026)

LLM Monster Hunter splits into **two projects**:

- **THIS repo — `LlmMonsterHunter-Local`, local-first.** Forked from the
  original at PR #167, with #168 (the settings/DeepSeek provider seam)
  merged in during Diet-M0. Redesigned so a small local GGUF model
  (llama-cpp-python, 7B-class today) delivers a *good* game — not a
  degraded big-model game. Cloud APIs (the DeepSeek provider) remain an
  optional boost, never a requirement.
- **The original repo — `LlmMonsterHunter`, API-first.** Keeps the
  maximalist design built through July 2026: LLM-refereed battles, deep
  5-stage personas, heavy judgment features. It runs the 2026-07-07
  *cloud generation initiative* (≥1M-token context floor, ComfyUI →
  Gemini image API with reference-image evolution regen) — planned and
  tracked there, not here.
- **Card art stays local here.** ComfyUI + SDXL Turbo already fit
  consumer GPUs — the cloud image API belongs to the API-first repo.

**Why.** The current design puts the LLM in the *runtime judgment loop*:
refereeing action outcomes, picking turn order, judging goal progress,
choosing enemy actions. Judgment tasks are exactly where small models are
weakest — calibrated one-word rulings, large exact-schema JSON, long
context — and they are also the most *frequent* calls in the game. The
pivot moves the LLM to *generation-time authoring* (set stats, tiers, and
flavor once, when content is born) and lets code resolve runtime outcomes
with math.

The one-sentence philosophy change:

> Today: the LLM picks words at runtime; code maps words to effects.
> After: the LLM authors content and parameters at birth; code alone
> resolves what happens at runtime — the LLM speaks only in social
> moments (dialogue, negotiation, chat) and end-of-scene summaries.

## Locked decisions (Aaron, July 7 2026)

1. **Menu-first combat.** V1 battle input is pick-from-menu (ability /
   attack / defend / talk); zero LLM interpretation calls in the loop.
   Freeform text returns as a fast-follow — one small classify-to-action
   call whose output code resolves.
2. **Tier words → code maps.** Every generation-time number (ability
   power, costs, stat nudges) comes from LLM-picked word ladders that
   constants map to numbers — the existing `normalize_choice` pattern.
   Rebalancing = editing constants, never regenerating content.
3. **Template battle log + end summary.** Turns resolve instantly with
   code-built log lines; ONE short LLM summary when the battle ends
   keeps the story alive. Per-turn LLM flavor may return later as an
   opt-in settings toggle.
4. **Births are spark + voice (2 calls).** Call 1: identity, element,
   role, size, temperament, look. Call 2: traits, speech style, a want,
   battle line — so negotiation and campfire chat keep a real voice.
   Everything else accrues in play; migration is New Game.

## Survey — what the LLM is asked to do today (July 2026)

**The surface:** 64 prompt templates across 12 domains
(`backend/ai/llm/prompts/*.json`), 55 generation call sites, all funneled
through `ai/gateway.py`. Default local floor: 7B GGUF (kunoichi-7b
recommended in README) at `LLM_CONTEXT_SIZE` 4096.

**The battle bill** (the pivot's smoking gun) — one battle vs 2 enemies:

| Phase | LLM calls | Templates involved |
|---|---|---|
| Enemy generation | 12 (+2 card arts) | 5 monster stages + initial abilities, ×2 enemies |
| Battle start | 2 | `battle_arrival`, `battle_intro` |
| Each round | ~9 | ~3× `next_turn`, `turn_vanity`, 3× `action_resolution`, 2× `enemy_turn` |
| Battle end | 3–4 | `battle_summary`, `battle_victory`/`_defeat`, `victory_cocatok`, `goal_check` |
| **4-round battle total** | **~50 calls** | most 400–600 max_tokens, most requiring valid JSON |

Every round-loop call is a *judgment* task: the referee calibrates
impact/cost words from free-prose ability descriptions
(`action_resolution`), and `next_turn` asks the LLM to execute a
fairness algorithm that `director.py` already encodes as rules — pure
code work being paid for in tokens.

**Monster generation:** 6 calls per monster (`monster/generator.py`
stages A1/A2/B/C/D + initial abilities), ~2,200 max_tokens of structured
JSON; `monster_social_self` alone demands 13 exact fields. Every explore/
dialogue/battle/reunion encounter pays this in full for each monster.

**Abilities** (`ability_generation.json`, `models/ability.py`): name +
free-prose description + type. **No numbers.** The description exists to
be *interpreted by the referee at runtime* — which is why long
descriptions actively hurt: they were recently bumped to 200 max_tokens
(`d576cf3`) because they *look* better, but every extra clause is more
text a 7B referee must weigh mid-battle.

**What's already right** (the pivot builds on these, not against them):

- **Stats are already code-owned numbers.** `cmdts_data.derive_stats()`
  maps role × rarity × size (all LLM-picked words / code-rolled) to
  health/attack/defense/speed with jitter — and battles never read them.
  The math engine's inputs already exist on every monster row.
- **Enum-pick + normalization infrastructure** (`normalize_choice` /
  `normalize_multi`) — the exact pattern numeric tiers need.
- **Per-template `max_tokens`** in the prompt JSONs — the budget lever
  exists; it just isn't governed by a policy.
- **The provider seam** (local / DeepSeek, stamped per request) — makes
  optional per-task API boosting feasible later without new plumbing.
- **Word ladders survive as *presentation*.** Condition/reserve words can
  become derived views of numbers (fresh = top HP band, spent = empty
  pool) so prompts and UI keep the numberless fiction while math runs
  underneath.

**Domain-by-domain verdict:**

| Domain (templates) | Runtime role today | Pivot verdict |
|---|---|---|
| battle (12) | judgment loop, ~9 calls/round | **mathify the loop**; keep `battle_talk` + one end summary |
| monster gen (5) | 6-call birth, huge schemas | **2-call birth**; depth becomes progressive |
| abilities (2) | prose the referee interprets | **numeric schema**, one-line flavor |
| dungeon (12) | authoring + `goal_check` judgment | keep, shorter; goal_check is already a 1-word task |
| exploration (6) | narration + item/ability adjudication (600–800 tok) | shrink hard; adjudication simplifies later |
| encounter (3) | riddles, dialogue — chat-shaped | keep, trim |
| memory (6) | reflections, returning transforms | keep, tier-based, shorter |
| inventory (5) | item/CoCaTok authoring | keep; effect keywords → enum later |
| evolution (5) | big authoring ceremony | keep concept; shrinks with new birth schema |
| chat (2) | replies + memory extraction | keep replies; simplify extraction |
| summary (2) | rolling condense + chronicle | keep — summaries are load-bearing context tools |
| player (4) | one-time creation | keep as-is |

## The proposed shape (core forks locked; details set per initiative)

### Ability schema v2 — numbers at birth

Everything picked from code-defined enums except name and flavor:

```
name        ≤ 30 chars
flavor      ONE sentence, ≤ 120 chars — display only, never parsed
type        attack|defense|support|special|movement|utility  (existing)
element     from existing ELEMENTS list, or none
power       tier word (e.g. feeble→legendary) → code multiplier
cost_pool   stamina|mana  (today's ABILITY_POOL_BY_TYPE stays the default)
cost        tier word → numeric pool cost
target      self|ally|enemy|all_enemies|all_allies
effect      ONE keyword from a small code-owned list (damage, guard,
            heal, haste, slow, drain, rally, …) — code implements each
```

Numbers live in `battle/constants.py` next to the ladders they replace.
Balance changes = editing constants, never regenerating content.

### Battle engine v1 — code resolves, LLM socializes

- **Turn order:** code — speed stat + not-yet-acted-first + waited-longest
  (port the `next_turn` prompt's own rules; delete the call).
- **Resolution:** damage/heal formula from attack/defense × power tier ×
  element × small variance; numeric HP (`current_health` finally used)
  and numeric stamina/mana pools with tiered costs.
- **Enemy & wary-ally actions:** code policy driven by a `temperament`
  word the LLM picks at birth (aggressive/cunning/protective/craven, …) +
  battle state (low HP + craven → flee). Optional tiny LLM pick later.
- **Narration:** template log lines every turn (instant); ONE short LLM
  summary at battle end. Per-turn LLM flavor becomes a settings toggle
  for beefier setups, not the default.
- **Talk stays LLM.** Battlefield negotiation (`battle_talk`) is the
  game's soul and is chat-shaped — the task class local models handle
  best. It remains the one LLM moment inside battle.
- **Word ladders become displays** of the underlying numbers, so
  the UI and any prose keep speaking words.

### Monster birth diet — basics only

- **Call 1 "spark":** name, race/species label, element(s), party_role,
  size, temperament, visual one-liner + colors → enough for stats
  (existing `derive_stats`), card art, and the battle engine.
- **Call 2 "voice":** 2-3 traits, speech style, one want, battle line →
  enough for talk/negotiation/chat to stay in character.
- Everything else the 5-stage generator produces today (taxonomy chain,
  ecology, inner life, secret, backstory) is **not generated at birth** —
  it accrues in play (chat, camp, evolution) or stays API-repo-only.
- Migration: none — New Game wipe (shipped in `feature/new-game-experience`)
  is the reset path.

### Text diet — budgets as policy

Per-template `max_tokens` gets governed: narration defaults to 1–2
sentences (~80–150 tokens); nothing above ~300 except designated
storytelling moments (chronicle, evolution narration). Worst offenders
first: `camp_scene` 800, `path_choices` 800, `monster_dialogue_turn` 700,
`expedition_notices` 700. An **eval harness** (below) measures instead of
guessing.

### Eval harness — measure, don't vibe

A dev-tools harness that runs each live template against the REAL local
model N times and reports: valid-JSON rate, mean output tokens, latency.
This turns "too difficult for the local model" from a feeling into a
per-template scoreboard, decides what else must shrink, and later gates
"is this model good enough" per capability preset.

## Open questions

The four direction forks (combat input, numbers source, narration, birth
scope) were answered day one — see Locked decisions. Still open (answers
land here as they're decided):

1. **Reference floor** — what model/hardware is THE design target?
   (README says kunoichi-7b @ 4096 context. Design decisions differ for a
   13B/24B floor.)
2. **Numbers visible to the player?** Word-ladder veneer over numeric HP,
   raw numbers in the UI, or both (toggle)?
3. **Stamina/mana** — numeric pools under word displays (recommended), or
   keep pure 5-word ladders?
4. **goal_check / run goals** — keep (it's a cheap 1-word judgment), or
   move goal progress to code-visible events only?
5. **Chronicle & memory extraction** — keep both but shorter, or park
   either for v1 of the pivot?
6. **Item/ability use in dungeon** (600-token adjudications) — shrink
   now and enum-ify effects later, or enum-ify in the same pass?
7. **API repo logistics — ANSWERED 2026-07-07:** the ORIGINAL repo
   (`LlmMonsterHunter`) is the API-first one and runs the
   cloud-generation initiative there; the pivot lives in this fork
   (`LlmMonsterHunter-Local`, forked at PR #167). See Deviations.
8. **Per-task provider routing** — v1 keeps the global local/DeepSeek
   switch (recommended); later, allow "API for these N heavy tasks when
   configured"?
9. **CLAUDE.md rule 3 amendment** — adopt the reworded philosophy above
   once the battle initiative lands (architecture.md referee section
   rewrites in the same commit).

## Roadmap — child initiatives (each gets its own plan doc)

| # | Initiative | What it delivers | Depends on |
|---|---|---|---|
| 0 | Split logistics | DONE 2026-07-07 — this fork created (see Deviations); README/docs repositioned | — |
| 1 | Text diet + eval harness | IN PROGRESS ([text-diet.md](text-diet.md)) — budget policy over all 64 templates; eval scoreboard CLI | — |
| 2 | Numeric core | Ability schema v2, 2-call birth, temperament; New Game as migration | 1 (harness data) |
| 3 | Math battle engine | Code turn order/resolution/policies; talk + end summary as the only battle LLM calls; ladders become displays | 2 |
| 4 | Progressive depth | Persona fields earned in play; extraction/chronicle slimmed; evolution aligned to new schemas | 2, 3 |
| 5 | Local ergonomics | Optional per-task API routing; capability presets by model size | 1–4 |

Sequencing rationale: #1 is immediate relief with zero schema risk and
produces the data the rest is tuned by; #3 cannot land before abilities
have numbers (#2); #4–5 polish once the core loop is proven fast.

## What this supersedes / touches

- **CLAUDE.md rule 3** — amended when #3 lands (wording above, Q13).
- **docs/architecture.md** "referee philosophy" section — rewritten when
  #3 lands; word ladders re-documented as presentation layer.
- **docs/plans/monster-depth-cmdts.md — REMOVED 2026-07-08** (see
  Deviations). The deep-persona/CMDTS direction lives on in the API-first
  repo; here it's superseded by the birth diet + progressive depth
  (#2, #4). The CMDTS code still ships until #2 lands —
  `backend/game/monster/cmdts_data.py` is now its own source of truth for
  the taxonomy shapes the deleted doc used to hold.
- **docs/design/ (Feb-2025 historical design phase) — REMOVED 2026-07-08.**
  `gameplay_design.md` / `story_design.md` were the original maximalist
  vision, superseded by the shipped plan docs and this pivot.
- **Architecture-review backlog** (July 2026): the battle god-function
  and referee complexity findings are absorbed by #3. (An earlier draft
  said a `gateway.py` Exception-kwargs bug fix rides #1 — stale: that
  bug was already fixed by the Architecture Exemplar initiative.)
- The README gains a Direction section now (this conversation) — feature
  descriptions stay truthful to what's implemented until initiatives land.

## Deviations log

- **2026-07-07 — repo assignment flipped.** This doc was written in the
  original repo assuming IT would go local-first. Aaron instead forked
  `LlmMonsterHunter-Local` (at PR #167) as the pivot's home and kept the
  ORIGINAL repo API-first (it runs the cloud-generation initiative). The
  umbrella doc + README reposition moved here; wording above updated.
- **2026-07-07 — Diet-M0 merged the fork forward.** `feature/game-settings`
  (upstream PR #168: settings panel + DeepSeek provider seam) was merged
  into this fork's `main` so the pivot keeps the provider seam it builds
  on, plus the provider/model columns the eval harness reads.
- **2026-07-07 — stale claim removed.** The gateway Exception-kwargs bug
  predates the fork and was already fixed (Architecture Exemplar); it is
  not part of initiative 1.
- **2026-07-08 — old-direction docs scrubbed (identity only).** Deleted
  the maximalist-direction docs that no longer describe this fork's
  identity: `docs/plans/monster-depth-cmdts.md` and the Feb-2025
  `docs/design/` set (`gameplay_design.md`, `story_design.md`). Dangling
  references fixed in the same pass — README dev-status row unlinked,
  `CLAUDE.md` + `architecture.md` directory pointers dropped `docs/design/`,
  and three code comments (`cmdts_data.py`, `models/monster.py`,
  `transformers/monsters.js`) stopped citing the deleted plan doc. Scope
  was deliberately narrow: accurate descriptions of features that still
  ship today (word-ladder battles, free-text combat, CMDTS deep births)
  were left intact — they get rewritten when their initiative lands
  (#2/#3), per "truthful until initiatives land" above.
