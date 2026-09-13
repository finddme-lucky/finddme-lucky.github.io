import json
import os
import stat
from datetime import datetime, timedelta, timezone

import pytest

from lucky import store
from lucky.sources import lotto645
from tests.fakes import lotto_raw

KST = timezone(timedelta(hours=9))


def lotto_records(first, last):
    return [lotto645.parse_row(lotto_raw(r)) for r in range(first, last + 1)]


def test_load_missing_file_is_empty(tmp_path):
    assert store.load_draws(tmp_path, "lotto645") == []


def test_save_and_load_roundtrip_one_draw_per_line(tmp_path):
    draws = lotto_records(1, 3)
    store.save_draws(tmp_path, "lotto645", draws)

    assert store.load_draws(tmp_path, "lotto645") == draws
    path = tmp_path / "lotto645.json"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == '{"schema": 1, "game": "lotto645", "draws": ['
    assert len(lines) == 5
    assert lines[-1] == "]}"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644


def test_save_empty_draws_is_valid_json(tmp_path):
    store.save_draws(tmp_path, "pension720", [])
    assert json.loads((tmp_path / "pension720.json").read_text(encoding="utf-8"))["draws"] == []


def test_load_rejects_wrong_game(tmp_path):
    store.save_draws(tmp_path, "lotto645", lotto_records(1, 1))
    (tmp_path / "pension720.json").write_text(
        (tmp_path / "lotto645.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="schema/game 불일치"):
        store.load_draws(tmp_path, "pension720")


def test_failed_write_keeps_old_file_and_no_temp(tmp_path, monkeypatch):
    store.save_draws(tmp_path, "lotto645", lotto_records(1, 2))
    before = (tmp_path / "lotto645.json").read_text(encoding="utf-8")

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(store.os, "replace", boom)
    with pytest.raises(OSError, match="disk full"):
        store.save_draws(tmp_path, "lotto645", lotto_records(1, 3))

    assert (tmp_path / "lotto645.json").read_text(encoding="utf-8") == before
    assert list(tmp_path.glob(".*.tmp")) == []


def test_save_meta_only_when_latest_changes(tmp_path):
    now = datetime(2026, 9, 13, 21, 0, tzinfo=KST)
    assert store.save_meta(tmp_path, now) is False
    assert not (tmp_path / "meta.json").exists()

    store.save_draws(tmp_path, "lotto645", lotto_records(1, 3))
    assert store.save_meta(tmp_path, now) is True
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert meta == {
        "schema": 1,
        "updatedAt": "2026-09-13T21:00:00+09:00",
        "games": {"lotto645": {"latestRound": 3, "latestDate": lotto_records(3, 3)[0]["date"]}},
    }

    assert store.save_meta(tmp_path, now + timedelta(hours=1)) is False

    store.save_draws(tmp_path, "lotto645", lotto_records(1, 4))
    assert store.save_meta(tmp_path, now + timedelta(hours=2)) is True
    meta = json.loads((tmp_path / "meta.json").read_text(encoding="utf-8"))
    assert meta["games"]["lotto645"]["latestRound"] == 4
    assert meta["updatedAt"] == "2026-09-13T23:00:00+09:00"
