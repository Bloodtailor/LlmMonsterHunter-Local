# Eval harness CLI.
#
#   python -m backend.tests.eval report [--since 2026-07-01] [--category battle_generation]
#                                       [--name generate_ability] [--provider local]
#                                       [--eval-only] [--json out.json]
#   python -m backend.tests.eval replay --name generate_ability [--per-template 3]
#                                       [--runs 1] [--params logged|current] [--dry-run]
#
# report reads the dev database only. replay GENERATES: it loads the
# local model in-process (run with the game backend stopped) or speaks
# to the cloud provider the settings panel currently selects.

import argparse
import sys
from datetime import datetime

from .bootstrap import build_dev_app, start_ai_queue
from .replay import run_replay
from .report import run_report


def _parse_arguments(argv):
    parser = argparse.ArgumentParser(
        prog='python -m backend.tests.eval',
        description="Per-template LLM scoreboard from the game's own logs",
    )
    commands = parser.add_subparsers(dest='command', required=True)

    report = commands.add_parser('report', help='aggregate existing log rows (no generations)')
    report.add_argument('--since', type=datetime.fromisoformat, help='ISO date/datetime floor')
    report.add_argument('--name', help='one template name')
    report.add_argument('--category', help='one prompt file stem, e.g. battle_generation')
    report.add_argument('--provider', help="'local' or 'deepseek'")
    report.add_argument(
        '--eval-only', action='store_true', help='show replay rows instead of game rows'
    )
    report.add_argument('--json', help='also write the stats to this JSON file')

    replay = commands.add_parser('replay', help='re-run logged prompts for fresh measurements')
    replay.add_argument('--name', help='template name(s), comma-separated')
    replay.add_argument('--category', help='replay every template in one prompt file')
    replay.add_argument(
        '--per-template', type=int, default=3, help='latest N logged prompts per template'
    )
    replay.add_argument('--runs', type=int, default=1, help='repeat each prompt N times')
    replay.add_argument(
        '--params',
        choices=('logged', 'current'),
        default='logged',
        help="'logged' = the row's exact parameters; 'current' = the template's config today",
    )
    replay.add_argument('--dry-run', action='store_true', help='list what would run, send nothing')

    return parser.parse_args(argv)


def main(argv=None) -> int:
    arguments = _parse_arguments(argv if argv is not None else sys.argv[1:])

    app = build_dev_app()
    if arguments.command == 'replay':
        start_ai_queue(app)

    with app.app_context():
        if arguments.command == 'report':
            return run_report(arguments)
        return run_replay(arguments)


if __name__ == '__main__':
    sys.exit(main())
