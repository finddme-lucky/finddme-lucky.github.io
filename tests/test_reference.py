from math import comb

from lucky import reference


def test_total_matches_combinations():
    assert reference.TOTAL == comb(45, 6) == 8145060


def test_sum_distribution_totals_and_range():
    dist = reference.sum_distribution()
    assert sum(dist.values()) == reference.TOTAL
    assert min(dist) == 21 and max(dist) == 255
    assert dist[21] == 1 and dist[255] == 1


def test_sum_distribution_is_symmetric():
    dist = reference.sum_distribution()
    assert all(count == dist[276 - value] for value, count in dist.items())


def test_sum_distribution_returns_a_fresh_dict_each_call():
    first = reference.sum_distribution()
    first[21] = 999
    assert reference.sum_distribution()[21] == 1


def test_adjacent_pair_distribution():
    dist = reference.adjacent_pair_distribution()
    assert sum(dist.values()) == reference.TOTAL
    assert set(dist) == {0, 1, 2, 3, 4, 5}
    assert dist[0] == comb(40, 6)  # 연속번호가 하나도 없는 조합
    assert dist[5] == 40  # 6개가 전부 연속 (1~6 … 40~45)
    assert dist == {0: 3838380, 1: 3290040, 2: 913900, 3: 98800, 4: 3900, 5: 40}


def test_adjacent_pair_distribution_returns_a_fresh_dict_each_call():
    first = reference.adjacent_pair_distribution()
    first[0] = 0
    assert reference.adjacent_pair_distribution()[0] == comb(40, 6)


def test_hypergeometric_matches_direct_formula():
    dist = reference.hypergeometric(45, 23, 6)  # 홀수 23개 중 몇 개가 뽑히나
    assert sum(dist.values()) == comb(45, 6)
    assert dist[6] == comb(23, 6)
    assert dist[0] == comb(22, 6)
    assert dist[3] == comb(23, 3) * comb(22, 3)


def test_hypergeometric_omits_impossible_counts():
    dist = reference.hypergeometric(10, 3, 8)
    assert set(dist) == {1, 2, 3}
    assert sum(dist.values()) == comb(10, 8)


def test_hypergeometric_returns_a_fresh_dict_each_call():
    first = reference.hypergeometric(45, 6, 6)
    first[0] = 0
    assert reference.hypergeometric(45, 6, 6)[0] == comb(39, 6)
