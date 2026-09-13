"""테스트용 가짜 동행복권 API — 2026-09-13 조사한 실제 엔드포인트 동작을 흉내 낸다."""

from datetime import date, timedelta

from lucky.errors import NetworkError


def _ymd(start, round_no):
    return (start + timedelta(days=7 * (round_no - 1))).strftime("%Y%m%d")


def _payload(key, rows):
    return {"resultCode": None, "resultMessage": None, "data": {key: rows}}


def lotto_raw(round_no):
    """검증을 통과하는 로또 원본 행. 번호는 일부러 정렬되지 않은 순서."""
    numbers = [(round_no + 7 * k) % 45 + 1 for k in range(6)]
    raw = {
        "winType0": 0,
        "gmSqNo": 5133,
        "ltEpsd": round_no,
        "bnsWnNo": (round_no + 42) % 45 + 1,
        "ltRflYmd": _ymd(date(2002, 12, 7), round_no),
        "rlvtEpsdSumNtslAmt": 1_000_000 * round_no,
        "excelRnk": "1등",
    }
    for i, n in enumerate(numbers, 1):
        raw[f"tm{i}WnNo"] = n
    for i in range(1, 6):
        raw[f"rnk{i}WnNope"] = i * 10
        raw[f"rnk{i}WnAmt"] = 10 ** (10 - i)
        raw[f"rnk{i}SumWnAmt"] = 0
    return raw


class FakeLottoApi:
    PATH = "/lt645/selectPstLt645InfoNew.do"

    def __init__(self, latest, fail_on_call=None):
        self.latest = latest
        self.fail_on_call = fail_on_call
        self.calls = []
        self.overrides = {}

    def __call__(self, path, params, referer):
        assert path == self.PATH and referer == "/lt645/result"
        self.calls.append(dict(params))
        if self.fail_on_call == len(self.calls):
            raise NetworkError("fake timeout")
        if params["srchDir"] == "center":
            lo = max(1, params["srchLtEpsd"] - 5)
            hi = min(self.latest, lo + 9)
        elif params["srchDir"] == "latest":
            cursor = params["srchCursorLtEpsd"]
            if cursor == 0:
                return _payload("list", [])
            lo, hi = cursor + 1, min(self.latest, cursor + 10)
        else:
            raise AssertionError(f"unexpected params {params}")
        rows = [self.overrides.get(r) or lotto_raw(r) for r in range(hi, lo - 1, -1)]
        return _payload("list", rows)


PENSION_PRIZES_RAW = {1: 1680000000, 2: 120000000, 3: 1000000, 4: 100000, 5: 50000, 6: 5000, 7: 1000, 21: 120000000}


def pension_list_raw(round_no):
    return {
        "psltEpsd": round_no,
        "psltRflYmd": _ymd(date(2020, 5, 7), round_no),
        "wnBndNo": str(round_no % 5 + 1),
        "wnRnkVl": f"{round_no * 123457 % 1_000_000:06d}",
        "bnsRnkVl": f"{round_no * 654321 % 1_000_000:06d}",
    }


def pension_detail_rows(round_no):
    base = pension_list_raw(round_no)
    rows = []
    for sq, amount in PENSION_PRIZES_RAW.items():
        if sq == 21:
            value = base["bnsRnkVl"]
        else:
            value = base["wnRnkVl"][max(sq - 2, 0):]  # 실제 응답처럼 등수가 낮을수록 끝자리만
        rows.append({
            "wnSqNo": sq,
            "wnAmt": amount,
            "wnBndNo": base["wnBndNo"] if sq == 1 else None,
            "wnRnkVl": value,
            "psltRflYmd": base["psltRflYmd"],
            "psltEpsd": round_no,
            "wnStoreCnt": sq,
            "wnInternetCnt": 2 * sq,
            "wnTotalCnt": 3 * sq,
        })
    return rows


class FakePensionApi:
    LIST_PATH = "/pt720/selectPstPt720WnList.do"
    DETAIL_PATH = "/pt720/selectPstPt720Info.do"

    def __init__(self, latest, fail_on_call=None):
        self.latest = latest
        self.fail_on_call = fail_on_call
        self.calls = []
        self.list_overrides = {}

    def __call__(self, path, params, referer):
        assert referer == "/pt720/result"
        self.calls.append((path, dict(params)))
        if self.fail_on_call == len(self.calls):
            raise NetworkError("fake timeout")
        if path == self.LIST_PATH:
            rows = [self.list_overrides.get(r) or pension_list_raw(r) for r in range(self.latest, 0, -1)]
        elif path == self.DETAIL_PATH:
            n = params["srchPsltEpsd"]
            hi, lo = min(self.latest, n + 5), max(1, n - 5)
            rows = [row for r in range(hi, lo - 1, -1) for row in pension_detail_rows(r)]
        else:
            raise AssertionError(f"unexpected path {path}")
        return _payload("result", rows)
