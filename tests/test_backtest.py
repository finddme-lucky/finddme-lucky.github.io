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


from pathlib import Path

from lucky import rules as rules_module
from lucky import sets, store
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


def test_run_lotto_random_hit_rate_brackets_the_theory_value_on_real_data():
    """spec §10: 백테스트 코드 자체(등수 판정·집계·CI)가 맞는지는, random 전략의
    실제 집계 결과가 정확한 초기하 이론값을 담고 있는지로 검사한다.

    관측치(점추정)는 300회의 표본 오차로 이론값과 정확히 같을 수 없으므로, 여기서는
    Wilson 95% 구간이 이론값을 포함하는지를 확인한다 — 이것이 파이프라인(등수 판정
    → matches 집계 → hitRate/CI 계산)이 이론과 정합함을 보여주는 올바른 단언이다.
    ml 전략은 느리므로(~0.31초/회) strategies=("random",)로만 돌려 15초 안에 끝낸다.
    """
    draws = store.load_draws(Path("data"), "lotto645")
    report = backtest.run_lotto(draws, rules=CONFIG, strategies=("random",), rounds=300)
    entry = report["strategies"]["random"]
    theory_hit_rate = backtest.lotto_theory()["hitRate"]
    assert theory_hit_rate == pytest.approx(0.023834, abs=1e-6)
    assert entry["hitRateCI"][0] <= theory_hit_rate <= entry["hitRateCI"][1]


def pension_draws(count):
    return [
        {
            "round": round_no,
            "date": "2020-05-07",
            "group": round_no % 5 + 1,
            "first": f"{round_no * 123457 % 1_000_000:06d}",
            "bonus": f"{round_no * 654321 % 1_000_000:06d}",
        }
        for round_no in range(1, count + 1)
    ]


def test_trailing_match_counts_from_the_right():
    assert backtest.trailing_match("123456", "123456") == 6
    assert backtest.trailing_match("923456", "123456") == 5
    assert backtest.trailing_match("111456", "123456") == 3
    assert backtest.trailing_match("123455", "123456") == 0


def test_pension_prize_follows_the_rank_table():
    draw = {"first": "123456", "bonus": "999999"}
    assert backtest.pension_prize("123456", draw) == (
        6,
        backtest.PENSION_PRIZES[1] + 4 * backtest.PENSION_PRIZES[2],
    )
    assert backtest.pension_prize("923456", draw) == (5, 5 * backtest.PENSION_PRIZES[3])
    assert backtest.pension_prize("999996", draw) == (1, 5 * backtest.PENSION_PRIZES[7])
    assert backtest.pension_prize("123450", draw) == (0, 0)
    # 보너스 번호와 끝 6자리가 같으면 조와 무관하게 5장 모두 보너스 등위
    assert backtest.pension_prize("999999", draw) == (0, 5 * backtest.PENSION_PRIZES["bonus"])


def test_pension_theory_matches_the_hand_computed_return():
    theory = backtest.pension_theory()
    assert sum(theory["lengthRates"].values()) == pytest.approx(1.0)
    assert theory["lengthRates"][0] == pytest.approx(0.9)
    assert theory["lengthRates"][6] == pytest.approx(1e-6)
    # 1등 2,160원 + 3~7등 990원 + 보너스 600원 = 3,750원 (5,000원 지출 기준 75%)
    assert theory["expectedPrize"] == pytest.approx(3750.0)
    assert theory["returnRate"] == pytest.approx(0.75)


def test_run_pension_reports_return_rate_against_theory():
    report = backtest.run_pension(pension_draws(80), strategies=("hot", "random"), rounds=10)

    assert report["evalRounds"] == 10
    assert report["theory"]["returnRate"] == pytest.approx(0.75)
    entry = report["strategies"]["hot"]
    assert entry["rounds"] == 10
    assert sum(entry["lengths"].values()) == 10
    assert set(entry["lengths"]) == set(range(7))
    assert entry["spent"] == 10 * 5 * backtest.TICKET_PRICE
    assert entry["returnRate"] == pytest.approx(entry["won"] / entry["spent"])
    assert report["strategies"]["random"]["pVsRandom"] is None


def test_run_pension_uses_only_past_draws_for_each_round():
    draws = pension_draws(80)
    report = backtest.run_pension(draws, strategies=("cold",), rounds=5, keep_sets=True)

    for record in report["strategies"]["cold"]["sets"]:
        index = next(i for i, draw in enumerate(draws) if draw["round"] == record["round"])
        history = draws[:index]
        expected = sets.build_pension_set(history, "cold", record["round"])
        assert record["number"] == expected


def test_run_pension_is_deterministic():
    draws = pension_draws(80)
    first = backtest.run_pension(draws, strategies=("cold",), rounds=5)
    second = backtest.run_pension(draws, strategies=("cold",), rounds=5)
    assert first == second
