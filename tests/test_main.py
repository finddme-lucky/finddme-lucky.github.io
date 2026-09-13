import json
from datetime import datetime, timedelta, timezone

from lucky.__main__ import main
from tests.fakes import FakeLottoApi, FakePensionApi

NOW = datetime(2026, 9, 13, 22, 0, tzinfo=timezone(timedelta(hours=9)))


def dispatch(lotto, pension):
    def get(path, params, referer):
        api = lotto if path.startswith("/lt645/") else pension
        return api(path, params, referer)

    return get


def read_meta(data_dir):
    return json.loads((data_dir / "meta.json").read_text(encoding="utf-8"))


def test_collect_all_games(tmp_path, capsys):
    get = dispatch(FakeLottoApi(latest=12), FakePensionApi(latest=13))
    code = main(["collect", "--data-dir", str(tmp_path)], get=get, now=NOW)

    assert code == 0
    out = capsys.readouterr().out
    assert "lotto645: 신규 12회" in out
    assert "pension720: 신규 13회" in out
    meta = read_meta(tmp_path)
    assert meta["games"]["lotto645"]["latestRound"] == 12
    assert meta["games"]["pension720"]["latestRound"] == 13
    assert meta["updatedAt"] == "2026-09-13T22:00:00+09:00"


def test_one_game_failure_still_collects_other_and_exits_1(tmp_path, capsys):
    get = dispatch(FakeLottoApi(latest=12, fail_on_call=1), FakePensionApi(latest=13))
    code = main(["collect", "--data-dir", str(tmp_path)], get=get, now=NOW)

    assert code == 1
    captured = capsys.readouterr()
    assert "lotto645: 실패" in captured.err
    assert "pension720: 신규 13회" in captured.out
    assert list(read_meta(tmp_path)["games"]) == ["pension720"]


def test_single_game_option(tmp_path):
    lotto, pension = FakeLottoApi(latest=12), FakePensionApi(latest=13)
    code = main(["collect", "--game", "pension720", "--data-dir", str(tmp_path)], get=dispatch(lotto, pension), now=NOW)

    assert code == 0
    assert lotto.calls == []
    assert not (tmp_path / "lotto645.json").exists()


def test_corrupt_data_file_fails_that_game_only(tmp_path, capsys):
    (tmp_path / "lotto645.json").write_text(
        '{"schema": 1, "game": "pension720", "draws": []}\n', encoding="utf-8"
    )
    get = dispatch(FakeLottoApi(latest=12), FakePensionApi(latest=13))
    code = main(["collect", "--data-dir", str(tmp_path)], get=get, now=NOW)

    assert code == 1
    captured = capsys.readouterr()
    assert "lotto645: 실패" in captured.err
    assert "pension720: 신규 13회" in captured.out
    assert "meta.json 갱신 실패" in captured.err
    assert not (tmp_path / "meta.json").exists()
