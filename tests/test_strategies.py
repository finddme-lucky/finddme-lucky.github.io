import pytest

from lucky.strategies import HALF_LIFE, lotto_scores

DRAWS = [
    {"round": 1, "date": "2002-12-07", "numbers": [1, 2, 3, 4, 5, 6], "bonus": 7},
    {"round": 2, "date": "2002-12-14", "numbers": [1, 2, 3, 7, 8, 9], "bonus": 10},
    {"round": 3, "date": "2002-12-21", "numbers": [1, 10, 11, 12, 13, 14], "bonus": 2},
]


def test_every_strategy_scores_all_45_numbers():
    for strategy in ("hot", "cold", "recent", "random"):
        scores = lotto_scores(DRAWS, strategy)
        assert set(scores) == set(range(1, 46))
        assert all(isinstance(value, float) for value in scores.values())


def test_hot_counts_appearances_in_the_window():
    scores = lotto_scores(DRAWS, "hot")
    assert scores[1] == 3.0
    assert scores[2] == 2.0
    assert scores[14] == 1.0
    assert scores[45] == 0.0

    latest_only = lotto_scores(DRAWS, "hot", window=1)
    assert latest_only[1] == 1.0
    assert latest_only[2] == 0.0


def test_cold_counts_rounds_since_the_last_appearance():
    scores = lotto_scores(DRAWS, "cold")
    assert scores[1] == 0.0    # 마지막 회차에 나왔다
    assert scores[7] == 1.0    # 2회차가 마지막
    assert scores[4] == 2.0    # 1회차가 마지막
    assert scores[45] == 3.0   # 한 번도 안 나왔다 (전체 회차 수)


def test_recent_weights_newer_draws_more():
    scores = lotto_scores(DRAWS, "recent")
    assert scores[1] == pytest.approx(1.0 + 0.5 ** (1 / HALF_LIFE) + 0.5 ** (2 / HALF_LIFE))
    assert scores[14] == pytest.approx(1.0)
    assert scores[4] == pytest.approx(0.5 ** (2 / HALF_LIFE))
    assert scores[45] == 0.0
    assert scores[14] > scores[4]


def test_random_is_flat():
    assert set(lotto_scores(DRAWS, "random").values()) == {1.0}


def test_unknown_strategy_is_rejected():
    with pytest.raises(ValueError, match="알 수 없는 전략"):
        lotto_scores(DRAWS, "psychic")
