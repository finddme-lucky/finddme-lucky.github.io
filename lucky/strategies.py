"""전략 점수 (spec §5.3).

점수가 높다고 당첨 확률이 높은 것은 아니다. 점수는 "이 전략이 어떤 번호를
선호하는가"일 뿐이고, 그 점수대로 뽑는 일은 lucky/sampling.py가 한다.
"""

from collections import Counter

LOTTO_HOT_WINDOW = 100
HALF_LIFE = 20
SIMPLE_STRATEGIES = ("hot", "cold", "recent", "random")
LOTTO_NUMBERS = range(1, 46)


def _decay(total, index, half_life=HALF_LIFE):
    """가장 최근 회차가 1.0, 반감기마다 절반."""
    return 0.5 ** ((total - 1 - index) / half_life)


def lotto_scores(draws, strategy, *, window=LOTTO_HOT_WINDOW):
    total = len(draws)
    if strategy == "random":
        return {number: 1.0 for number in LOTTO_NUMBERS}

    if strategy == "hot":
        counts = Counter(
            number for draw in draws[-window:] for number in draw["numbers"]
        )
        return {number: float(counts.get(number, 0)) for number in LOTTO_NUMBERS}

    if strategy == "cold":
        last_seen = {}
        for index, draw in enumerate(draws):
            for number in draw["numbers"]:
                last_seen[number] = index
        return {
            number: float(total - 1 - last_seen[number]) if number in last_seen else float(total)
            for number in LOTTO_NUMBERS
        }

    if strategy == "recent":
        scores = {number: 0.0 for number in LOTTO_NUMBERS}
        for index, draw in enumerate(draws):
            weight = _decay(total, index)
            for number in draw["numbers"]:
                scores[number] += weight
        return scores

    raise ValueError(f"lotto645: 알 수 없는 전략 {strategy!r}")
