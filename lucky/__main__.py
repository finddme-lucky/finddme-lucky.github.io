"""python -m lucky collect [--game lotto645|pension720|all] [--data-dir data] [--full]"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lucky import store
from lucky.collect import collect
from lucky.errors import NetworkError, SourceError, ValidationError
from lucky.http import Client

KST = timezone(timedelta(hours=9))


def main(argv=None, *, get=None, now=None):
    parser = argparse.ArgumentParser(prog="python -m lucky")
    commands = parser.add_subparsers(dest="command", required=True)
    collect_cmd = commands.add_parser("collect", help="동행복권에서 신규 회차를 수집해 data/에 저장")
    collect_cmd.add_argument("--game", choices=[*store.GAMES, "all"], default="all")
    collect_cmd.add_argument("--data-dir", type=Path, default=Path("data"))
    collect_cmd.add_argument(
        "--full", action="store_true", help="전 회차를 다시 받아 저장된 값이 바뀌지 않았는지 확인"
    )
    args = parser.parse_args(argv)

    get = get or Client().get
    games = store.GAMES if args.game == "all" else (args.game,)
    failed = []
    for game in games:
        try:
            added = collect(game, args.data_dir, get, full=args.full)
            print(f"{game}: 신규 {added}회")
        except (SourceError, NetworkError, ValidationError) as e:
            failed.append(game)
            print(f"{game}: 실패 — {e}", file=sys.stderr)

    if store.save_meta(args.data_dir, now or datetime.now(KST)):
        print("meta.json 갱신")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
