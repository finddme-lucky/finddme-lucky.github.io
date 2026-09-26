import pytest

from lucky import rules as rules_module
from lucky import sets
from lucky.sources import lotto645
from tests.fakes import lotto_raw


def lotto_draws(count):
    return [lotto645.parse_row(lotto_raw(round_no)) for round_no in range(1, count + 1)]


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


CONFIG = rules_module.load_rules()


def test_lotto_set_has_five_games_of_six_sorted_numbers():
    games = sets.build_lotto_set(lotto_draws(120), "hot", 121, rules=CONFIG)
    assert len(games) == 5
    for game in games:
        assert len(game) == 6
        assert game == sorted(game)
        assert all(1 <= number <= 45 for number in game)


def test_lotto_games_never_share_a_number():
    games = sets.build_lotto_set(lotto_draws(120), "recent", 121, rules=CONFIG)
    flattened = [number for game in games for number in game]
    assert len(set(flattened)) == 30


def test_lotto_set_passes_the_unpopular_filter():
    draws = lotto_draws(120)
    past = {tuple(draw["numbers"]) for draw in draws}
    games = sets.build_lotto_set(draws, "cold", 121, rules=CONFIG, past_combinations=past)
    for game in games:
        assert rules_module.unpopular_reasons(game, CONFIG, past) == []


def test_lotto_set_is_stable_per_round_and_changes_next_round():
    draws = lotto_draws(120)
    first = sets.build_lotto_set(draws, "hot", 121, rules=CONFIG)
    assert first == sets.build_lotto_set(draws, "hot", 121, rules=CONFIG)
    assert first != sets.build_lotto_set(draws, "hot", 122, rules=CONFIG)
    assert first != sets.build_lotto_set(draws, "cold", 121, rules=CONFIG)


def test_lotto_set_gives_up_after_the_attempt_limit():
    impossible = dict(CONFIG, allLowMax=45)  # 어떤 조합도 통과할 수 없다
    with pytest.raises(ValueError, match="3회 안에"):
        sets.build_lotto_set(lotto_draws(120), "hot", 121, rules=impossible, max_attempts=3)


def test_lotto_set_works_with_the_ml_strategy():
    games = sets.build_lotto_set(lotto_draws(150), "ml", 151, rules=CONFIG)
    assert len({number for game in games for number in game}) == 30


def test_pension_set_is_six_digits_and_stable_per_round():
    draws = pension_draws(60)
    number = sets.build_pension_set(draws, "hot", 61)
    assert len(number) == 6 and number.isdigit()
    assert number == sets.build_pension_set(draws, "hot", 61)
    assert number != sets.build_pension_set(draws, "hot", 62)


def test_pension_random_strategy_differs_from_a_score_strategy():
    draws = pension_draws(60)
    assert sets.build_pension_set(draws, "random", 61) != sets.build_pension_set(draws, "cold", 61)


def test_strategy_lists_match_the_spec():
    assert sets.LOTTO_STRATEGIES == ("hot", "cold", "recent", "ml")
    assert sets.PENSION_STRATEGIES == ("hot", "cold", "recent", "ml", "random")


def test_build_lotto_set_accepts_precomputed_scores():
    draws = lotto_draws(120)
    scores = sets.lotto_scores(draws, "hot")
    assert sets.build_lotto_set(draws, "hot", 121, rules=CONFIG, scores=scores) == sets.build_lotto_set(
        draws, "hot", 121, rules=CONFIG
    )
