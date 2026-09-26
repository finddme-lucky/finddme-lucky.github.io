"""워크포워드 백테스트 (spec §5.4).

전략이 고른 번호를 과거 실제 추첨과 맞춰 본다. 목적은 어떤 전략이 낫다는 것을 보이는
것이 아니라, 무작위 기준선·이론값과 구분되지 않는다는 사실을 수치로 남기는 것이다.
"""

from math import comb, sqrt

from scipy.stats import norm

from lucky import reference

LOTTO_EVAL_ROUNDS = 300
PENSION_EVAL_ROUNDS = 200
ALPHA = 0.05
RANK_BY_MATCHES = {6: 1, 5: 3, 4: 4, 3: 5}


def match_count(game, winning):
    return len(set(game) & set(winning))


def lotto_rank(game, winning, bonus):
    """일치 개수로 등수를 매긴다. 5개 일치 + 보너스는 2등."""
    matched = match_count(game, winning)
    if matched == 5 and bonus in game:
        return 2
    return RANK_BY_MATCHES.get(matched)


def lotto_theory():
    """정확한 초기하 이론값 — 일치 개수 확률, 5등 이상 확률, 평균 일치 개수."""
    rates = {
        matched: count / reference.TOTAL
        for matched, count in reference.hypergeometric(45, 6, 6).items()
    }
    return {
        "matchRates": rates,
        "hitRate": sum(rate for matched, rate in rates.items() if matched >= 3),
        "meanMatches": sum(matched * rate for matched, rate in rates.items()),
    }


def wilson_interval(successes, trials, z=1.96):
    """비율의 Wilson 신뢰구간 — 적중이 드물어도 0 아래로 내려가지 않는다."""
    if trials == 0:
        return (0.0, 0.0)
    rate = successes / trials
    denominator = 1 + z**2 / trials
    centre = (rate + z**2 / (2 * trials)) / denominator
    margin = z * sqrt(rate * (1 - rate) / trials + z**2 / (4 * trials**2)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def two_proportion_p(successes_a, trials_a, successes_b, trials_b):
    """두 적중률이 같다는 가정에서의 양측 p값 (정규 근사)."""
    if not trials_a or not trials_b:
        return None
    pooled = (successes_a + successes_b) / (trials_a + trials_b)
    if pooled in (0.0, 1.0):
        return 1.0
    standard_error = sqrt(pooled * (1 - pooled) * (1 / trials_a + 1 / trials_b))
    if standard_error == 0:
        return 1.0
    z = (successes_a / trials_a - successes_b / trials_b) / standard_error
    return float(2 * norm.sf(abs(z)))


def holm(pvalues):
    """Holm 보정. 입력 순서를 유지한 보정 p값을 돌려준다."""
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted
