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
