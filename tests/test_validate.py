import pytest

from lucky.errors import ValidationError
from lucky.sources import lotto645, pension720
from lucky.validate import check_unchanged, validate_lotto, validate_pension
from tests.fakes import lotto_raw, pension_detail_rows, pension_list_raw


def lotto_records(first, last):
    return [lotto645.parse_row(lotto_raw(r)) for r in range(first, last + 1)]


def pension_records(first, last):
    records = []
    for r in range(first, last + 1):
        listed = pension720.parse_list({"data": {"result": [pension_list_raw(r)]}})[r]
        detail = pension720.parse_detail({"data": {"result": pension_detail_rows(r)}})[r]
        records.append(pension720.merge(listed, detail))
    return records


def test_lotto_valid_from_empty_and_continuing():
    validate_lotto([], lotto_records(1, 3))
    validate_lotto(lotto_records(1, 2), lotto_records(3, 4))


def test_lotto_empty_store_must_start_at_round_1():
    with pytest.raises(ValidationError, match="1회 기대, 2회 받음"):
        validate_lotto([], lotto_records(2, 3))


def test_lotto_gap_is_rejected():
    with pytest.raises(ValidationError, match="3회 기대, 4회 받음"):
        validate_lotto(lotto_records(1, 2), lotto_records(4, 4))


def test_lotto_date_must_increase():
    new = lotto_records(3, 3)
    new[0]["date"] = lotto_records(2, 2)[0]["date"]
    with pytest.raises(ValidationError, match="추첨일"):
        validate_lotto(lotto_records(1, 2), new)


def test_lotto_calendar_invalid_date_is_rejected():
    new = lotto_records(1, 1)
    new[0]["date"] = "2024-02-30"
    with pytest.raises(ValidationError, match="추첨일 형식 이상"):
        validate_lotto([], new)


@pytest.mark.parametrize(
    "numbers",
    [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 46], [1, 1, 2, 3, 4, 5], [2, 1, 3, 4, 5, 6], [0, 2, 3, 4, 5, 6]],
)
def test_lotto_bad_numbers(numbers):
    new = lotto_records(1, 1)
    new[0]["numbers"] = numbers
    with pytest.raises(ValidationError, match="당첨번호 이상"):
        validate_lotto([], new)


def test_lotto_bonus_must_differ_from_numbers():
    new = lotto_records(1, 1)
    new[0]["bonus"] = new[0]["numbers"][0]
    with pytest.raises(ValidationError, match="보너스 번호 이상"):
        validate_lotto([], new)


def test_lotto_sales_and_rank_counts():
    new = lotto_records(1, 1)
    new[0]["sales"] = 0
    with pytest.raises(ValidationError, match="판매액 이상"):
        validate_lotto([], new)
    new = lotto_records(1, 1)
    new[0]["ranks"][2]["winners"] = -1
    with pytest.raises(ValidationError, match="3등 당첨자 수"):
        validate_lotto([], new)


def test_pension_valid():
    validate_pension([], pension_records(1, 3))
    validate_pension(pension_records(1, 3), pension_records(4, 5))


def test_pension_bad_group():
    new = pension_records(1, 1)
    new[0]["group"] = 6
    with pytest.raises(ValidationError, match="조 이상"):
        validate_pension([], new)


@pytest.mark.parametrize("value", ["12345", "12a456", "1234567"])
def test_pension_bad_first_number(value):
    new = pension_records(1, 1)
    new[0]["first"] = value
    with pytest.raises(ValidationError, match="first 번호 이상"):
        validate_pension([], new)


def test_pension_prize_change_detected():
    new = pension_records(1, 1)
    new[0]["ranks"][0]["prize"] = 1
    with pytest.raises(ValidationError, match="고정 당첨금과 다름"):
        validate_pension([], new)


def test_pension_ticket_counts_must_add_up():
    new = pension_records(1, 1)
    new[0]["ranks"][1]["total"] += 1
    with pytest.raises(ValidationError, match="2등 당첨 매수 이상"):
        validate_pension([], new)


def test_pension_rank_structure():
    new = pension_records(1, 1)
    new[0]["ranks"] = new[0]["ranks"][:-1]
    with pytest.raises(ValidationError, match="등수 구성 이상"):
        validate_pension([], new)


def test_check_unchanged():
    stored = lotto_records(1, 3)
    check_unchanged("lotto645", stored, lotto_records(1, 5))
    changed = lotto_records(1, 3)
    changed[1]["bonus"] = 45 if changed[1]["bonus"] != 45 else 44
    with pytest.raises(ValidationError, match="2회: 저장된 값과 다시 받은 값이 다름"):
        check_unchanged("lotto645", stored, changed)
