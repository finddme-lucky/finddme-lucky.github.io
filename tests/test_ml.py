import random
from datetime import date, timedelta

import pytest

from lucky import ml


def lotto_draws(count, *, always=None, seed=3):
    rng = random.Random(seed)
    start = date(2002, 12, 7)
    draws = []
    for index in range(1, count + 1):
        pool = [number for number in range(1, 46) if number != always]
        numbers = sorted(rng.sample(pool, 6 if always is None else 5) + ([always] if always else []))
        draws.append({
            "round": index,
            "date": (start + timedelta(days=7 * (index - 1))).isoformat(),
            "numbers": numbers,
            "bonus": next(n for n in range(1, 46) if n not in numbers),
        })
    return draws


def pension_draws(count, *, first_digit=None, seed=5):
    rng = random.Random(seed)
    start = date(2020, 5, 7)
    draws = []
    for index in range(1, count + 1):
        digits = [rng.randrange(10) for _ in range(6)]
        if first_digit is not None:
            digits[0] = first_digit
        draws.append({
            "round": index,
            "date": (start + timedelta(days=7 * (index - 1))).isoformat(),
            "group": rng.randrange(1, 6),
            "first": "".join(str(digit) for digit in digits),
            "bonus": "".join(str(rng.randrange(10)) for _ in range(6)),
        })
    return draws


def test_lotto_scores_cover_every_number_as_probabilities():
    scores = ml.lotto_scores(lotto_draws(200))
    assert set(scores) == set(range(1, 46))
    assert all(0.0 < value < 1.0 for value in scores.values())


def test_lotto_scores_are_deterministic():
    draws = lotto_draws(200)
    assert ml.lotto_scores(draws) == ml.lotto_scores(draws)


def test_lotto_model_picks_up_a_planted_signal():
    scores = ml.lotto_scores(lotto_draws(200, always=7))
    assert max(scores, key=scores.get) == 7
    assert scores[7] > 0.9


def test_lotto_needs_enough_history():
    with pytest.raises(ValueError, match="최소 101회"):
        ml.lotto_scores(lotto_draws(80))


def test_pension_scores_cover_positions_and_digits():
    scores = ml.pension_scores(pension_draws(150))
    assert len(scores) == 6
    assert all(set(position) == set(range(10)) for position in scores)
    assert all(0.0 < value < 1.0 for position in scores for value in position.values())


def test_pension_model_picks_up_a_planted_signal():
    scores = ml.pension_scores(pension_draws(150, first_digit=3))
    assert max(scores[0], key=scores[0].get) == 3
    assert scores[0][3] > 0.9


def test_pension_needs_enough_history():
    with pytest.raises(ValueError, match="최소 51회"):
        ml.pension_scores(pension_draws(40))
