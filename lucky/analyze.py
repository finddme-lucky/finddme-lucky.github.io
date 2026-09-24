"""통계와 공정성 검정을 묶어 data/stats/<game>.json에 저장한다 (spec §5.1, §5.2)."""

from datetime import datetime

from lucky import fairness, store
from lucky.stats import lotto_stats, pension_stats

DISCLAIMER = "과거 분포이며 다음 회차 확률과 무관하다."
ANALYZERS = {
    "lotto645": (lotto_stats, fairness.run_lotto),
    "pension720": (pension_stats, fairness.run_pension),
}


def build_report(game, draws, now):
    compute_stats, run_fairness = ANALYZERS[game]
    return {
        "schema": 1,
        "game": game,
        "generatedAt": now.isoformat(timespec="seconds"),
        "latestRound": draws[-1]["round"] if draws else None,
        "latestDate": draws[-1]["date"] if draws else None,
        "disclaimer": DISCLAIMER,
        "stats": compute_stats(draws),
        "fairness": run_fairness(draws),
    }


def load_report(game, data_dir, now=None):
    """저장된 회차로 보고서를 만든다 (저장은 하지 않는다)."""
    draws = store.load_draws(data_dir, game)
    if not draws:
        raise ValueError(f"{game}: 수집된 회차가 없다 — 먼저 collect를 실행할 것")
    return draws, build_report(game, draws, now or datetime.now(store.KST))


def analyze(game, data_dir, *, now=None, log=print):
    draws, report = load_report(game, data_dir, now)
    if not store.save_document_if_changed(data_dir, f"stats/{game}.json", report):
        log(f"{game}: {len(draws)}회 분석 — 변경 없음")
        return report
    flagged = [
        result["id"]
        for period in ("all", "recent")
        for result in report["fairness"][period]
        if result["biased"]
    ]
    suffix = f" (편향 의심: {', '.join(sorted(set(flagged)))})" if flagged else ""
    log(f"{game}: {len(draws)}회 분석 → data/stats/{game}.json{suffix}")
    return report


def format_fairness(report):
    lines = []
    for period in ("all", "recent"):
        header = "전체" if period == "all" else f"최근 {report['fairness']['recentWindow']}회"
        lines.append(f"[{header}]")
        for result in report["fairness"][period]:
            if result["p"] is None:
                lines.append(f"  {result['label']}: 생략 ({result['note']})")
                continue
            verdict = "편향 증거 있음" if result["biased"] else "편향 증거 없음"
            lines.append(
                f"  {result['label']}: p={result['p']:.4f}"
                f" (Holm 보정 {result['pAdj']:.4f}) → {verdict}"
            )
    return "\n".join(lines)
