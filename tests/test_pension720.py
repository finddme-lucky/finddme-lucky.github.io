import pytest

from lucky.errors import SourceError
from lucky.sources import pension720
from tests.fakes import FakePensionApi, pension_list_raw

LIST_1 = {"psltEpsd": 1, "psltRflYmd": "20200507", "wnBndNo": "4", "wnRnkVl": "162132", "bnsRnkVl": "278239"}
DETAIL_1 = [
    {"rnum": 2649, "wnSqNo": 1, "wnAmt": 1680000000, "wnBndNo": "4", "wnRnkVl": "162132", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 1, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 0, "wnInternetCnt": 1, "wnTotalCnt": 1},
    {"rnum": 2650, "wnSqNo": 2, "wnAmt": 120000000, "wnBndNo": None, "wnRnkVl": "162132", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 2, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 1, "wnInternetCnt": 4, "wnTotalCnt": 5},
    {"rnum": 2651, "wnSqNo": 3, "wnAmt": 1000000, "wnBndNo": None, "wnRnkVl": "62132", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 3, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 15, "wnInternetCnt": 42, "wnTotalCnt": 57},
    {"rnum": 2652, "wnSqNo": 4, "wnAmt": 100000, "wnBndNo": None, "wnRnkVl": "2132", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 4, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 151, "wnInternetCnt": 395, "wnTotalCnt": 546},
    {"rnum": 2653, "wnSqNo": 5, "wnAmt": 50000, "wnBndNo": None, "wnRnkVl": "132", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 5, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 1348, "wnInternetCnt": 3461, "wnTotalCnt": 4809},
    {"rnum": 2654, "wnSqNo": 6, "wnAmt": 5000, "wnBndNo": None, "wnRnkVl": "32", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 6, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 13650, "wnInternetCnt": 34740, "wnTotalCnt": 48390},
    {"rnum": 2655, "wnSqNo": 7, "wnAmt": 1000, "wnBndNo": None, "wnRnkVl": "2", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 7, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 136755, "wnInternetCnt": 351583, "wnTotalCnt": 488338},
    {"rnum": 2656, "wnSqNo": 21, "wnAmt": 120000000, "wnBndNo": None, "wnRnkVl": "278239", "psltRflYmd": "20200507", "psltEpsd": 1, "psltSn": 8, "ltGdsCd": "LP72", "swiperIndex": 0, "wnStoreCnt": 2, "wnInternetCnt": 5, "wnTotalCnt": 7},
]
EXPECTED_1 = {
    "round": 1,
    "date": "2020-05-07",
    "group": 4,
    "first": "162132",
    "bonus": "278239",
    "ranks": [
        {"rank": 1, "prize": 1680000000, "store": 0, "online": 1, "total": 1},
        {"rank": 2, "prize": 120000000, "store": 1, "online": 4, "total": 5},
        {"rank": 3, "prize": 1000000, "store": 15, "online": 42, "total": 57},
        {"rank": 4, "prize": 100000, "store": 151, "online": 395, "total": 546},
        {"rank": 5, "prize": 50000, "store": 1348, "online": 3461, "total": 4809},
        {"rank": 6, "prize": 5000, "store": 13650, "online": 34740, "total": 48390},
        {"rank": 7, "prize": 1000, "store": 136755, "online": 351583, "total": 488338},
        {"rank": "bonus", "prize": 120000000, "store": 2, "online": 5, "total": 7},
    ],
}


def payload(rows):
    return {"data": {"result": rows}}


def test_parse_list_real_round_1_and_keeps_leading_zero():
    row_zero = dict(LIST_1, psltEpsd=2, psltRflYmd="20200514", wnRnkVl="011391", bnsRnkVl="060727")
    listing = pension720.parse_list(payload([row_zero, LIST_1]))
    assert listing[1] == {"round": 1, "date": "2020-05-07", "group": 4, "first": "162132", "bonus": "278239"}
    assert listing[2]["first"] == "011391"
    assert listing[2]["bonus"] == "060727"


def test_parse_list_bad_shape_is_source_error():
    for bad in ({}, payload("x"), payload([dict(LIST_1, wnBndNo="조")])):
        with pytest.raises(SourceError):
            pension720.parse_list(bad)


def test_parse_detail_real_round_1_and_merge():
    detail = pension720.parse_detail(payload(list(reversed(DETAIL_1))))
    assert pension720.merge(pension720.parse_list(payload([LIST_1]))[1], detail[1]) == EXPECTED_1


def test_parse_detail_missing_rank_is_source_error():
    with pytest.raises(SourceError, match="등수 행 누락"):
        pension720.parse_detail(payload(DETAIL_1[:-1]))


def test_parse_detail_unknown_rank_code_is_source_error():
    with pytest.raises(SourceError, match="알 수 없는 등수 코드"):
        pension720.parse_detail(payload(DETAIL_1 + [dict(DETAIL_1[0], wnSqNo=99)]))


def test_merge_mismatch_is_source_error():
    listed = pension720.parse_list(payload([dict(LIST_1, wnRnkVl="999999")]))[1]
    detail = pension720.parse_detail(payload(DETAIL_1))[1]
    with pytest.raises(SourceError, match="목록과 상세의 first 불일치"):
        pension720.merge(listed, detail)


def rounds(pages):
    return [[d["round"] for d in page] for page in pages]


def test_fetch_after_backfill_uses_11_round_windows():
    api = FakePensionApi(latest=30)
    pages = list(pension720.fetch_after(api, 0))
    assert rounds(pages) == [list(range(1, 12)), list(range(12, 23)), list(range(23, 31))]
    assert api.calls == [
        (FakePensionApi.LIST_PATH, {}),
        (FakePensionApi.DETAIL_PATH, {"srchPsltEpsd": 6}),
        (FakePensionApi.DETAIL_PATH, {"srchPsltEpsd": 17}),
        (FakePensionApi.DETAIL_PATH, {"srchPsltEpsd": 28}),
    ]
    assert pages[0][0]["first"] == pension_list_raw(1)["wnRnkVl"]


def test_fetch_after_incremental_window_past_latest():
    api = FakePensionApi(latest=30)
    assert rounds(pension720.fetch_after(api, 28)) == [[29, 30]]
    assert api.calls[1] == (FakePensionApi.DETAIL_PATH, {"srchPsltEpsd": 34})


def test_fetch_after_nothing_new_calls_list_only():
    api = FakePensionApi(latest=30)
    assert list(pension720.fetch_after(api, 30)) == []
    assert api.calls == [(FakePensionApi.LIST_PATH, {})]


def test_fetch_after_list_detail_mismatch_is_source_error():
    api = FakePensionApi(latest=5)
    api.list_overrides[3] = dict(pension_list_raw(3), wnBndNo="5" if pension_list_raw(3)["wnBndNo"] != "5" else "1")
    with pytest.raises(SourceError, match="3회: 목록과 상세의 group 불일치"):
        list(pension720.fetch_after(api, 0))
