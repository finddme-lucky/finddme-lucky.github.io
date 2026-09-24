"""로또 인기 패턴 필터 (spec §5.3 L1).

당첨 확률을 바꾸지 않는다. 1등이 됐을 때 당첨금을 나눠 가질 사람 수를 줄이는 것이
목적이며, 사람들이 많이 고르는 모양(생일 편중·연속번호·용지 줄무늬 등)을 피한다.
"""

import json
from collections import Counter
from pathlib import Path

RULES_PATH = Path("rules/lotto645-unpopular.json")


def load_rules(path=RULES_PATH):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("schema") != 1:
        raise ValueError(f"{path}: 규칙 schema 불일치 ({config.get('schema')!r})")
    return config


def longest_run(numbers):
    """오름차순 번호에서 가장 긴 연속 구간의 길이."""
    longest = current = 1
    for low, high in zip(numbers, numbers[1:]):
        current = current + 1 if high - low == 1 else 1
        longest = max(longest, current)
    return longest


def unpopular_reasons(numbers, rules, past_combinations=()):
    """인기 패턴에 걸리는 이유 목록. 빈 목록이면 통과."""
    width = rules["gridWidth"]
    reasons = []
    if numbers[-1] <= rules["allLowMax"]:
        reasons.append("allLow")
    if longest_run(numbers) > rules["maxConsecutiveRun"]:
        reasons.append("consecutive")
    if max(Counter(number % 10 for number in numbers).values()) > rules["maxSameLastDigit"]:
        reasons.append("sameLastDigit")
    if max(Counter((number - 1) // width for number in numbers).values()) > rules["maxSameGridRow"]:
        reasons.append("gridRow")
    if max(Counter((number - 1) % width for number in numbers).values()) > rules["maxSameGridColumn"]:
        reasons.append("gridColumn")
    if sum(1 for number in numbers if number % 7 == 0) > rules["maxMultiplesOfSeven"]:
        reasons.append("multiplesOfSeven")
    gaps = {high - low for low, high in zip(numbers, numbers[1:])}
    if rules["rejectArithmeticProgression"] and len(gaps) == 1:
        reasons.append("arithmetic")
    if rules["rejectPastWinningCombination"] and tuple(numbers) in past_combinations:
        reasons.append("pastWinner")
    return reasons
