"""원천 모듈 공용 변환."""

from lucky.errors import SourceError


def ymd_to_iso(ymd):
    if not (isinstance(ymd, str) and len(ymd) == 8 and ymd.isdigit()):
        raise SourceError(f"추첨일 형식 변경: {ymd!r}")
    return f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
