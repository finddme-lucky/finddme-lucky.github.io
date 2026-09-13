"""로또 6/45 — /lt645/selectPstLt645InfoNew.do (요청당 최대 10회차, 회차 내림차순 응답)."""

from lucky.errors import SourceError
from lucky.sources.common import ymd_to_iso

PATH = "/lt645/selectPstLt645InfoNew.do"
REFERER = "/lt645/result"


def parse_row(raw):
    try:
        return {
            "round": raw["ltEpsd"],
            "date": ymd_to_iso(raw["ltRflYmd"]),
            "numbers": sorted(raw[f"tm{i}WnNo"] for i in range(1, 7)),
            "bonus": raw["bnsWnNo"],
            "sales": raw["rlvtEpsdSumNtslAmt"],
            "ranks": [
                {"rank": i, "winners": raw[f"rnk{i}WnNope"], "prize": raw[f"rnk{i}WnAmt"]}
                for i in range(1, 6)
            ],
        }
    except (KeyError, TypeError) as e:
        raise SourceError(f"로또 응답 형식 변경: {e!r}") from e


def parse_page(payload):
    try:
        rows = payload["data"]["list"]
    except (KeyError, TypeError) as e:
        raise SourceError(f"로또 응답 형식 변경: {e!r}") from e
    if not isinstance(rows, list):
        raise SourceError("로또 응답 형식 변경: list가 목록이 아님")
    return sorted((parse_row(r) for r in rows), key=lambda d: d["round"])


def fetch_after(get, after):
    """after회 다음 회차부터 끝까지 페이지 단위(오름차순)로 내보낸다.

    커서 0은 빈 목록을 돌려주므로 처음 수집은 center 1(1~10회)로 시작한다.
    """
    if after == 0:
        params = {"srchDir": "center", "srchLtEpsd": 1}
    else:
        params = {"srchDir": "latest", "srchCursorLtEpsd": after}
    while True:
        page = [d for d in parse_page(get(PATH, params, REFERER)) if d["round"] > after]
        if not page:
            return
        yield page
        after = page[-1]["round"]
        params = {"srchDir": "latest", "srchCursorLtEpsd": after}
