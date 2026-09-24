"""로또 6/45 조합의 정확한 기준 분포.

공정성 검정(§5.2)의 기대 빈도로 쓴다. 근사나 몬테카를로가 아니라
조합론으로 정확히 센다 — 45개 중 6개 조합은 8,145,060가지뿐이라
합계는 동적 계획법으로, 연속번호는 닫힌 식으로 바로 구할 수 있다.
"""

from functools import lru_cache
from math import comb

NUMBERS = 45
PICK = 6
TOTAL = comb(NUMBERS, PICK)


@lru_cache(maxsize=None)
def _sum_distribution():
    dp = {(0, 0): 1}
    for number in range(1, NUMBERS + 1):
        nxt = dict(dp)
        for (picked, total), count in dp.items():
            if picked < PICK:
                key = (picked + 1, total + number)
                nxt[key] = nxt.get(key, 0) + count
        dp = nxt
    return {total: count for (picked, total), count in dp.items() if picked == PICK}


@lru_cache(maxsize=None)
def _adjacent_pair_distribution():
    # k개를 고르면 "연속 덩어리" 수 b에 대해 인접쌍은 k-b개다.
    # 덩어리가 b개인 조합 수 = C(n-k+1, b) * C(k-1, b-1)
    dist = {}
    for runs in range(1, PICK + 1):
        ways = comb(NUMBERS - PICK + 1, runs) * comb(PICK - 1, runs - 1)
        dist[PICK - runs] = dist.get(PICK - runs, 0) + ways
    return dist


@lru_cache(maxsize=None)
def _hypergeometric(population, successes, draws):
    low = max(0, draws - (population - successes))
    high = min(draws, successes)
    return {
        hits: comb(successes, hits) * comb(population - successes, draws - hits)
        for hits in range(low, high + 1)
    }


def sum_distribution():
    """번호 6개의 합 -> 그 합을 가진 조합 수."""
    return dict(_sum_distribution())


def adjacent_pair_distribution():
    """인접한 번호 쌍의 개수(0~5) -> 그런 조합 수."""
    return dict(_adjacent_pair_distribution())


def hypergeometric(population, successes, draws):
    """모집단에서 draws개를 뽑을 때 '성공' 개수 -> 그런 조합 수."""
    return dict(_hypergeometric(population, successes, draws))
