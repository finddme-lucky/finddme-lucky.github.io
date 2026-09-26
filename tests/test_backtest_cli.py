import json
from datetime import datetime, timedelta

import pytest

from lucky import backtest, store
from lucky import rules as rules_module
from lucky.__main__ import main
from lucky.sources import lotto645
from tests.fakes import lotto_raw

NOW = datetime(2026, 9, 26, 21, 0, tzinfo=store.KST)
CONFIG = rules_module.load_rules()


def seed_data(tmp_path, lotto=120, pension=60):
    store.save_draws(
        tmp_path,
        "lotto645",
        [lotto645.parse_row(lotto_raw(round_no)) for round_no in range(1, lotto + 1)],
    )
    store.save_draws(
        tmp_path,
        "pension720",
        [
            {
                "round": round_no,
                "date": "2020-05-07",
                "group": round_no % 5 + 1,
                "first": f"{round_no * 123457 % 1_000_000:06d}",
                "bonus": f"{round_no * 654321 % 1_000_000:06d}",
                "ranks": [],
            }
            for round_no in range(1, pension + 1)
        ],
    )


def test_build_document_has_both_games_and_the_popularity_section(tmp_path):
    seed_data(tmp_path)
    document = backtest.build_document(
        tmp_path, now=NOW, rules=CONFIG, strategies=("hot", "random"), rounds=4
    )

    assert document["schema"] == 1
    assert document["generatedAt"] == "2026-09-26T21:00:00+09:00"
    assert document["disclaimer"] == backtest.DISCLAIMER
    assert document["lotto645"]["evalRounds"] == 4
    assert document["pension720"]["evalRounds"] == 4
    assert set(document["lotto645"]["strategies"]) == {"hot", "random"}
    assert document["popularity"]["rounds"] > 0
    assert document["popularity"]["caveat"]


def test_build_document_without_lotto_has_no_popularity_section(tmp_path):
    seed_data(tmp_path)
    document = backtest.build_document(
        tmp_path, now=NOW, rules=CONFIG, games=("pension720",), strategies=("hot",), rounds=4
    )
    assert "popularity" not in document
    assert "lotto645" not in document


def test_build_document_needs_collected_draws(tmp_path):
    with pytest.raises(ValueError, match="수집된 회차가 없다"):
        backtest.build_document(tmp_path, now=NOW, rules=CONFIG, strategies=("hot",), rounds=4)


def test_save_document_skips_when_only_the_timestamp_changes(tmp_path):
    seed_data(tmp_path)
    first = backtest.build_document(
        tmp_path, now=NOW, rules=CONFIG, strategies=("hot", "random"), rounds=4
    )
    assert backtest.save_document(tmp_path, first) is True

    later = backtest.build_document(
        tmp_path, now=NOW + timedelta(hours=2), rules=CONFIG, strategies=("hot", "random"), rounds=4
    )
    assert backtest.save_document(tmp_path, later) is False


def test_cli_backtest_writes_the_document(tmp_path, capsys, monkeypatch):
    seed_data(tmp_path)
    # 기본 평가 구간(로또 300회)을 그대로 쓰면 ml 재학습이 300번 돌아 테스트가 몇 분 걸린다
    monkeypatch.setattr(backtest, "LOTTO_EVAL_ROUNDS", 3)
    monkeypatch.setattr(backtest, "PENSION_EVAL_ROUNDS", 3)
    code = main(["backtest", "--data-dir", str(tmp_path)], now=NOW)

    assert code == 0
    out = capsys.readouterr().out
    assert "lotto645" in out and "pension720" in out
    saved = json.loads((tmp_path / "backtest.json").read_text(encoding="utf-8"))
    assert saved["lotto645"]["evalRounds"] > 0
    assert "backtest.json 저장" in out


def test_cli_backtest_with_filters_prints_without_writing(tmp_path, capsys):
    seed_data(tmp_path)
    code = main(
        ["backtest", "--game", "lotto645", "--data-dir", str(tmp_path), "--rounds", "3", "--strategy", "cold"],
        now=NOW,
    )

    assert code == 0
    assert "cold" in capsys.readouterr().out
    assert not (tmp_path / "backtest.json").exists()


def test_cli_backtest_reports_failure(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(backtest, "LOTTO_EVAL_ROUNDS", 3)
    monkeypatch.setattr(backtest, "PENSION_EVAL_ROUNDS", 3)
    code = main(["backtest", "--data-dir", str(tmp_path)], now=NOW)
    assert code == 1
    assert "backtest: 실패" in capsys.readouterr().err
