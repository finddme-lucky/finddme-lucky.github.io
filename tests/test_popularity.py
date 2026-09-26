import pytest

from lucky import popularity
from lucky import rules as rules_module

CONFIG = rules_module.load_rules()
ALL_LOW = [1, 5, 12, 19, 24, 31]      # 6개 전부 31 이하 → allLow
SPREAD = [3, 11, 17, 28, 34, 42]      # 어느 규칙에도 걸리지 않는다


def draw(round_no, numbers, winners, sales=1_000_000_000):
    return {
        "round": round_no,
        "date": "2002-12-07",
        "numbers": numbers,
        "bonus": 45,
        "sales": sales,
        "ranks": [
            {"rank": 1, "winners": 0, "prize": 0},
            {"rank": 2, "winners": 0, "prize": 0},
            {"rank": 3, "winners": 0, "prize": 0},
            {"rank": 4, "winners": 0, "prize": 0},
            {"rank": 5, "winners": winners, "prize": 5000},
        ],
    }


def test_winner_ratios_divide_observed_by_the_sales_based_expectation():
    games = 1_000_000_000 / 1000
    expected = games * popularity.FIFTH_PRIZE_RATE
    ratios = popularity.winner_ratios([draw(1, SPREAD, round(expected))])
    assert ratios[0] == pytest.approx(1.0, rel=1e-3)
    assert popularity.winner_ratios([draw(2, SPREAD, 0)]) == [None]


def test_normalize_removes_an_era_level_shift():
    ratios = [1.0] * 60 + [2.0] * 60
    normalized = popularity.normalize(ratios, window=21)
    middle = normalized[10:50] + normalized[70:110]
    assert all(value == pytest.approx(1.0) for value in middle)


def test_normalize_keeps_a_single_round_standing_out():
    ratios = [1.0] * 60
    ratios[30] = 3.0
    normalized = popularity.normalize(ratios, window=21)
    assert normalized[30] == pytest.approx(3.0)
    assert normalized[10] == pytest.approx(1.0)


def test_evidence_finds_a_planted_association():
    # 당첨자가 많은 회차에만 생일 편중 조합을 심는다
    draws = []
    for round_no in range(1, 61):
        if round_no % 2 == 0:
            draws.append(draw(round_no, ALL_LOW, 40000))
        else:
            draws.append(draw(round_no, SPREAD, 20000))

    report = popularity.evidence(draws, CONFIG, window=11)

    assert report["rounds"] == 60
    assert report["high"]["flaggedRate"] == pytest.approx(1.0)
    assert report["low"]["flaggedRate"] == pytest.approx(0.0)
    assert report["byRule"]["allLow"]["difference"] == pytest.approx(1.0)
    assert report["byRule"]["consecutive"]["difference"] == pytest.approx(0.0)
    assert report["caveat"] == popularity.CAVEAT
    # "관계 없음"과 "한 번도 안 걸림"을 구분할 수 있어야 한다
    assert report["byRule"]["allLow"]["highFlagged"] == 30
    assert report["byRule"]["allLow"]["lowFlagged"] == 0
    assert report["byRule"]["consecutive"]["highFlagged"] == 0
    assert report["byRule"]["consecutive"]["lowFlagged"] == 0


def test_evidence_reports_no_difference_when_patterns_are_unrelated_to_winners():
    draws = [
        draw(round_no, SPREAD, 20000 + (round_no % 7) * 500) for round_no in range(1, 61)
    ]
    report = popularity.evidence(draws, CONFIG, window=11)
    assert report["high"]["flaggedRate"] == 0.0
    assert report["low"]["flaggedRate"] == 0.0


def test_evidence_shape_covers_deciles_rules_and_eras():
    draws = [
        draw(round_no, ALL_LOW if round_no % 3 == 0 else SPREAD, 20000 + round_no * 10)
        for round_no in range(1, 121)
    ]
    report = popularity.evidence(draws, CONFIG, window=21)

    assert set(report) == {
        "window", "rounds", "high", "low", "topDecile", "bottomDecile", "byRule", "byEra", "caveat",
    }
    assert set(report["byRule"]) == set(popularity.RULE_IDS)
    assert "pastWinner" not in report["byRule"]
    for group in ("high", "low", "topDecile", "bottomDecile"):
        assert 0.0 <= report[group]["flaggedRate"] <= 1.0
        assert report[group]["rounds"] > 0
    assert report["byEra"] and all(era["rounds"] > 0 for era in report["byEra"])
    assert [(era["from"], era["to"]) for era in report["byEra"]] == [(1, 100), (101, 400)]


def test_winner_ratios_skip_rounds_without_sales():
    assert popularity.winner_ratios([draw(1, SPREAD, 20000, sales=0)]) == [None]
