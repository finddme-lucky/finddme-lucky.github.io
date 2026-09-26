from math import comb

import pytest

from lucky import backtest


def test_match_count():
    assert backtest.match_count([1, 2, 3, 4, 5, 6], [1, 2, 3, 40, 41, 42]) == 3
    assert backtest.match_count([1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]) == 0
    assert backtest.match_count([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6]) == 6


def test_lotto_rank_covers_every_prize_tier():
    winning = [1, 2, 3, 4, 5, 6]
    assert backtest.lotto_rank([1, 2, 3, 4, 5, 6], winning, 7) == 1
    assert backtest.lotto_rank([1, 2, 3, 4, 5, 7], winning, 7) == 2   # 5개 + 보너스
    assert backtest.lotto_rank([1, 2, 3, 4, 5, 8], winning, 7) == 3   # 5개, 보너스 없음
    assert backtest.lotto_rank([1, 2, 3, 4, 8, 9], winning, 7) == 4
    assert backtest.lotto_rank([1, 2, 3, 8, 9, 10], winning, 7) == 5
    assert backtest.lotto_rank([1, 2, 8, 9, 10, 11], winning, 7) is None


def test_lotto_theory_is_the_exact_hypergeometric():
    theory = backtest.lotto_theory()
    assert sum(theory["matchRates"].values()) == pytest.approx(1.0)
    assert theory["matchRates"][0] == pytest.approx(comb(39, 6) / comb(45, 6))
    assert theory["matchRates"][6] == pytest.approx(1 / comb(45, 6))
    # 5등 이상 = 3개 이상 일치
    expected_hit = sum(
        comb(6, k) * comb(39, 6 - k) for k in (3, 4, 5, 6)
    ) / comb(45, 6)
    assert theory["hitRate"] == pytest.approx(expected_hit)
    assert theory["hitRate"] == pytest.approx(0.023834, abs=1e-6)  # 5등 이상 = 3개 이상 일치
    assert theory["meanMatches"] == pytest.approx(6 * 6 / 45)


def test_wilson_interval_brackets_the_observed_rate():
    low, high = backtest.wilson_interval(30, 1000)
    assert low < 0.03 < high
    assert 0.0 < low and high < 0.1
    assert backtest.wilson_interval(0, 0) == (0.0, 0.0)
    wide, narrow = backtest.wilson_interval(3, 10), backtest.wilson_interval(300, 1000)
    assert (wide[1] - wide[0]) > (narrow[1] - narrow[0])


def test_two_proportion_p_is_large_for_equal_rates_and_small_for_different_ones():
    assert backtest.two_proportion_p(50, 1000, 50, 1000) == pytest.approx(1.0)
    assert backtest.two_proportion_p(50, 1000, 55, 1000) > 0.5
    assert backtest.two_proportion_p(200, 1000, 50, 1000) < 1e-10
    assert backtest.two_proportion_p(0, 0, 5, 10) is None


def test_holm_adjusts_and_keeps_order():
    assert backtest.holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    assert backtest.holm([0.5, 0.9]) == [1.0, 1.0]


from lucky import rules as rules_module
from lucky import sets
from lucky.sources import lotto645
from tests.fakes import lotto_raw

CONFIG = rules_module.load_rules()


def lotto_draws(count):
    return [lotto645.parse_row(lotto_raw(round_no)) for round_no in range(1, count + 1)]


def test_separation_is_the_gap_between_drawn_and_undrawn_scores():
    scores = {1: 1.0, 2: 1.0, 3: 0.0, 4: 0.0}
    assert backtest.separation(scores, [1, 2]) == pytest.approx(1.0)
    assert backtest.separation(scores, [3, 4]) == pytest.approx(-1.0)
    assert backtest.separation(scores, [1, 3]) == pytest.approx(0.0)
    assert backtest.separation(scores, [1, 2, 3, 4]) == 0.0  # 전부 뽑히면 비교 대상이 없다


def test_run_lotto_reports_every_strategy_with_theory_alongside():
    report = backtest.run_lotto(lotto_draws(120), rules=CONFIG, strategies=("hot", "random"), rounds=5)

    assert report["evalRounds"] == 5
    assert report["theory"]["hitRate"] == pytest.approx(backtest.lotto_theory()["hitRate"])
    assert set(report["strategies"]) == {"hot", "random"}
    entry = report["strategies"]["hot"]
    assert entry["games"] == 25  # 5회차 × 5게임
    assert sum(entry["matchCounts"].values()) == 25
    assert set(entry["matchCounts"]) == set(range(7))
    assert set(entry["ranks"]) == {1, 2, 3, 4, 5}
    assert 0.0 <= entry["hitRate"] <= 1.0
    assert entry["hitRateCI"][0] <= entry["hitRate"] <= entry["hitRateCI"][1]
    assert entry["meanMatches"] == pytest.approx(
        sum(matched * count for matched, count in entry["matchCounts"].items()) / 25
    )


def test_run_lotto_marks_strategies_against_the_random_baseline():
    report = backtest.run_lotto(lotto_draws(120), rules=CONFIG, strategies=("hot", "cold", "random"), rounds=5)

    assert report["strategies"]["random"]["pVsRandom"] is None
    assert report["strategies"]["random"]["distinguishable"] is False
    for name in ("hot", "cold"):
        entry = report["strategies"][name]
        assert 0.0 <= entry["pVsRandom"] <= 1.0
        assert entry["pAdj"] >= entry["pVsRandom"]
        assert entry["distinguishable"] is (entry["pAdj"] < backtest.ALPHA)


def test_run_lotto_uses_only_past_draws_for_each_round():
    draws = lotto_draws(120)
    report = backtest.run_lotto(draws, rules=CONFIG, strategies=("hot",), rounds=3, keep_sets=True)

    for record in report["strategies"]["hot"]["sets"]:
        index = next(i for i, draw in enumerate(draws) if draw["round"] == record["round"])
        history = draws[:index]
        expected = sets.build_lotto_set(
            history,
            "hot",
            record["round"],
            rules=CONFIG,
            past_combinations={tuple(draw["numbers"]) for draw in history},
        )
        assert record["games"] == expected


def test_run_lotto_is_deterministic():
    draws = lotto_draws(120)
    first = backtest.run_lotto(draws, rules=CONFIG, strategies=("recent",), rounds=4)
    second = backtest.run_lotto(draws, rules=CONFIG, strategies=("recent",), rounds=4)
    assert first == second


def test_ml_entry_carries_fit_versus_evaluation_separation():
    report = backtest.run_lotto(lotto_draws(130), rules=CONFIG, strategies=("ml", "random"), rounds=3)
    entry = report["strategies"]["ml"]
    assert "inSampleSeparation" in entry and "outOfSampleSeparation" in entry
    assert "inSampleSeparation" not in report["strategies"]["random"]
