"""워크포워드 백테스트 (spec §5.4).

전략이 고른 번호를 과거 실제 추첨과 맞춰 본다. 목적은 어떤 전략이 낫다는 것을 보이는
것이 아니라, 무작위 기준선·이론값과 구분되지 않는다는 사실을 수치로 남기는 것이다.
"""

import json
from collections import Counter
from math import comb, sqrt

from scipy.stats import norm

from lucky import reference
from lucky import sets

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


def separation(scores, drawn):
    """뽑힌 번호와 안 뽑힌 번호의 평균 점수 차이. 비교 대상이 없으면 0."""
    drawn = set(drawn)
    inside = [score for number, score in scores.items() if number in drawn]
    outside = [score for number, score in scores.items() if number not in drawn]
    if not inside or not outside:
        return 0.0
    return sum(inside) / len(inside) - sum(outside) / len(outside)


def compare_with_random(entries, baseline="random", alpha=ALPHA):
    """각 전략의 5등 이상 적중률을 무작위 기준선과 맞대어 본다."""
    base = entries.get(baseline)
    others = [name for name in entries if name != baseline]
    pvalues = []
    for name in others:
        entry = entries[name]
        entry["pVsRandom"] = (
            None
            if base is None
            else two_proportion_p(entry["hits"], entry["games"], base["hits"], base["games"])
        )
        pvalues.append(1.0 if entry["pVsRandom"] is None else entry["pVsRandom"])
    for name, adjusted in zip(others, holm(pvalues) if pvalues else []):
        entries[name]["pAdj"] = adjusted
        entries[name]["distinguishable"] = (
            entries[name]["pVsRandom"] is not None and adjusted < alpha
        )
    if base is not None:
        base["pVsRandom"] = None
        base["pAdj"] = None
        base["distinguishable"] = False
    return entries


def run_lotto(draws, *, rules, strategies=None, rounds=LOTTO_EVAL_ROUNDS, keep_sets=False):
    """최근 rounds 회차를 워크포워드로 평가한다 (t회차는 t 이전 자료만으로 만든 세트로)."""
    names = tuple(strategies) if strategies else (*sets.LOTTO_STRATEGIES, "random")
    evaluated = draws[-rounds:] if rounds else draws
    start = len(draws) - len(evaluated)
    report = {"evalRounds": len(evaluated), "theory": lotto_theory(), "strategies": {}}

    for strategy in names:
        matches, ranks, recorded = Counter(), Counter(), []
        in_sample, out_of_sample = [], []
        for index in range(start, len(draws)):
            target, history = draws[index], draws[:index]
            scores = sets.lotto_scores(history, strategy)
            games = sets.build_lotto_set(
                history,
                strategy,
                target["round"],
                rules=rules,
                past_combinations={tuple(draw["numbers"]) for draw in history},
                scores=scores,
            )
            for game in games:
                matches[match_count(game, target["numbers"])] += 1
                rank = lotto_rank(game, target["numbers"], target["bonus"])
                if rank:
                    ranks[rank] += 1
            if strategy == "ml":
                in_sample.append(separation(scores, history[-1]["numbers"]))
                out_of_sample.append(separation(scores, target["numbers"]))
            if keep_sets:
                recorded.append({"round": target["round"], "games": games})

        played = sum(matches.values())
        hits = sum(count for matched, count in matches.items() if matched >= 3)
        entry = {
            "games": played,
            "matchCounts": {matched: matches.get(matched, 0) for matched in range(7)},
            "ranks": {rank: ranks.get(rank, 0) for rank in (1, 2, 3, 4, 5)},
            "meanMatches": (
                sum(matched * count for matched, count in matches.items()) / played if played else 0.0
            ),
            "hits": hits,
            "hitRate": hits / played if played else 0.0,
            "hitRateCI": wilson_interval(hits, played),
        }
        if strategy == "ml":
            entry["inSampleSeparation"] = sum(in_sample) / len(in_sample) if in_sample else 0.0
            entry["outOfSampleSeparation"] = (
                sum(out_of_sample) / len(out_of_sample) if out_of_sample else 0.0
            )
        if keep_sets:
            entry["sets"] = recorded
        report["strategies"][strategy] = entry

    compare_with_random(report["strategies"])
    return report


PENSION_PRIZES = {
    1: 1_680_000_000,
    2: 120_000_000,
    3: 1_000_000,
    4: 100_000,
    5: 50_000,
    6: 5_000,
    7: 1_000,
    "bonus": 120_000_000,
}
TICKET_PRICE = 1_000
TICKETS_PER_ROUND = 5  # 1~5조를 전부 산다 (spec §5.3 P2)


