"""다음 회차 번호 세트 (spec §5.3) → data/predictions.json."""

from lucky import sets, store

DISCLAIMER = "어떤 전략도 당첨 확률을 바꾸지 않는다. 과거 성적은 백테스트 결과와 함께 볼 것."


def _pick(available, strategy):
    if strategy is None:
        return available
    if strategy not in available:
        raise ValueError(f"알 수 없는 전략 {strategy!r} (가능: {', '.join(available)})")
    return (strategy,)


def _lotto_section(draws, round_no, rules, strategy):
    past = {tuple(draw["numbers"]) for draw in draws}
    return {
        "round": round_no,
        "sets": [
            {
                "strategy": name,
                "games": sets.build_lotto_set(
                    draws, name, round_no, rules=rules, past_combinations=past
                ),
            }
            for name in _pick(sets.LOTTO_STRATEGIES, strategy)
        ],
    }


def _pension_section(draws, round_no, strategy):
    return {
        "round": round_no,
        "purchase": "all-groups",
        "sets": [
            {"strategy": name, "number": sets.build_pension_set(draws, name, round_no)}
            for name in _pick(sets.PENSION_STRATEGIES, strategy)
        ],
    }


def build_predictions(data_dir, *, now, rules, games=store.GAMES, strategy=None, round_no=None):
    document = {
        "schema": 1,
        "generatedAt": now.isoformat(timespec="seconds"),
        "disclaimer": DISCLAIMER,
    }
    for game in games:
        draws = store.load_draws(data_dir, game)
        if not draws:
            raise ValueError(f"{game}: 수집된 회차가 없다 — 먼저 collect를 실행할 것")
        target = round_no if round_no is not None else draws[-1]["round"] + 1
        history = [draw for draw in draws if draw["round"] < target]
        if game == "lotto645":
            document[game] = _lotto_section(history, target, rules, strategy)
        else:
            document[game] = _pension_section(history, target, strategy)
    return document


def save_predictions(data_dir, document):
    return store.save_document_if_changed(data_dir, "predictions.json", document)
