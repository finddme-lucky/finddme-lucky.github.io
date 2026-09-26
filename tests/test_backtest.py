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
