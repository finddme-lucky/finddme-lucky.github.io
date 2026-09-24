"""python -m lucky <collect|analyze|fairness> — 수집·분석 CLI."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from lucky import store
from lucky.analyze import analyze, format_fairness, load_report
from lucky.collect import collect
from lucky.errors import NetworkError, SourceError, ValidationError
from lucky.http import Client
from lucky.store import KST


def main(argv=None, *, get=None, now=None):
    parser = argparse.ArgumentParser(prog="python -m lucky")
    commands = parser.add_subparsers(dest="command", required=True)

    collect_cmd = commands.add_parser("collect", help="동행복권에서 신규 회차를 수집해 data/에 저장")
    collect_cmd.add_argument("--game", choices=[*store.GAMES, "all"], default="all")
    collect_cmd.add_argument("--data-dir", type=Path, default=Path("data"))
    collect_cmd.add_argument(
        "--full", action="store_true", help="전 회차를 다시 받아 저장된 값이 바뀌지 않았는지 확인"
    )

    analyze_cmd = commands.add_parser("analyze", help="통계·공정성 검정을 계산해 data/stats/에 저장")
    analyze_cmd.add_argument("--game", choices=[*store.GAMES, "all"], default="all")
    analyze_cmd.add_argument("--data-dir", type=Path, default=Path("data"))

    fairness_cmd = commands.add_parser("fairness", help="추첨 공정성 검정 결과 출력 (저장하지 않음)")
    fairness_cmd.add_argument("--game", choices=[*store.GAMES, "all"], default="all")
    fairness_cmd.add_argument("--data-dir", type=Path, default=Path("data"))

    args = parser.parse_args(argv)
    games = store.GAMES if args.game == "all" else (args.game,)
    if args.command == "collect":
        return _collect(args, games, get, now)
    if args.command == "analyze":
        return _analyze(args, games, now)
    return _fairness(args, games, now)


def _collect(args, games, get, now):
    get = get or Client().get
    failed = []
    for game in games:
        try:
            added = collect(game, args.data_dir, get, full=args.full)
            print(f"{game}: 신규 {added}회")
        except (SourceError, NetworkError, ValidationError, ValueError, OSError) as e:
            failed.append(game)
            print(f"{game}: 실패 — {e}", file=sys.stderr)

    try:
        if store.save_meta(args.data_dir, now or datetime.now(KST)):
            print("meta.json 갱신")
    except (ValueError, OSError) as e:
        failed.append("meta")
        print(f"meta.json 갱신 실패 — {e}", file=sys.stderr)
    return 1 if failed else 0


def _analyze(args, games, now):
    failed = []
    for game in games:
        try:
            analyze(game, args.data_dir, now=now)
        except (ValueError, OSError) as e:
            failed.append(game)
            print(f"{game}: 실패 — {e}", file=sys.stderr)
    return 1 if failed else 0


def _fairness(args, games, now):
    failed = []
    for game in games:
        try:
            draws, report = load_report(game, args.data_dir, now)
            print(f"== {game} ({len(draws)}회) ==")
            print(format_fairness(report))
        except (ValueError, OSError) as e:
            failed.append(game)
            print(f"{game}: 실패 — {e}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
