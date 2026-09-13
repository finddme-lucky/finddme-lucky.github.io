import pytest

from lucky import store
from lucky.collect import collect
from lucky.errors import NetworkError, ValidationError
from tests.fakes import FakeLottoApi, FakePensionApi, lotto_raw


def quiet(_message):
    pass


def saved_rounds(data_dir, game):
    return [d["round"] for d in store.load_draws(data_dir, game)]


def test_lotto_backfill_from_empty(tmp_path):
    api = FakeLottoApi(latest=25)
    assert collect("lotto645", tmp_path, api, log=quiet) == 25
    assert saved_rounds(tmp_path, "lotto645") == list(range(1, 26))
    assert len(api.calls) == 4


def test_lotto_incremental(tmp_path):
    collect("lotto645", tmp_path, FakeLottoApi(latest=25), log=quiet)
    api = FakeLottoApi(latest=27)
    assert collect("lotto645", tmp_path, api, log=quiet) == 2
    assert saved_rounds(tmp_path, "lotto645") == list(range(1, 28))
    assert api.calls[0] == {"srchDir": "latest", "srchCursorLtEpsd": 25}


def test_nothing_new_leaves_file_untouched(tmp_path):
    collect("lotto645", tmp_path, FakeLottoApi(latest=25), log=quiet)
    before = (tmp_path / "lotto645.json").read_text(encoding="utf-8")
    assert collect("lotto645", tmp_path, FakeLottoApi(latest=25), log=quiet) == 0
    assert (tmp_path / "lotto645.json").read_text(encoding="utf-8") == before


def test_network_failure_keeps_saved_pages_and_resumes(tmp_path):
    with pytest.raises(NetworkError):
        collect("lotto645", tmp_path, FakeLottoApi(latest=25, fail_on_call=2), log=quiet)
    assert saved_rounds(tmp_path, "lotto645") == list(range(1, 11))

    assert collect("lotto645", tmp_path, FakeLottoApi(latest=25), log=quiet) == 15
    assert saved_rounds(tmp_path, "lotto645") == list(range(1, 26))


def test_invalid_page_is_not_saved(tmp_path):
    api = FakeLottoApi(latest=25)
    broken = lotto_raw(12)
    broken["tm2WnNo"] = broken["tm1WnNo"]
    api.overrides[12] = broken
    with pytest.raises(ValidationError, match="12회: 당첨번호 이상"):
        collect("lotto645", tmp_path, api, log=quiet)
    assert saved_rounds(tmp_path, "lotto645") == list(range(1, 11))


def test_pension_backfill(tmp_path):
    assert collect("pension720", tmp_path, FakePensionApi(latest=30), log=quiet) == 30
    assert saved_rounds(tmp_path, "pension720") == list(range(1, 31))


def test_full_detects_changed_past_value(tmp_path):
    collect("lotto645", tmp_path, FakeLottoApi(latest=12), log=quiet)
    draws = store.load_draws(tmp_path, "lotto645")
    draws[4]["sales"] += 1
    store.save_draws(tmp_path, "lotto645", draws)

    with pytest.raises(ValidationError, match="5회: 저장된 값과 다시 받은 값이 다름"):
        collect("lotto645", tmp_path, FakeLottoApi(latest=14), full=True, log=quiet)
    assert saved_rounds(tmp_path, "lotto645") == list(range(1, 13))


def test_full_without_changes_saves_new_rounds(tmp_path):
    collect("lotto645", tmp_path, FakeLottoApi(latest=12), log=quiet)
    assert collect("lotto645", tmp_path, FakeLottoApi(latest=14), full=True, log=quiet) == 2
    assert saved_rounds(tmp_path, "lotto645") == list(range(1, 15))
