"""번호 세트 구성 (spec §5.3).

로또: 전략 점수로 30개를 뽑아 6개씩 5게임으로 나눈다 — 30개가 모두 달라 게임끼리
번호가 겹치지 않는다(L2). 한 게임이라도 인기 패턴(L1)에 걸리면 시드에 시도 번호를
붙여 처음부터 다시 뽑는다.
연금복권: 자리마다 숫자를 하나씩 뽑아 6자리 하나를 만든다. 1~5조를 전부 사는 것을
전제하므로 조는 고르지 않는다(P2).

어느 방식도 당첨 확률을 바꾸지 않는다. L1은 당첨 시 나눠 갖는 인원, L2·P2는
당첨 분포에만 영향을 준다.
"""

import random

from lucky import ml, sampling, strategies
from lucky import rules as rules_module

GAMES_PER_TICKET = 5
NUMBERS_PER_GAME = 6
MAX_ATTEMPTS = 1000
LOTTO_STRATEGIES = ("hot", "cold", "recent", "ml")
PENSION_STRATEGIES = ("hot", "cold", "recent", "ml", "random")


def lotto_scores(draws, strategy):
    if strategy == "ml":
        return ml.lotto_scores(draws)
    return strategies.lotto_scores(draws, strategy)


def pension_scores(draws, strategy):
    if strategy == "ml":
        return ml.pension_scores(draws)
    return strategies.pension_scores(draws, strategy)


def build_lotto_set(draws, strategy, round_no, *, rules, past_combinations=(), max_attempts=MAX_ATTEMPTS, scores=None):
    scores = lotto_scores(draws, strategy) if scores is None else scores
    for attempt in range(max_attempts):
        rng = random.Random(sampling.seed_for("lotto645", strategy, round_no, attempt))
        picked = sampling.weighted_sample(rng, scores, GAMES_PER_TICKET * NUMBERS_PER_GAME)
        games = [
            sorted(picked[start : start + NUMBERS_PER_GAME])
            for start in range(0, len(picked), NUMBERS_PER_GAME)
        ]
        if all(
            not rules_module.unpopular_reasons(game, rules, past_combinations) for game in games
        ):
            return games
    raise ValueError(
        f"lotto645 {round_no}회 {strategy}: {max_attempts}회 안에 "
        "인기 패턴을 피한 세트를 만들지 못했다"
    )


def build_pension_set(draws, strategy, round_no, *, scores=None):
    position_scores = pension_scores(draws, strategy) if scores is None else scores
    rng = random.Random(sampling.seed_for("pension720", strategy, round_no))
    digits = [sampling.weighted_sample(rng, scores, 1)[0] for scores in position_scores]
    return "".join(str(digit) for digit in digits)