def trailing_match(number, winning):
    """오른쪽 끝부터 연속으로 같은 자리의 개수 (0~6)."""
    length = 0
    for mine, theirs in zip(reversed(number), reversed(winning)):
        if mine != theirs:
            break
        length += 1
    return length


def pension_prize(number, draw):
    """(끝자리 일치 길이, 1~5조를 전부 산 경우의 수령액)."""
    length = trailing_match(number, draw["first"])
    prize = 0
    if length == 6:
        prize += PENSION_PRIZES[1] + 4 * PENSION_PRIZES[2]
    elif length:
        prize += TICKETS_PER_ROUND * PENSION_PRIZES[8 - length]
    if trailing_match(number, draw["bonus"]) == 6:
        prize += TICKETS_PER_ROUND * PENSION_PRIZES["bonus"]
    return length, prize


def pension_theory():
    """끝자리 일치 길이의 이론 확률과 1~5조 구매 기준 기대 수익률."""
    rates = {length: 9 / 10 ** (length + 1) for length in range(6)}
    rates[6] = 1 / 10**6
    expected = rates[6] * (PENSION_PRIZES[1] + 4 * PENSION_PRIZES[2])
    expected += sum(
        rates[length] * TICKETS_PER_ROUND * PENSION_PRIZES[8 - length] for length in range(1, 6)
    )
    expected += (1 / 10**6) * TICKETS_PER_ROUND * PENSION_PRIZES["bonus"]
    cost = TICKETS_PER_ROUND * TICKET_PRICE
    return {"lengthRates": rates, "expectedPrize": expected, "returnRate": expected / cost}


def run_pension(draws, *, strategies=None, rounds=PENSION_EVAL_ROUNDS):
    """최근 rounds 회차를 워크포워드로 평가한다 (1~5조 전부 구매 가정)."""
    names = tuple(strategies) if strategies else sets.PENSION_STRATEGIES
    evaluated = draws[-rounds:] if rounds else draws
    start = len(draws) - len(evaluated)
    report = {"evalRounds": len(evaluated), "theory": pension_theory(), "strategies": {}}

    for strategy in names:
        lengths, won = Counter(), 0
        for index in range(start, len(draws)):
            target, history = draws[index], draws[:index]
            number = sets.build_pension_set(
                history, strategy, target["round"], scores=sets.pension_scores(history, strategy)
            )
            length, prize = pension_prize(number, target)
            lengths[length] += 1
            won += prize

        played = sum(lengths.values())
        hits = sum(count for length, count in lengths.items() if length >= 1)
        spent = played * TICKETS_PER_ROUND * TICKET_PRICE
        report["strategies"][strategy] = {
            "rounds": played,
            "lengths": {length: lengths.get(length, 0) for length in range(7)},
            "hits": hits,
            "games": played,  # compare_with_random이 쓰는 시행 횟수
            "hitRate": hits / played if played else 0.0,
            "hitRateCI": wilson_interval(hits, played),
            "spent": spent,
            "won": won,
            "returnRate": won / spent if spent else 0.0,
        }

    compare_with_random(report["strategies"])
    return report


from lucky import popularity, store

DISCLAIMER = (
    "전략이 무작위보다 낫다는 근거는 없다. 이 기록은 그것을 확인하기 위한 것이다."
)


def build_document(data_dir, *, now, rules, games=store.GAMES, strategies=None, rounds=None):
    """게임별 백테스트와 인기 규칙 근거를 한 문서로 묶는다."""
    document = {
        "schema": 1,
        "generatedAt": now.isoformat(timespec="seconds"),
        "disclaimer": DISCLAIMER,
    }
    for game in games:
        draws = store.load_draws(data_dir, game)
        if not draws:
            raise ValueError(f"{game}: 수집된 회차가 없다 — 먼저 collect를 실행할 것")
        if game == "lotto645":
            document[game] = run_lotto(
                draws,
                rules=rules,
                strategies=strategies,
                rounds=rounds or LOTTO_EVAL_ROUNDS,
            )
            document["popularity"] = popularity.evidence(draws, rules)
        else:
            document[game] = run_pension(
                draws, strategies=strategies, rounds=rounds or PENSION_EVAL_ROUNDS
            )
    return document


def save_document(data_dir, document):
    """이번에 계산하지 않은 게임 구간은 기존 파일에서 가져온다 (한 게임만 실행해도 지워지지 않게)."""
    path = data_dir / "backtest.json"
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}
        carried = {
            game: previous[game]
            for game in store.GAMES
            if game in previous and game not in document
        }
        if "lotto645" not in document and "popularity" in previous:
            carried["popularity"] = previous["popularity"]  # 근거 보강은 로또와 함께 계산된다
        document = {**document, **carried}
    return store.save_document_if_changed(data_dir, "backtest.json", document)
