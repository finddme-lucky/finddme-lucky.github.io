"""추첨 공정성 검정 (spec §5.2, S1).

관측 분포를 이론 분포와 카이제곱 적합도로 맞대어 본다. 한 게임에 검정을
여러 개 돌리므로 Holm 보정으로 다중 검정을 교정한다. "편향 증거 없음"이
정상적인 결과이며, 그것을 확인하는 것이 이 검정의 목적이다.
"""

from scipy.stats import chi2

from lucky import reference
from lucky.stats import lotto_stats, pension_stats

ALPHA = 0.05
MIN_EXPECTED = 5.0
LOTTO_RECENT = 300
PENSION_RECENT = 200


def merge_small(rows, min_expected=MIN_EXPECTED):
    """기대빈도가 작은 구간을 앞에서부터 합친다 (카이제곱 근사 조건)."""
    merged = []
    label, observed, expected = None, 0, 0.0
    for row_label, row_observed, row_expected in rows:
        label = row_label if label is None else f"{label}~{row_label}"
        observed += row_observed
        expected += row_expected
        if expected >= min_expected:
            merged.append((label, observed, expected))
            label, observed, expected = None, 0, 0.0
    if label is not None:
        if merged:
            last_label, last_observed, last_expected = merged[-1]
            merged[-1] = (
                f"{last_label}~{label}",
                last_observed + observed,
                last_expected + expected,
            )
        else:
            merged.append((label, observed, expected))
    return merged


def goodness_of_fit(test_id, label, observed, weights):
    """카이제곱 적합도. weights는 상대 가중치이며 관측 총합에 맞춰 정규화한다."""
    categories = sorted(set(observed) | set(weights))
    total = sum(observed.get(category, 0) for category in categories)
    weight_total = sum(weights.get(category, 0) for category in categories)
    base = {"id": test_id, "label": label, "n": total}
    if total == 0 or weight_total == 0:
        return {**base, "categories": 0, "stat": None, "dof": 0, "p": None,
                "note": "자료가 없어 검정 생략", "buckets": []}

    rows = [
        (str(category), observed.get(category, 0), weights.get(category, 0) * total / weight_total)
        for category in categories
    ]
    merged = merge_small(rows)
    labels = [label for label, _count, _expected in merged]
    if len(merged) < 2:
        return {**base, "categories": len(merged), "stat": None, "dof": 0, "p": None,
                "note": f"기대빈도 {MIN_EXPECTED} 이상 구간이 2개 미만이라 검정 생략", "buckets": labels}

    statistic = sum((count - expected) ** 2 / expected for _, count, expected in merged)
    dof = len(merged) - 1
    return {**base, "categories": len(merged), "stat": statistic, "dof": dof,
            "p": float(chi2.sf(statistic, dof)), "buckets": labels}


def holm(pvalues):
    """Holm 보정. 입력 순서를 유지한 보정 p값을 돌려준다."""
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


def _finalize(results, alpha=ALPHA):
    scored = [result for result in results if result["p"] is not None]
    for result, adjusted in zip(scored, holm([result["p"] for result in scored])):
        result["pAdj"] = adjusted
        result["biased"] = adjusted < alpha
    for result in results:
        result.setdefault("pAdj", None)
        result.setdefault("biased", False)
    return results


def _lotto_tests(draws):
    stats = lotto_stats(draws)
    uniform = {number: 1 for number in range(1, 46)}
    return [
        goodness_of_fit("numbers", "번호별 출현 (본번호)", stats["counts"], uniform),
        goodness_of_fit("numbersWithBonus", "번호별 출현 (보너스 포함)", stats["countsWithBonus"], uniform),
        goodness_of_fit("oddEven", "홀수 개수 분포", stats["oddEven"], reference.hypergeometric(45, 23, 6)),
        goodness_of_fit("lowHigh", "저번호(1~22) 개수 분포", stats["lowHigh"], reference.hypergeometric(45, 22, 6)),
        goodness_of_fit("sum", "번호 합 분포", stats["sums"], reference.sum_distribution()),
        goodness_of_fit("adjacent", "연속번호 쌍 개수 분포", stats["adjacentPairs"], reference.adjacent_pair_distribution()),
        goodness_of_fit("overlap", "직전 회차와 겹치는 번호 개수", stats["overlapWithPrevious"], reference.hypergeometric(45, 6, 6)),
    ]


def _pension_tests(draws):
    stats = pension_stats(draws)
    uniform_digits = {digit: 1 for digit in range(10)}
    results = [
        goodness_of_fit("groups", "1등 조 분포", stats["groups"], {group: 1 for group in range(1, 6)})
    ]
    for position in range(6):
        results.append(
            goodness_of_fit(
                f"first{position + 1}",
                f"1등 {position + 1}번째 자리 숫자 분포",
                stats["firstDigits"][position],
                uniform_digits,
            )
        )
    for position in range(6):
        results.append(
            goodness_of_fit(
                f"bonus{position + 1}",
                f"보너스 {position + 1}번째 자리 숫자 분포",
                stats["bonusDigits"][position],
                uniform_digits,
            )
        )
    return results


def run_lotto(draws, *, recent=LOTTO_RECENT):
    window = draws[-recent:] if recent else []
    return {
        "alpha": ALPHA,
        "recentWindow": len(window),
        "all": _finalize(_lotto_tests(draws)),
        "recent": _finalize(_lotto_tests(window)),
    }


def run_pension(draws, *, recent=PENSION_RECENT):
    window = draws[-recent:] if recent else []
    return {
        "alpha": ALPHA,
        "recentWindow": len(window),
        "all": _finalize(_pension_tests(draws)),
        "recent": _finalize(_pension_tests(window)),
    }
