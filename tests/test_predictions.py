import json
from datetime import datetime, timedelta

import pytest

from lucky import predictions, rules as rules_module, store
from lucky.__main__ import main
from lucky.sources import lotto645
from tests.fakes import lotto_raw

NOW = datetime(2026, 9, 24, 21, 0, tzinfo=store.KST)
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


def test_build_predictions_targets_the_next_round(tmp_path):
    seed_data(tmp_path)
    document = predictions.build_predictions(tmp_path, now=NOW, rules=CONFIG, strategy="hot")

    assert document["schema"] == 1
    assert document["generatedAt"] == "2026-09-24T21:00:00+09:00"
    assert document["disclaimer"] == predictions.DISCLAIMER
    assert document["lotto645"]["round"] == 121
    assert document["pension720"]["round"] == 61
    assert document["pension720"]["purchase"] == "all-groups"
    assert [entry["strategy"] for entry in document["lotto645"]["sets"]] == ["hot"]
    assert len(document["lotto645"]["sets"][0]["games"]) == 5
    assert len(document["pension720"]["sets"][0]["number"]) == 6


def test_build_predictions_for_an_explicit_round_ignores_later_draws(tmp_path):
    seed_data(tmp_path)
    limited = predictions.build_predictions(
        tmp_path, now=NOW, rules=CONFIG, games=("lotto645",), strategy="hot", round_no=100
    )
    store.save_draws(
        tmp_path,
        "lotto645",
        [lotto645.parse_row(lotto_raw(round_no)) for round_no in range(1, 200)],
    )
    again = predictions.build_predictions(
        tmp_path, now=NOW, rules=CONFIG, games=("lotto645",), strategy="hot", round_no=100
    )
    assert limited["lotto645"] == again["lotto645"]


def test_build_predictions_rejects_an_unknown_strategy(tmp_path):
    seed_data(tmp_path)
    with pytest.raises(ValueError, match="알 수 없는 전략"):
        predictions.build_predictions(tmp_path, now=NOW, rules=CONFIG, strategy="psychic")


def test_build_predictions_needs_collected_draws(tmp_path):
    with pytest.raises(ValueError, match="수집된 회차가 없다"):
        predictions.build_predictions(tmp_path, now=NOW, rules=CONFIG, strategy="hot")


def test_save_predictions_skips_when_only_the_timestamp_changes(tmp_path):
    seed_data(tmp_path)
    document = predictions.build_predictions(tmp_path, now=NOW, rules=CONFIG, strategy="hot")
    assert predictions.save_predictions(tmp_path, document) is True

    later = predictions.build_predictions(
        tmp_path, now=NOW + timedelta(hours=5), rules=CONFIG, strategy="hot"
    )
    assert predictions.save_predictions(tmp_path, later) is False


def test_cli_sets_writes_predictions(tmp_path, capsys):
    seed_data(tmp_path)
    code = main(["sets", "--data-dir", str(tmp_path), "--strategy", "hot"], now=NOW)

    assert code == 0
    out = capsys.readouterr().out
    assert "lotto645 121회" in out
    assert "1~5조 전부" in out
    saved = json.loads((tmp_path / "predictions.json").read_text(encoding="utf-8"))
    assert saved["lotto645"]["round"] == 121


def test_cli_sets_with_an_explicit_round_does_not_write(tmp_path, capsys):
    seed_data(tmp_path)
    code = main(
        ["sets", "--game", "lotto645", "--data-dir", str(tmp_path), "--round", "100", "--strategy", "cold"],
        now=NOW,
    )

    assert code == 0
    assert "lotto645 100회" in capsys.readouterr().out
    assert not (tmp_path / "predictions.json").exists()


def test_cli_sets_reports_failure(tmp_path, capsys):
    code = main(["sets", "--data-dir", str(tmp_path), "--strategy", "hot"], now=NOW)

    assert code == 1
    assert "sets: 실패" in capsys.readouterr().err


def test_save_predictions_keeps_the_other_games_section(tmp_path):
    seed_data(tmp_path)
    full = predictions.build_predictions(tmp_path, now=NOW, rules=CONFIG, strategy="hot")
    predictions.save_predictions(tmp_path, full)

    only_lotto = predictions.build_predictions(
        tmp_path, now=NOW, rules=CONFIG, games=("lotto645",), strategy="cold"
    )
    predictions.save_predictions(tmp_path, only_lotto)

    saved = json.loads((tmp_path / "predictions.json").read_text(encoding="utf-8"))
    assert saved["lotto645"]["sets"][0]["strategy"] == "cold"
    assert saved["pension720"]["sets"][0]["strategy"] == "hot"
