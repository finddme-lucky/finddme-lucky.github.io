"""연금복권720+ — 목록(전 회차 1요청) + 상세(요청 회차 N의 N-5 ~ N+5회, 등수별 8행)."""

from lucky.errors import SourceError
from lucky.sources.common import ymd_to_iso

LIST_PATH = "/pt720/selectPstPt720WnList.do"
DETAIL_PATH = "/pt720/selectPstPt720Info.do"
REFERER = "/pt720/result"
WINDOW_HALF = 5
RANKS = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 21: "bonus"}


def _rows(payload):
    try:
        rows = payload["data"]["result"]
    except (KeyError, TypeError) as e:
        raise SourceError(f"연금복권 응답 형식 변경: {e!r}") from e
    if not isinstance(rows, list):
        raise SourceError("연금복권 응답 형식 변경: result가 목록이 아님")
    return rows


def parse_list(payload):
    listing = {}
    try:
        for row in _rows(payload):
            listing[row["psltEpsd"]] = {
                "round": row["psltEpsd"],
                "date": ymd_to_iso(row["psltRflYmd"]),
                "group": int(row["wnBndNo"]),
                "first": row["wnRnkVl"],
                "bonus": row["bnsRnkVl"],
            }
    except (KeyError, TypeError, ValueError) as e:
        raise SourceError(f"연금복권 목록 형식 변경: {e!r}") from e
    return listing


def parse_detail(payload):
    by_round = {}
    try:
        for row in _rows(payload):
            code = row["wnSqNo"]
            if code not in RANKS:
                raise SourceError(f"연금복권 상세: 알 수 없는 등수 코드 {code}")
            entry = by_round.setdefault(row["psltEpsd"], {"ranks": {}})
            rank = RANKS[code]
            entry["ranks"][rank] = {
                "rank": rank,
                "prize": row["wnAmt"],
                "store": row["wnStoreCnt"],
                "online": row["wnInternetCnt"],
                "total": row["wnTotalCnt"],
            }
            if code == 1:
                entry["date"] = ymd_to_iso(row["psltRflYmd"])
                entry["group"] = int(row["wnBndNo"])
                entry["first"] = row["wnRnkVl"]
            elif code == 21:
                entry["bonus"] = row["wnRnkVl"]
    except (KeyError, TypeError, ValueError) as e:
        raise SourceError(f"연금복권 상세 형식 변경: {e!r}") from e

    details = {}
    for round_no, entry in by_round.items():
        if set(entry["ranks"]) != set(RANKS.values()):
            found = sorted(str(r) for r in entry["ranks"])
            raise SourceError(f"연금복권 상세 {round_no}회: 등수 행 누락 (받은 등수 {found})")
        details[round_no] = {
            "date": entry["date"],
            "group": entry["group"],
            "first": entry["first"],
            "bonus": entry["bonus"],
            "ranks": [entry["ranks"][rank] for rank in RANKS.values()],
        }
    return details


def merge(listed, detail):
    for key in ("date", "group", "first", "bonus"):
        if listed[key] != detail[key]:
            raise SourceError(
                f"연금복권 {listed['round']}회: 목록과 상세의 {key} 불일치 "
                f"({listed[key]!r} != {detail[key]!r})"
            )
    return {**listed, "ranks": detail["ranks"]}


def fetch_after(get, after):
    """after회 다음 회차부터 끝까지 페이지 단위(오름차순, 최대 11회)로 내보낸다."""
    listing = parse_list(get(LIST_PATH, {}, REFERER))
    new_rounds = sorted(r for r in listing if r > after)
    i = 0
    while i < len(new_rounds):
        start = new_rounds[i]
        details = parse_detail(get(DETAIL_PATH, {"srchPsltEpsd": start + WINDOW_HALF}, REFERER))
        page = []
        for round_no in new_rounds[i:]:
            if round_no not in details:
                break
            page.append(merge(listing[round_no], details[round_no]))
        if not page:
            raise SourceError(f"연금복권 상세 응답에 {start}회가 없음 (창 규칙 변경 의심)")
        yield page
        i += len(page)
