import random
from collections import Counter

import pytest

from lucky import sampling


def test_seed_is_stable_per_round_and_attempt():
    first = sampling.seed_for("lotto645", "hot", 1243)
    assert first == sampling.seed_for("lotto645", "hot", 1243)
    assert first != sampling.seed_for("lotto645", "hot", 1244)
    assert first != sampling.seed_for("lotto645", "cold", 1243)
    assert first != sampling.seed_for("pension720", "hot", 1243)
    assert first != sampling.seed_for("lotto645", "hot", 1243, attempt=1)
    assert 0 <= first < 2**64


def test_probabilities_are_flat_when_scores_are_equal():
    probabilities = sampling.probabilities({1: 5.0, 2: 5.0, 3: 5.0})
    assert probabilities == pytest.approx({1: 1 / 3, 2: 1 / 3, 3: 1 / 3})


def test_probabilities_follow_scores_but_never_reach_zero():
    probabilities = sampling.probabilities({1: 0.0, 2: 1.0, 3: 2.0})
    assert probabilities[3] > probabilities[2] > probabilities[1] > 0
    assert sum(probabilities.values()) == pytest.approx(1.0)
    # 최저 점수는 바닥값만, 최고 점수는 1 + 바닥값 — 비율은 11배
    assert probabilities[3] / probabilities[1] == pytest.approx((1 + sampling.FLOOR) / sampling.FLOOR)


def test_a_higher_floor_moves_toward_uniform():
    scores = {1: 0.0, 2: 10.0}
    sharp = sampling.probabilities(scores, floor=0.01)
    soft = sampling.probabilities(scores, floor=10.0)
    assert sharp[2] > soft[2]
    assert soft[2] / soft[1] < 1.2


def test_weighted_sample_picks_distinct_keys_and_is_deterministic():
    scores = {number: float(number) for number in range(1, 46)}
    first = sampling.weighted_sample(random.Random(42), scores, 30)
    second = sampling.weighted_sample(random.Random(42), scores, 30)

    assert first == second
    assert len(first) == len(set(first)) == 30
    assert set(first) <= set(scores)


def test_weighted_sample_favours_high_scores():
    scores = {1: 0.0, 2: 0.0, 3: 100.0}
    picked_first = Counter(
        sampling.weighted_sample(random.Random(seed), scores, 1)[0] for seed in range(300)
    )
    assert picked_first[3] > picked_first[1] + picked_first[2]


def test_weighted_sample_can_exhaust_the_pool():
    picked = sampling.weighted_sample(random.Random(7), {1: 1.0, 2: 2.0, 3: 3.0}, 3)
    assert sorted(picked) == [1, 2, 3]


def test_weighted_sample_refuses_to_draw_more_than_the_pool():
    with pytest.raises(ValueError, match="후보"):
        sampling.weighted_sample(random.Random(1), {1: 1.0, 2: 2.0, 3: 3.0}, 5)
