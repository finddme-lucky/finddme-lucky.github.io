"""수집 레코드 검증 — 통과하지 못하면 저장하지 않는다 (spec §3.4)."""

import re

from lucky.errors import ValidationError

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LOTTO_RANKS = [1, 2, 3, 4, 5]
PENSION_RANKS = [1, 2, 3, 4, 5, 6, 7, "bonus"]
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


def _is_int(value, lo=0, hi=None):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= lo
        and (hi is None or value <= hi)
    )


def _is_six_digits(value):
    return isinstance(value, str) and len(value) == 6 and value.isascii() and value.isdigit()


def _check_sequence(game, existing, new):
    prev = existing[-1] if existing else None
    for draw in new:
        expected = prev["round"] + 1 if prev else 1
        if draw["round"] != expected:
            raise ValidationError(f"{game}: 회차 불연속 — {expected}회 기대, {draw['round']}회 받음")
        if not (isinstance(draw["date"], str) and DATE_RE.match(draw["date"])):
            raise ValidationError(f"{game} {draw['round']}회: 추첨일 형식 이상 {draw['date']!r}")
        if prev and draw["date"] <= prev["date"]:
            raise ValidationError(
                f"{game} {draw['round']}회: 추첨일 {draw['date']}이 이전 회차({prev['date']})보다 늦지 않음"
            )
        prev = draw


def validate_lotto(existing, new):
    _check_sequence("lotto645", existing, new)
    for draw in new:
        tag = f"lotto645 {draw['round']}회"
        numbers = draw["numbers"]
        if not (
            isinstance(numbers, list)
            and len(numbers) == 6
            and all(_is_int(n, 1, 45) for n in numbers)
            and len(set(numbers)) == 6
            and numbers == sorted(numbers)
        ):
            raise ValidationError(f"{tag}: 당첨번호 이상 {numbers!r}")
        if not _is_int(draw["bonus"], 1, 45) or draw["bonus"] in numbers:
            raise ValidationError(f"{tag}: 보너스 번호 이상 {draw['bonus']!r}")
        if not _is_int(draw["sales"], 1):
            raise ValidationError(f"{tag}: 판매액 이상 {draw['sales']!r}")
        if [r["rank"] for r in draw["ranks"]] != LOTTO_RANKS:
            raise ValidationError(f"{tag}: 등수 구성 이상")
        for r in draw["ranks"]:
            if not (_is_int(r["winners"]) and _is_int(r["prize"])):
                raise ValidationError(f"{tag}: {r['rank']}등 당첨자 수·당첨금 이상 {r!r}")


def validate_pension(existing, new):
    _check_sequence("pension720", existing, new)
    for draw in new:
        tag = f"pension720 {draw['round']}회"
        if not _is_int(draw["group"], 1, 5):
            raise ValidationError(f"{tag}: 조 이상 {draw['group']!r}")
        for key in ("first", "bonus"):
            if not _is_six_digits(draw[key]):
                raise ValidationError(f"{tag}: {key} 번호 이상 {draw[key]!r}")
        if [r["rank"] for r in draw["ranks"]] != PENSION_RANKS:
            raise ValidationError(f"{tag}: 등수 구성 이상")
        for r in draw["ranks"]:
            if r["prize"] != PENSION_PRIZES[r["rank"]]:
                raise ValidationError(
                    f"{tag}: {r['rank']}등 당첨금 {r['prize']!r} — 고정 당첨금과 다름 (제도 변경 확인 필요)"
                )
            counts = (r["store"], r["online"], r["total"])
            if not all(_is_int(c) for c in counts) or r["store"] + r["online"] != r["total"]:
                raise ValidationError(f"{tag}: {r['rank']}등 당첨 매수 이상 {r!r}")


def check_unchanged(game, existing, refetched):
    stored = {draw["round"]: draw for draw in existing}
    for draw in refetched:
        old = stored.get(draw["round"])
        if old is not None and old != draw:
            raise ValidationError(
                f"{game} {draw['round']}회: 저장된 값과 다시 받은 값이 다름 (과거 데이터 변경)"
            )
