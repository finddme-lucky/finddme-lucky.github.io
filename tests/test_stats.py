from lucky.stats import adjacent_pairs, lotto_stats

DRAWS = [
    {"round": 1, "date": "2002-12-07", "numbers": [1, 2, 3, 11, 21, 45], "bonus": 5,
     "sales": 1000, "ranks": [{"rank": 1, "winners": 0, "prize": 0}]},
    {"round": 2, "date": "2002-12-14", "numbers": [2, 3, 4, 22, 23, 44], "bonus": 1,
     "sales": 2000, "ranks": [{"rank": 1, "winners": 2, "prize": 500}]},
    {"round": 3, "date": "2002-12-21", "numbers": [5, 6, 7, 8, 9, 10], "bonus": 2,
     "sales": 3000, "ranks": [{"rank": 1, "winners": 1, "prize": 900}]},
]


def test_adjacent_pairs_counts_consecutive_numbers():
    assert adjacent_pairs([1, 2, 3, 11, 21, 45]) == 2
    assert adjacent_pairs([5, 6, 7, 8, 9, 10]) == 5
    assert adjacent_pairs([1, 3, 5, 7, 9, 11]) == 0


def test_counts_cover_every_number_and_include_bonus_separately():
    stats = lotto_stats(DRAWS, recent=2)
    assert set(stats["counts"]) == set(range(1, 46))
    assert stats["counts"][2] == 2
    assert stats["counts"][45] == 1
    assert stats["counts"][12] == 0
    # 보너스 포함 집계에서만 1(2회차 보너스)·2(3회차 보너스)·5(1회차 보너스)가 하나씩 늘어난다
    assert stats["countsWithBonus"][1] == 2
    assert stats["countsWithBonus"][2] == 3
    assert stats["countsWithBonus"][5] == 2


def test_recent_counts_use_only_the_last_n_draws():
    stats = lotto_stats(DRAWS, recent=2)
    assert stats["recentCountsWindow"] == 2
    assert stats["recentCounts"][1] == 0  # 1은 1회차에만 나왔다
    assert stats["recentCounts"][2] == 1
    assert stats["recentCounts"][5] == 1


def test_gaps_measure_rounds_since_last_appearance():
    stats = lotto_stats(DRAWS)
    assert stats["gaps"][5] == 0  # 마지막 회차에 나옴
    assert stats["gaps"][2] == 1
    assert stats["gaps"][45] == 2
    assert stats["gaps"][12] is None  # 한 번도 안 나옴


def test_shape_distributions():
    stats = lotto_stats(DRAWS)
    assert stats["oddEven"] == {0: 0, 1: 0, 2: 1, 3: 1, 4: 0, 5: 1, 6: 0}
    assert stats["lowHigh"] == {0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 1, 6: 1}
    assert stats["sums"] == {45: 1, 83: 1, 98: 1}
    assert stats["adjacentPairs"] == {0: 0, 1: 0, 2: 1, 3: 1, 4: 0, 5: 1}
    assert stats["overlapWithPrevious"] == {0: 1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0}


def test_decades_split_numbers_into_five_bands():
    stats = lotto_stats(DRAWS)
    assert stats["decades"] == {"1-10": 12, "11-20": 1, "21-30": 3, "31-40": 0, "41-45": 2}


def test_series_carries_round_level_money_figures():
    stats = lotto_stats(DRAWS)
    assert stats["draws"] == 3
    assert stats["series"][1] == {
        "round": 2, "date": "2002-12-14", "sales": 2000,
        "firstWinners": 2, "firstPrize": 500,
    }


def test_empty_draws_produce_empty_but_complete_shape():
    stats = lotto_stats([])
    assert stats["draws"] == 0
    assert stats["series"] == []
    assert set(stats["counts"]) == set(range(1, 46))
    assert all(value == 0 for value in stats["counts"].values())
    assert all(value is None for value in stats["gaps"].values())


from lucky.stats import pension_stats

PENSION_DRAWS = [
    {"round": 1, "date": "2020-05-07", "group": 4, "first": "011391", "bonus": "060727",
     "ranks": [{"rank": 1, "prize": 1680000000, "store": 0, "online": 1, "total": 1},
               {"rank": "bonus", "prize": 120000000, "store": 2, "online": 5, "total": 7}]},
    {"round": 2, "date": "2020-05-14", "group": 1, "first": "123456", "bonus": "060727",
     "ranks": [{"rank": 1, "prize": 1680000000, "store": 1, "online": 1, "total": 2},
               {"rank": "bonus", "prize": 120000000, "store": 3, "online": 3, "total": 6}]},
]


def test_pension_group_counts_cover_all_five():
    stats = pension_stats(PENSION_DRAWS)
    assert stats["groups"] == {1: 1, 2: 0, 3: 0, 4: 1, 5: 0}


def test_pension_recent_groups_use_only_the_last_n_draws():
    stats = pension_stats(PENSION_DRAWS, recent=1)
    assert stats["recentCountsWindow"] == 1
    assert stats["recentGroups"] == {1: 1, 2: 0, 3: 0, 4: 0, 5: 0}


def test_pension_digits_are_counted_per_position_including_leading_zero():
    stats = pension_stats(PENSION_DRAWS)
    assert len(stats["firstDigits"]) == 6
    assert set(stats["firstDigits"][0]) == set(range(10))
    # 첫 자리: "0"(1회차) 과 "1"(2회차)
    assert stats["firstDigits"][0][0] == 1
    assert stats["firstDigits"][0][1] == 1
    # 마지막 자리: "1"(1회차) 과 "6"(2회차)
    assert stats["firstDigits"][5][1] == 1
    assert stats["firstDigits"][5][6] == 1
    # 보너스는 두 회차 모두 "060727"
    assert stats["bonusDigits"][0][0] == 2
    assert stats["bonusDigits"][1][6] == 2


def test_pension_series_carries_rank_ticket_totals():
    stats = pension_stats(PENSION_DRAWS)
    assert stats["draws"] == 2
    assert stats["series"][0] == {
        "round": 1, "date": "2020-05-07", "rankTotals": {"1": 1, "bonus": 7},
    }
