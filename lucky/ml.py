"""간단 ML 전략 (spec §5.3) — 로지스틱 회귀의 "다음 회차 출현" 확률을 점수로 쓴다.

과거에는 그럴듯하게 맞고 미래에는 맞지 않는다는 것을 2B-2 백테스트에서 나란히
보여주기 위한 장치이기도 하다. 실측(2026-09-24, 로또 1242회)에서 예측 확률은
0.1285~0.1368로 기준값 6/45 = 0.1333 주변에 붙어 있었다 — 사실상 신호가 없다.
"""

import numpy as np
from sklearn.linear_model import LogisticRegression

from lucky.strategies import DIGITS, LOTTO_NUMBERS, PENSION_POSITIONS

LOTTO_WARMUP = 100
PENSION_WARMUP = 50
WINDOWS = (10, 30, 100)
MAX_ITER = 1000


def _features(history, member):
    """history: 과거 회차의 집합 목록(최근이 뒤). -> (윈도별 출현 수…, 마지막 출현 이후 회차 수)"""
    counts = [sum(1 for item in history[-window:] if member in item) for window in WINDOWS]
    gap = next(
        (index for index, item in enumerate(reversed(history)) if member in item),
        len(history),
    )
    return (*counts, gap)


def _fit(features, labels):
    return LogisticRegression(max_iter=MAX_ITER).fit(
        np.array(features, dtype=float), np.array(labels)
    )


def _predict(model, rows):
    return model.predict_proba(np.array(rows, dtype=float))[:, 1]


def lotto_scores(draws, *, warmup=LOTTO_WARMUP):
    if len(draws) <= warmup:
        raise ValueError(
            f"lotto645: ml 전략은 최소 {warmup + 1}회가 필요하다 (현재 {len(draws)}회)"
        )
    history = [set(draw["numbers"]) for draw in draws]
    features, labels = [], []
    for index in range(warmup, len(history)):
        past = history[:index]
        for number in LOTTO_NUMBERS:
            features.append(_features(past, number))
            labels.append(1 if number in history[index] else 0)
    model = _fit(features, labels)
    predicted = _predict(model, [_features(history, number) for number in LOTTO_NUMBERS])
    return {number: float(value) for number, value in zip(LOTTO_NUMBERS, predicted)}


def pension_scores(draws, *, warmup=PENSION_WARMUP):
    if len(draws) <= warmup:
        raise ValueError(
            f"pension720: ml 전략은 최소 {warmup + 1}회가 필요하다 (현재 {len(draws)}회)"
        )
    histories = [
        [{int(draw["first"][position])} for draw in draws]
        for position in range(PENSION_POSITIONS)
    ]
    features, labels = [], []
    for history in histories:
        for index in range(warmup, len(history)):
            past = history[:index]
            for digit in DIGITS:
                features.append(_features(past, digit))
                labels.append(1 if digit in history[index] else 0)
    model = _fit(features, labels)
    return [
        {
            digit: float(value)
            for digit, value in zip(
                DIGITS, _predict(model, [_features(history, digit) for digit in DIGITS])
            )
        }
        for history in histories
    ]
