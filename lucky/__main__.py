"""python -m lucky <collect|analyze|fairness|sets|backtest> — 수집·분석·번호 세트 CLI."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from lucky import predictions, store
from lucky import rules as rules_module
from lucky import backtest as backtest_module
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

    sets_cmd = commands.add_parser("sets", help="다음 회차 번호 세트를 만들어 data/predictions.json에 저장")
    sets_cmd.add_argument("--game", choices=[*store.GAMES, "all"], default="all")
    sets_cmd.add_argument("--data-dir", type=Path, default=Path("data"))
    sets_cmd.add_argument("--round", type=int, help="점검용: 이 회차 기준으로 계산하고 저장하지 않는다")
    sets_cmd.add_argument("--strategy", help="점검용: 한 전략만 계산하고 저장하지 않는다")

    backtest_cmd = commands.add_parser("backtest", help="전략별 과거 성적을 계산해 data/backtest.json에 저장")
    backtest_cmd.add_argument("--game", choices=[*store.GAMES, "all"], default="all")
    backtest_cmd.add_argument("--data-dir", type=Path, default=Path("data"))
    backtest_cmd.add_argument("--rounds", type=int, help="점검용: 평가 회차 수를 줄이고 저장하지 않는다")
    backtest_cmd.add_argument("--strategy", help="점검용: 한 전략만 계산하고 저장하지 않는다")

    args = parser.parse_args(argv)
    games = store.GAMES if args.game == "all" else (args.game,)
    if args.command == "collect":
        return _collect(args, games, get, now)
    if args.command == "analyze":
        return _analyze(args, games, now)
    if args.command == "sets":
        return _sets(args, games, now)
    if args.command == "backtest":
        return _backtest(args, games, now)
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

    stamp = now or datetime.now(KST)
    for name, writer in (("meta.json", store.save_meta), ("latest.json", store.save_latest)):
        try:
            if writer(args.data_dir, stamp):
                print(f"{name} 갱신")
        except (ValueError, OSError) as e:
            failed.append(name)
            print(f"{name} 갱신 실패 — {e}", file=sys.stderr)
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


def _sets(args, games, now):
    inspecting = args.round is not None or args.strategy is not None
    try:
        document = predictions.build_predictions(
            args.data_dir,
            now=now or datetime.now(KST),
            rules=rules_module.load_rules(),
            games=games,
            strategy=args.strategy,
            round_no=args.round,
        )
    except (ValueError, OSError) as e:
        print(f"sets: 실패 — {e}", file=sys.stderr)
        return 1

    for game in games:
        section = document[game]
        print(f"== {game} {section['round']}회 ==")
        for entry in section["sets"]:
            if "games" in entry:
                for numbers in entry["games"]:
                    print(f"  {entry['strategy']:7} {numbers}")
            else:
                print(f"  {entry['strategy']:7} {entry['number']} (1~5조 전부)")

    if not inspecting:
        try:
            written = predictions.save_predictions(args.data_dir, document)
        except (ValueError, OSError) as e:
            print(f"sets: 저장 실패 — {e}", file=sys.stderr)
            return 1
        print("predictions.json 저장" if written else "predictions.json 변경 없음")
    return 0


def _backtest(args, games, now):
    inspecting = args.rounds is not None or args.strategy is not None
    try:
        document = backtest_module.build_document(
            args.data_dir,
            now=now or datetime.now(KST),
            rules=rules_module.load_rules(),
            games=games,
            strategies=(args.strategy,) if args.strategy else None,
            rounds=args.rounds,
        )
    except (ValueError, OSError) as e:
        print(f"backtest: 실패 — {e}", file=sys.stderr)
        return 1

    for game in games:
        report = document[game]
        theory = report["theory"]
        print(f"== {game} (평가 {report['evalRounds']}회) ==")
        for name, entry in report["strategies"].items():
            if game == "lotto645":
                verdict = "무작위와 구분됨" if entry["distinguishable"] else "무작위와 구분되지 않음"
                print(
                    f"  {name:7} 5등 이상 {entry['hitRate']:.4%}"
                    f" (이론 {theory['hitRate']:.4%}, 95% 구간 {entry['hitRateCI'][0]:.4%}~{entry['hitRateCI'][1]:.4%})"
                    f" → {verdict}"
                )
            else:
                verdict = "무작위와 구분됨" if entry["distinguishable"] else "무작위와 구분되지 않음"
                print(
                    f"  {name:7} 수익률 {entry['returnRate']:.1%}"
                    f" (이론 {theory['returnRate']:.1%}, 지출 {entry['spent']:,}원 → 수령 {entry['won']:,}원)"
                    f" → {verdict}"
                )
        if game == "lotto645" and "ml" in report["strategies"]:
            entry = report["strategies"]["ml"]
            print(
                f"  ml 학습 구간 분리도 {entry['inSampleSeparation']:+.5f}"
                f" vs 평가 구간 {entry['outOfSampleSeparation']:+.5f}"
            )

    if "popularity" in document:
        evidence = document["popularity"]
        print(
            f"== 인기 규칙 근거 (주변 {evidence['window']}회차 정규화) ==\n"
            f"  당첨자 많은 회차 {evidence['high']['rounds']}개 중 {evidence['high']['flaggedRate']:.1%}가 인기 패턴\n"
            f"  적은 회차 {evidence['low']['rounds']}개 중 {evidence['low']['flaggedRate']:.1%}"
        )
        for rule, rates in sorted(
            evidence["byRule"].items(), key=lambda item: -item[1]["difference"]
        )[:3]:
            print(f"  {rule:18} 차이 {rates['difference']:+.2%}")

    if not inspecting:
        try:
            written = backtest_module.save_document(args.data_dir, document)
        except (ValueError, OSError) as e:
            print(f"backtest: 저장 실패 — {e}", file=sys.stderr)
            return 1
        print("backtest.json 저장" if written else "backtest.json 변경 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
