import random
from datetime import date, timedelta

from lucky import fairness


def fair_lotto_draws(count, *, seed=7, forced=None):
    rng = random.Random(seed)
    start = date(2002, 12, 7)
    draws = []
    for index in range(1, count + 1):
        if forced is None:
            numbers = sorted(rng.sample(range(1, 46), 6))
        else:
            rest = [n for n in range(1, 46) if n != forced]
            numbers = sorted([forced] + rng.sample(rest, 5))
        bonus = rng.choice([n for n in range(1, 46) if n not in numbers])
        draws.append({
            "round": index,
            "date": (start + timedelta(days=7 * (index - 1))).isoformat(),
            "numbers": numbers,
            "bonus": bonus,
            "sales": 1000,
            "ranks": [{"rank": 1, "winners": 0, "prize": 0}],
        })
    return draws


def fair_pension_draws(count, *, seed=11, fixed_first_digit=None):
    rng = random.Random(seed)
    start = date(2020, 5, 7)
    draws = []
    for index in range(1, count + 1):
        digits = [rng.randrange(10) for _ in range(6)]
        if fixed_first_digit is not None:
            digits[0] = fixed_first_digit
        draws.append({
            "round": index,
            "date": (start + timedelta(days=7 * (index - 1))).isoformat(),
            "group": rng.randrange(1, 6),
            "first": "".join(str(digit) for digit in digits),
            "bonus": "".join(str(rng.randrange(10)) for _ in range(6)),
            "ranks": [{"rank": 1, "prize": 1680000000, "store": 0, "online": 1, "total": 1}],
        })
    return draws


def by_id(results):
    return {result["id"]: result for result in results}


def test_holm_adjusts_and_keeps_input_order():
    assert fairness.holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


def test_holm_caps_at_one_and_is_monotone():
    assert fairness.holm([0.5, 0.9]) == [1.0, 1.0]


def test_merge_small_merges_until_expected_is_large_enough():
    rows = [("a", 1, 1.0), ("b", 2, 2.0), ("c", 3, 3.0), ("d", 10, 10.0)]
    assert fairness.merge_small(rows) == [("a~b~c", 6, 6.0), ("d", 10, 10.0)]


def test_merge_small_folds_the_leftover_tail_into_the_previous_bucket():
    rows = [("a", 10, 10.0), ("b", 1, 1.0)]
    assert fairness.merge_small(rows) == [("a~b", 11, 11.0)]


def test_goodness_of_fit_normalizes_relative_weights():
    observed = {0: 50, 1: 50}
    result = fairness.goodness_of_fit("t", "라벨", observed, {0: 1, 1: 1})
    assert result["n"] == 100
    assert result["dof"] == 1
    assert result["stat"] == 0.0
    assert result["p"] > 0.99
    # 가중치 크기는 상관없다 — 비율만 쓴다
    scaled = fairness.goodness_of_fit("t", "라벨", observed, {0: 8145060, 1: 8145060})
    assert scaled["stat"] == result["stat"]


def test_goodness_of_fit_flags_a_lopsided_observation():
    result = fairness.goodness_of_fit("t", "라벨", {0: 90, 1: 10}, {0: 1, 1: 1})
    assert result["stat"] == 64.0
    assert result["p"] < 1e-10


def test_goodness_of_fit_skips_when_there_is_nothing_to_compare():
    result = fairness.goodness_of_fit("t", "라벨", {0: 2, 1: 1}, {0: 1, 1: 1})
    assert result["p"] is None
    assert "note" in result


def test_fair_lotto_draws_show_no_bias_evidence():
    report = fairness.run_lotto(fair_lotto_draws(600), recent=300)
    assert report["alpha"] == 0.05
    assert report["recentWindow"] == 300
    assert {result["id"] for result in report["all"]} == {
        "numbers", "numbersWithBonus", "oddEven", "lowHigh", "sum", "adjacent", "overlap",
    }
    assert not any(result["biased"] for result in report["all"])
    assert not any(result["biased"] for result in report["recent"])


def test_a_number_forced_into_every_lotto_draw_is_detected():
    report = fairness.run_lotto(fair_lotto_draws(600, forced=7), recent=300)
    results = by_id(report["all"])
    assert results["numbers"]["biased"] is True
    assert results["numbers"]["pAdj"] < 0.05


def test_fair_pension_draws_show_no_bias_evidence():
    report = fairness.run_pension(fair_pension_draws(600), recent=200)
    assert {result["id"] for result in report["all"]} >= {"groups", "first1", "bonus1"}
    assert len(report["all"]) == 13
    assert not any(result["biased"] for result in report["all"])


def test_a_fixed_pension_first_digit_is_detected():
    report = fairness.run_pension(fair_pension_draws(600, fixed_first_digit=3), recent=200)
    results = by_id(report["all"])
    assert results["first1"]["biased"] is True
    assert not results["bonus1"]["biased"]


def test_too_few_draws_produce_skipped_tests_rather_than_errors():
    report = fairness.run_lotto(fair_lotto_draws(2), recent=2)
    assert all(result["biased"] is False for result in report["all"])
    assert any(result["p"] is None for result in report["all"])
