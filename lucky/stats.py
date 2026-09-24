"""관측 통계 집계 (spec §5.1). 과거 분포를 세기만 하고 확률로 해석하지 않는다."""

from collections import Counter

LOTTO_RECENT = 100
DECADES = ((1, 10), (11, 20), (21, 30), (31, 40), (41, 45))


def adjacent_pairs(numbers):
    """오름차순 번호에서 연속한 쌍의 개수 (예: [5,6,7] -> 2)."""
    return sum(1 for low, high in zip(numbers, numbers[1:]) if high - low == 1)


def _fill(counter, keys):
    return {key: counter.get(key, 0) for key in keys}


def _decade_label(number):
    for low, high in DECADES:
        if low <= number <= high:
            return f"{low}-{high}"
    raise ValueError(f"번호 범위 밖: {number}")


def lotto_stats(draws, *, recent=LOTTO_RECENT):
    numbers = range(1, 46)
    main = Counter(number for draw in draws for number in draw["numbers"])
    with_bonus = Counter(main)
    with_bonus.update(draw["bonus"] for draw in draws)
    recent_draws = draws[-recent:] if recent else []
    recent_counts = Counter(number for draw in recent_draws for number in draw["numbers"])

    last_seen = {}
    for draw in draws:
        for number in draw["numbers"]:
            last_seen[number] = draw["round"]
    latest = draws[-1]["round"] if draws else 0
    gaps = {
        number: (latest - last_seen[number] if number in last_seen else None)
        for number in numbers
    }

    decades = Counter(
        _decade_label(number) for draw in draws for number in draw["numbers"]
    )

    return {
        "draws": len(draws),
        "recentCountsWindow": len(recent_draws),
        "counts": _fill(main, numbers),
        "countsWithBonus": _fill(with_bonus, numbers),
        "recentCounts": _fill(recent_counts, numbers),
        "gaps": gaps,
        "oddEven": _fill(
            Counter(sum(1 for n in draw["numbers"] if n % 2) for draw in draws), range(7)
        ),
        "lowHigh": _fill(
            Counter(sum(1 for n in draw["numbers"] if n <= 22) for draw in draws), range(7)
        ),
        "sums": dict(sorted(Counter(sum(draw["numbers"]) for draw in draws).items())),
        "decades": {f"{low}-{high}": decades.get(f"{low}-{high}", 0) for low, high in DECADES},
        "adjacentPairs": _fill(
            Counter(adjacent_pairs(draw["numbers"]) for draw in draws), range(6)
        ),
        "overlapWithPrevious": _fill(
            Counter(
                len(set(previous["numbers"]) & set(current["numbers"]))
                for previous, current in zip(draws, draws[1:])
            ),
            range(7),
        ),
        "series": [
            {
                "round": draw["round"],
                "date": draw["date"],
                "sales": draw["sales"],
                "firstWinners": draw["ranks"][0]["winners"],
                "firstPrize": draw["ranks"][0]["prize"],
            }
            for draw in draws
        ],
    }


PENSION_RECENT = 50
DIGITS = range(10)
GROUPS = range(1, 6)
POSITIONS = 6


def _digit_counts(draws, key):
    per_position = [Counter() for _ in range(POSITIONS)]
    for draw in draws:
        for position, digit in enumerate(draw[key]):
            per_position[position][int(digit)] += 1
    return [_fill(counter, DIGITS) for counter in per_position]


def pension_stats(draws, *, recent=PENSION_RECENT):
    recent_draws = draws[-recent:] if recent else []
    return {
        "draws": len(draws),
        "recentCountsWindow": len(recent_draws),
        "groups": _fill(Counter(draw["group"] for draw in draws), GROUPS),
        "recentGroups": _fill(Counter(draw["group"] for draw in recent_draws), GROUPS),
        "firstDigits": _digit_counts(draws, "first"),
        "bonusDigits": _digit_counts(draws, "bonus"),
        "series": [
            {
                "round": draw["round"],
                "date": draw["date"],
                "rankTotals": {str(rank["rank"]): rank["total"] for rank in draw["ranks"]},
            }
            for draw in draws
        ],
    }
