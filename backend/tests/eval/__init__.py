# LLM eval harness - measures how the CURRENT model handles the game's
# prompt templates, using REAL play logs as the corpus.
#
#   python -m backend.tests.eval report   - scoreboard from existing logs
#   python -m backend.tests.eval replay   - re-run logged prompts for fresh data
#
# This is an ONLINE dev tool (real dev database, optionally the real
# model). It is deliberately NOT a pytest suite and never runs in CI -
# pytest collection is pinned to test_offline_suites.py.
