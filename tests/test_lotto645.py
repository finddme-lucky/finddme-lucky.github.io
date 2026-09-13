import pytest

from lucky.errors import SourceError
from lucky.sources import lotto645
from lucky.sources.common import ymd_to_iso
from tests.fakes import FakeLottoApi, lotto_raw

RAW_1 = {"winType0": 0, "winType1": 0, "winType2": 0, "winType3": 0, "gmSqNo": 5133, "ltEpsd": 1, "tm1WnNo": 10, "tm2WnNo": 23, "tm3WnNo": 29, "tm4WnNo": 33, "tm5WnNo": 37, "tm6WnNo": 40, "bnsWnNo": 16, "ltRflYmd": "20021207", "rnk1WnNope": 0, "rnk1WnAmt": 0, "rnk1SumWnAmt": 863604600, "rnk2WnNope": 1, "rnk2WnAmt": 143934100, "rnk2SumWnAmt": 0, "rnk3WnNope": 28, "rnk3WnAmt": 5140500, "rnk3SumWnAmt": 0, "rnk4WnNope": 2537, "rnk4WnAmt": 113400, "rnk4SumWnAmt": 0, "rnk5WnNope": 40155, "rnk5WnAmt": 10000, "rnk5SumWnAmt": 0, "sumWnNope": 42721, "rlvtEpsdSumNtslAmt": 3681782000, "wholEpsdSumNtslAmt": 3681782000, "excelRnk": "1등"}
RAW_9 = {"winType0": 0, "winType1": 0, "winType2": 0, "winType3": 0, "gmSqNo": 5133, "ltEpsd": 9, "tm1WnNo": 2, "tm2WnNo": 4, "tm3WnNo": 16, "tm4WnNo": 17, "tm5WnNo": 36, "tm6WnNo": 39, "bnsWnNo": 14, "ltRflYmd": "20030201", "rnk1WnNope": 0, "rnk1WnAmt": 0, "rnk1SumWnAmt": 25803852000, "rnk2WnNope": 4, "rnk2WnAmt": 769456500, "rnk2SumWnAmt": 0, "rnk3WnNope": 352, "rnk3WnAmt": 8743800, "rnk3SumWnAmt": 0, "rnk4WnNope": 23672, "rnk4WnAmt": 260000, "rnk4SumWnAmt": 0, "rnk5WnNope": 603375, "rnk5WnAmt": 10000, "rnk5SumWnAmt": 0, "sumWnNope": 627403, "rlvtEpsdSumNtslAmt": 73624020000, "wholEpsdSumNtslAmt": 73624020000, "excelRnk": "1등"}


def test_ymd_to_iso():
    assert ymd_to_iso("20021207") == "2002-12-07"
    for bad in ("2002-12-07", "2002127", 20021207, None):
        with pytest.raises(SourceError, match="추첨일 형식"):
            ymd_to_iso(bad)


def test_parse_row_real_round_1():
    assert lotto645.parse_row(RAW_1) == {
        "round": 1,
        "date": "2002-12-07",
        "numbers": [10, 23, 29, 33, 37, 40],
        "bonus": 16,
        "sales": 3681782000,
        "ranks": [
            {"rank": 1, "winners": 0, "prize": 0},
            {"rank": 2, "winners": 1, "prize": 143934100},
            {"rank": 3, "winners": 28, "prize": 5140500},
            {"rank": 4, "winners": 2537, "prize": 113400},
            {"rank": 5, "winners": 40155, "prize": 10000},
        ],
    }


def test_parse_row_real_round_9_no_first_prize_winner():
    row = lotto645.parse_row(RAW_9)
    assert row["numbers"] == [2, 4, 16, 17, 36, 39]
    assert row["ranks"][0] == {"rank": 1, "winners": 0, "prize": 0}
    assert row["sales"] == 73624020000


def test_parse_row_sorts_numbers():
    assert lotto645.parse_row(lotto_raw(3))["numbers"] == sorted(
        lotto_raw(3)[f"tm{i}WnNo"] for i in range(1, 7)
    )


def test_parse_row_missing_field_is_source_error():
    raw = dict(RAW_1)
    del raw["bnsWnNo"]
    with pytest.raises(SourceError, match="로또 응답 형식"):
        lotto645.parse_row(raw)


def test_parse_page_sorts_ascending_and_checks_shape():
    page = lotto645.parse_page({"data": {"list": [RAW_9, RAW_1]}})
    assert [d["round"] for d in page] == [1, 9]
    for bad in ({}, {"data": {}}, {"data": {"list": "x"}}):
        with pytest.raises(SourceError):
            lotto645.parse_page(bad)


def rounds(pages):
    return [[d["round"] for d in page] for page in pages]


def test_fetch_after_backfill_from_empty():
    api = FakeLottoApi(latest=25)
    pages = list(lotto645.fetch_after(api, 0))
    assert rounds(pages) == [list(range(1, 11)), list(range(11, 21)), list(range(21, 26))]
    assert api.calls == [
        {"srchDir": "center", "srchLtEpsd": 1},
        {"srchDir": "latest", "srchCursorLtEpsd": 10},
        {"srchDir": "latest", "srchCursorLtEpsd": 20},
        {"srchDir": "latest", "srchCursorLtEpsd": 25},
    ]


def test_fetch_after_incremental():
    api = FakeLottoApi(latest=27)
    assert rounds(lotto645.fetch_after(api, 25)) == [[26, 27]]
    assert api.calls[0] == {"srchDir": "latest", "srchCursorLtEpsd": 25}


def test_fetch_after_nothing_new():
    api = FakeLottoApi(latest=25)
    assert list(lotto645.fetch_after(api, 25)) == []
    assert len(api.calls) == 1


def test_fetch_after_short_history():
    api = FakeLottoApi(latest=5)
    assert rounds(lotto645.fetch_after(api, 0)) == [[1, 2, 3, 4, 5]]
