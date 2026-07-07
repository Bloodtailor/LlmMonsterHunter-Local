# Text Diet + Eval Harness — Plan

**Status:** IN PROGRESS (July 2026) — Diet-M0 underway.
**Branch:** `feature/text-diet` — one milestone commit per milestone, prefix `Diet-M#`.
**Parent:** [local-first-pivot.md](local-first-pivot.md) — this is child initiative 1.

The pivot survey found 64 prompt templates whose `max_tokens` are
ungoverned: ability generation was bumped 150→200 (`d576cf3`, upstream)
chasing detail — the wrong direction for a 7B floor — and the worst
offenders sit at 700–800 tokens while a one-word `goal_check` answer is
budgeted 250. This initiative shrinks every generated text NOW (no
schema changes — those are initiatives 2–3) and builds the measurement
tool the rest of the pivot is tuned by. The enabling discovery:
`llm_logs` + `generation_logs` already store response tokens, caps,
parse results, durations, provider, and model per generation — so a
`report` command can baseline the whole game from existing play logs
with zero new generations.

## Locked decisions

1. **Measure before and after.** The eval harness lands first (M1) and
   the baseline is captured (M2) before any template changes (M3); the
   soak delta (M4) proves the diet did what it claims.
2. **Budgets are policy, not vibes.** Every template is mapped to a
   budget class in `backend/ai/llm/prompt_budgets.py`; an offline suite
   fails when a template exceeds its class ceiling or is unmapped — new
   prompts must declare a class (the file-size-ceiling precedent).
3. **The harness reads the REAL dev DB** (real play prompts are the
   corpus — `reset_db.py` precedent), is CLI-only
   (`python -m backend.tests.eval`), is never pytest-collected, and
   never runs in CI.
4. **Replay goes through the gateway** like every other generation
   (logged byte-exact, provider-stamped), at priority 10 so live
   gameplay always wins the queue, with `prompt_type='eval:<original>'`
   so game stats and eval stats never mix.
5. **Replayed prompts strip the nothink prefill** before resubmitting —
   stored `prompt_text` is byte-exact and already contains it; the
   gateway re-adds it per the current provider.
6. **Wording changes only.** Template names, variables, and parser
   `expected_fields`/`required_fields` are untouched in M3 — no step-name
   or parsing contract changes.
7. **Fork bring-up is part of this initiative** (Diet-M0): merge
   `feature/game-settings` (upstream PR #168) into fork `main`, fork-own
   databases (`monster_hunter_local` / `_test`), dev DB cloned in as the
   eval corpus.

## Budget classes (ceilings enforced by the suite)

| Class | Ceiling | Meant for |
|---|---|---|
| `word_answer` | 80 | one-word/enum JSON answers (`goal_check`, `next_turn`) |
| `one_liner` | 120 | single-sentence flavor (`turn_vanity`, `camp_spotlight`) |
| `short_narration` | 250 | 1–3 sentence scene text (arrivals, victories, `camp_scene`) |
| `structured` | 450 | multi-field JSON authoring (monster stages, items, notices) |
| `storytelling` | 550 | the deliberate allowlist: `run_chronicle`, `evolution_prose`, `evolution_narration`, `battle_summary`, `battle_talk`, `monster_dialogue_turn`, `path_choices` |

Representative diet targets (final numbers set from the M2 baseline):
`generate_ability` 200→120 with "description: ONE sentence" wording
(deliberately reverses `d576cf3` — Aaron's call); `goal_check` 250→60;
`camp_scene` 800→250; `path_choices` 800→500 (the 6-path batch stays —
`PATH_OVERGENERATE_COUNT` exists for small-model repetition);
`expedition_notices` 700→450; `monster_dialogue_turn` 700→550;
`battle_talk` 600→550; battle narrations 400–500→220–250.

## Milestones

- **Diet-M0 — Fork bring-up.** #168 merged (`afb9a83`); `.env` with
  `monster_hunter_local` DBs; dev DB cloned (641 generation logs);
  venv (py3.10) + base/dev requirements + prebuilt cu124
  llama-cpp-python wheel (the setup flow's method); `npm install`;
  suites green; this plan doc + the parked pivot docs committed
  ("Plan:" commit).
- **Diet-M1 — Eval harness.** `backend/tests/eval/` package:
  `report.py` (per-template scoreboard from `generation_logs ⋈
  llm_logs`: runs, failed/retry/parse-fail/truncation rates, avg+p95
  response tokens vs cap, duration, tokens/sec; `--since/--category/
  --name/--provider/--json`), `replay.py` (re-run latest K logged
  prompts per template through the gateway, stored or current params),
  `__main__.py` CLI. Usage note: local replay loads the GGUF in-process
  — run with the game backend stopped.
- **Diet-M2 — Budget policy + baseline.** `prompt_budgets.py`
  (BUDGET_CLASSES + TEMPLATE_CLASS for all 64); baseline table from the
  cloned corpus pasted below; ceilings adjusted only with a logged
  deviation.
- **Diet-M3 — The diet pass.** All 12 `prompts/*.json`: class-compliant
  `max_tokens` + brevity wording; `test_prompt_budgets.py` registered in
  `SUITES` (green at this commit).
- **Diet-M4 — Soak + docs.** Aaron plays a run (battle, camp, chat) on
  local; `report --since` delta vs baseline (shorter outputs, parse
  rates no worse); tuning.md "Generation budgets" section; CLAUDE.md
  eval command line; both plan docs closed out.

## Baseline (filled in at M2)

*(pending)*

## Verification checklist

- [ ] `./venv/Scripts/python.exe -m pytest` green (incl. budget suite)
- [ ] `ruff check backend setup tools` clean; file-size ceiling respected
- [ ] `python -m backend.tests.eval report` returns the scoreboard from cloned logs
- [ ] `python -m backend.tests.eval replay --name generate_ability --runs 2` (backend stopped) — fresh `eval:` rows visible in the dev AI log
- [ ] Soak battle: dev AI log shows new caps on every row; abilities generate one-sentence descriptions

## Deviations log

- *(none yet)*
