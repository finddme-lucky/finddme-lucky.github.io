"""인기 패턴 규칙의 근거 보강 (spec §5.3).

질문: 사람들이 많이 고르는 조합이 실제로 당첨자 수를 늘리는가?
방법: 5등 당첨자 수를 판매 규모로 나눈 값을 주변 회차 중앙값으로 정규화하고, 그 값이
높은 회차의 당첨번호가 인기 패턴 규칙에 더 많이 걸리는지 본다.

주의: 판매액 필드(`sales`)는 회차 구간마다 의미가 달라 절대 기대값과 비교할 수 없다
(실측 5등 관측/기대 중앙값: 1~100회 0.51, 101~400회 1.07, 401회 이후 2.00). 그래서
정규화한 상대 비교만 한다.
"""

from math import comb
from statistics import median

from lucky.rules import unpopular_reasons

FIFTH_PRIZE_RATE = comb(6, 3) * comb(39, 3) / comb(45, 6)
WINDOW = 51
ERAS = ((1, 100), (101, 400), (401, None))
RULE_IDS = (
    "allLow",
    "consecutive",
    "sameLastDigit",
    "gridRow",
    "gridColumn",
    "gridDiagonal",
    "multiplesOfSeven",
    "arithmetic",
    "sameDecade",
)
CAVEAT = (
    "판매액 필드의 의미가 회차 구간마다 달라 절대 기대값과는 비교할 수 없다. "
    "주변 회차 중앙값으로 정규화한 상대 비교만 유효하다."
)


def winner_ratios(draws):
    """회차별 (5등 당첨자 수) ÷ (판매액 기준 기대 당첨자 수). 절대 배율은 의미 없다."""
    ratios = []
    for draw in draws:
        games = draw["sales"] / 1000
        winners = next((rank["winners"] for rank in draw["ranks"] if rank["rank"] == 5), 0)
        ratios.append(winners / (games * FIFTH_PRIZE_RATE) if games and winners else None)
    return ratios


def normalize(ratios, window=WINDOW):
    """주변 window 회차의 중앙값으로 나눈다 — 구간별 배율 차이를 없앤다."""
    half = window // 2
    normalized = []
    for index, value in enumerate(ratios):
        if value is None:
            normalized.append(None)
            continue
        nearby = [
            other for other in ratios[max(0, index - half) : index + half + 1] if other is not None
        ]
        normalized.append(value / median(nearby))
    return normalized


def _group(rows):
    flagged = sum(1 for row in rows if row[2])
    return {
        "rounds": len(rows),
        "flagged": flagged,
        "flaggedRate": flagged / len(rows) if rows else 0.0,
    }


def _rule_counts(rows, rule):
    flagged = sum(1 for row in rows if rule in row[3])
    return flagged, flagged / len(rows) if rows else 0.0


def _rule_entry(high, low, rule):
    high_flagged, high_rate = _rule_counts(high, rule)
    low_flagged, low_rate = _rule_counts(low, rule)
    return {
        "high": high_rate,
        "low": low_rate,
        "difference": high_rate - low_rate,
        "highFlagged": high_flagged,
        "lowFlagged": low_flagged,
    }


def evidence(draws, rules, *, window=WINDOW):
    """당첨자가 많았던 회차의 당첨번호가 인기 패턴에 더 많이 걸리는지 비교한다."""
    normalized = normalize(winner_ratios(draws), window)
    rows = []
    for draw, value in zip(draws, normalized):
        if value is None:
            continue
        reasons = [
            reason
            for reason in unpopular_reasons(draw["numbers"], rules)
            if reason != "pastWinner"  # 과거 당첨 조합은 자기 자신에 걸린다
        ]
        rows.append((draw["round"], value, bool(reasons), reasons))

    middle = median(row[1] for row in rows) if rows else 0.0
    high = [row for row in rows if row[1] > middle]
    low = [row for row in rows if row[1] <= middle]
    ordered = sorted(rows, key=lambda row: row[1])
    decile = max(1, len(rows) // 10)

    eras = []
    for start, end in ERAS:
        part = [row for row in rows if start <= row[0] and (end is None or row[0] <= end)]
        if not part:
            continue
        cut = median(row[1] for row in part)
        eras.append(
            {
                "from": start,
                "to": end,
                "rounds": len(part),
                "high": _group([row for row in part if row[1] > cut])["flaggedRate"],
                "low": _group([row for row in part if row[1] <= cut])["flaggedRate"],
            }
        )

    return {
        "window": window,
        "rounds": len(rows),
        "high": _group(high),
        "low": _group(low),
        "topDecile": _group(ordered[-decile:]),
        "bottomDecile": _group(ordered[:decile]),
        "byRule": {rule: _rule_entry(high, low, rule) for rule in RULE_IDS},
        "byEra": eras,
        "caveat": CAVEAT,
    }
