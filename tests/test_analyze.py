import json
from datetime import datetime

import pytest

from lucky import store
from lucky.__main__ import main
from lucky.analyze import DISCLAIMER, analyze, build_report, format_fairness
from lucky.sources import lotto645, pension720
from tests.fakes import lotto_raw, pension_detail_rows, pension_list_raw

NOW = datetime(2026, 9, 24, 15, 0, tzinfo=store.KST)


def lotto_draws(count):
    return [lotto645.parse_row(lotto_raw(round_no)) for round_no in range(1, count + 1)]


def pension_draws(count):
    draws = []
    for round_no in range(1, count + 1):
        listed = pension720.parse_list({"data": {"result": [pension_list_raw(round_no)]}})[round_no]
        detail = pension720.parse_detail({"data": {"result": pension_detail_rows(round_no)}})[round_no]
        draws.append(pension720.merge(listed, detail))
    return draws


def seed_data(tmp_path, lotto=40, pension=30):
    store.save_draws(tmp_path, "lotto645", lotto_draws(lotto))
    store.save_draws(tmp_path, "pension720", pension_draws(pension))


def test_build_report_has_the_documented_shape():
    report = build_report("lotto645", lotto_draws(40), NOW)
    assert report["schema"] == 1
    assert report["game"] == "lotto645"
    assert report["generatedAt"] == "2026-09-24T15:00:00+09:00"
    assert report["latestRound"] == 40
    assert report["latestDate"] == lotto_draws(40)[-1]["date"]
    assert report["disclaimer"] == DISCLAIMER
    assert set(report["stats"]) >= {"counts", "gaps", "sums", "series"}
    assert set(report["fairness"]) == {"alpha", "recentWindow", "all", "recent"}


def test_analyze_writes_the_report_under_stats(tmp_path):
    seed_data(tmp_path)
    report = analyze("pension720", tmp_path, now=NOW, log=lambda _message: None)

    path = tmp_path / "stats" / "pension720.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["game"] == "pension720"
    assert saved["latestRound"] == 30
    # JSON에서는 정수 키가 문자열이 된다 — 3단계 웹이 이 형태를 읽는다
    assert saved["stats"]["groups"]["1"] == report["stats"]["groups"][1]
    assert list(tmp_path.glob("stats/.*.tmp")) == []


def test_analyze_refuses_when_nothing_was_collected(tmp_path):
    with pytest.raises(ValueError, match="수집된 회차가 없다"):
        analyze("lotto645", tmp_path, now=NOW, log=lambda _message: None)


def test_format_fairness_reports_a_verdict_per_test():
    report = build_report("lotto645", lotto_draws(40), NOW)
    text = format_fairness(report)
    assert "[전체]" in text and "[최근" in text
    assert "편향 증거" in text or "생략" in text


def test_cli_analyze_writes_both_games(tmp_path, capsys):
    seed_data(tmp_path)
    code = main(["analyze", "--data-dir", str(tmp_path)], now=NOW)

    assert code == 0
    out = capsys.readouterr().out
    assert "lotto645: 40회 분석" in out
    assert "pension720: 30회 분석" in out
    assert (tmp_path / "stats" / "lotto645.json").exists()
    assert (tmp_path / "stats" / "pension720.json").exists()


def test_cli_analyze_fails_per_game_without_data(tmp_path, capsys):
    store.save_draws(tmp_path, "pension720", pension_draws(30))
    code = main(["analyze", "--data-dir", str(tmp_path)], now=NOW)

    assert code == 1
    captured = capsys.readouterr()
    assert "lotto645: 실패" in captured.err
    assert "pension720: 30회 분석" in captured.out
    assert not (tmp_path / "stats" / "lotto645.json").exists()


def test_cli_fairness_prints_without_writing(tmp_path, capsys):
    seed_data(tmp_path)
    code = main(["fairness", "--game", "lotto645", "--data-dir", str(tmp_path)], now=NOW)

    assert code == 0
    assert "lotto645" in capsys.readouterr().out
    assert not (tmp_path / "stats").exists()
