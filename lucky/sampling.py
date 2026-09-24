"""점수대로 뽑기 + 회차 고정 시드 (spec §5.3).

보안용 난수가 아니다. 같은 회차에는 언제 봐도 같은 번호가 나와야 하므로
의도적으로 결정적이다. 점수가 높을수록 자주 뽑히지만 매번 같지는 않다.
"""

import hashlib

FLOOR = 0.1


def seed_for(game, strategy, round_no, attempt=0):
    key = f"{game}:{strategy}:{round_no}"
    if attempt:
        key += f":{attempt}"
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def probabilities(scores, floor=FLOOR):
    """점수를 0~1로 정규화하고 바닥값을 더해 확률로 만든다."""
    values = scores.values()
    low, high = min(values), max(values)
    span = high - low
    weights = {
        key: floor if span == 0 else (value - low) / span + floor
        for key, value in scores.items()
    }
    total = sum(weights.values())
    return {key: weight / total for key, weight in weights.items()}


def weighted_sample(rng, scores, count, *, floor=FLOOR):
    """가중 비복원 추출. 뽑힌 순서대로 돌려준다."""
    if count > len(scores):
        raise ValueError(f"뽑을 개수 {count}가 후보 {len(scores)}개보다 많다")
    remaining = probabilities(scores, floor)
    picked = []
    for _ in range(count):
        threshold = rng.random() * sum(remaining.values())
        cumulative = 0.0
        for key, weight in remaining.items():
            cumulative += weight
            if cumulative >= threshold:
                picked.append(key)
                del remaining[key]
                break
        else:  # 부동소수 오차로 아무 구간도 못 넘긴 경우 — 짧은 세트를 내놓지 않는다
            key = next(iter(remaining))
            picked.append(key)
            del remaining[key]
    return picked
