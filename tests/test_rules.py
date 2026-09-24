import json
import random

import pytest

from lucky import rules


def loaded():
    return rules.load_rules()


def test_rules_file_loads_and_checks_schema(tmp_path):
    assert loaded()["gridWidth"] == 7
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema": 99}), encoding="utf-8")
    with pytest.raises(ValueError, match="규칙 schema 불일치"):
        rules.load_rules(bad)


def test_longest_run():
    assert rules.longest_run([1, 2, 3, 11, 21, 45]) == 3
    assert rules.longest_run([5, 6, 7, 8, 9, 10]) == 6
    assert rules.longest_run([1, 3, 5, 7, 9, 11]) == 1


def test_an_ordinary_spread_combination_passes():
    assert rules.unpopular_reasons([3, 11, 17, 28, 34, 42], loaded()) == []


@pytest.mark.parametrize(
    ("numbers", "reason"),
    [
        ([1, 5, 12, 19, 24, 31], "allLow"),          # 6개 전부 31 이하 (생일 편중)
        ([5, 6, 7, 8, 20, 41], "consecutive"),        # 연속 4개
        ([3, 13, 23, 33, 40, 44], "sameLastDigit"),   # 끝자리 3이 4개
        ([1, 2, 3, 4, 5, 40], "gridRow"),             # 용지 첫 줄에 5개
        ([1, 8, 15, 22, 29, 40], "gridColumn"),       # 용지 첫 칸에 5개
        ([7, 14, 21, 28, 33, 40], "multiplesOfSeven"),  # 7의 배수 4개 (등차수열도 아님)
        ([2, 9, 16, 23, 30, 37], "arithmetic"),       # 공차 7 등차수열
    ],
)
def test_each_popular_pattern_is_flagged(numbers, reason):
    assert reason in rules.unpopular_reasons(numbers, loaded())


def test_past_winning_combination_is_flagged():
    numbers = [3, 11, 17, 28, 34, 42]
    assert rules.unpopular_reasons(numbers, loaded()) == []
    assert rules.unpopular_reasons(numbers, loaded(), {tuple(numbers)}) == ["pastWinner"]


def test_rejection_rate_stays_around_one_in_ten():
    """규칙이 너무 많이 걸러내면 세트 생성이 느려지고, 너무 적게 걸러내면 의미가 없다.

    2026-09-24 실측: 무작위 조합 20만 개 중 9.87% 기각.
    """
    rng = random.Random(1)
    config = loaded()
    rejected = sum(
        1
        for _ in range(5000)
        if rules.unpopular_reasons(sorted(rng.sample(range(1, 46), 6)), config)
    )
    assert 0.05 < rejected / 5000 < 0.15
