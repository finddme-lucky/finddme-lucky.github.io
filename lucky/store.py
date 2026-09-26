"""data/*.json 읽기·쓰기. 쓰기는 임시 파일 → os.replace로 원자적으로 교체한다."""

import json
import os
import tempfile
from datetime import timedelta, timezone

KST = timezone(timedelta(hours=9))

SCHEMA = 1
GAMES = ("lotto645", "pension720")
LATEST_DRAWS = 5


def _path(data_dir, game):
    return data_dir / f"{game}.json"


def load_draws(data_dir, game):
    path = _path(data_dir, game)
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("draws"), list):
        raise ValueError(f"{path}: draws 목록이 없음")
    if doc.get("schema") != SCHEMA or doc.get("game") != game:
        raise ValueError(f"{path}: schema/game 불일치 ({doc.get('schema')!r}, {doc.get('game')!r})")
    return doc["draws"]


def dumps_draws(game, draws):
    lines = ",\n".join(
        "  " + json.dumps(draw, ensure_ascii=False, separators=(",", ":")) for draw in draws
    )
    body = f"\n{lines}\n" if draws else ""
    return f'{{"schema": {SCHEMA}, "game": "{game}", "draws": [{body}]}}\n'


def _write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def save_draws(data_dir, game, draws):
    _write_atomic(_path(data_dir, game), dumps_draws(game, draws))


def save_meta(data_dir, now):
    games = {}
    for game in GAMES:
        draws = load_draws(data_dir, game)
        if draws:
            games[game] = {"latestRound": draws[-1]["round"], "latestDate": draws[-1]["date"]}
    if not games:
        return False
    path = data_dir / "meta.json"
    if path.exists() and json.loads(path.read_text(encoding="utf-8")).get("games") == games:
        return False
    doc = {"schema": SCHEMA, "updatedAt": now.isoformat(timespec="seconds"), "games": games}
    _write_atomic(path, json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    return True


def save_latest(data_dir, now):
    """앱 홈 화면용 요약 — 전체 회차 파일(수백 KB)을 폰이 받지 않도록 최근 회차만 담는다."""
    games = {}
    for game in GAMES:
        draws = load_draws(data_dir, game)
        if draws:
            games[game] = {
                "latestRound": draws[-1]["round"],
                "latestDate": draws[-1]["date"],
                "draws": draws[-LATEST_DRAWS:],
            }
    if not games:
        return False
    doc = {"schema": SCHEMA, "updatedAt": now.isoformat(timespec="seconds"), "games": games}
    return save_document_if_changed(data_dir, "latest.json", doc, ignore=("updatedAt",))


def save_document(data_dir, relative_path, doc):
    """data_dir 아래 상대 경로에 JSON 문서를 원자적으로 저장한다."""
    _write_atomic(data_dir / relative_path, json.dumps(doc, ensure_ascii=False, indent=1) + "\n")


def _comparable(document, ignore):
    normalized = json.loads(json.dumps(document, ensure_ascii=False))
    for key in ignore:
        normalized.pop(key, None)
    return normalized


def save_document_if_changed(data_dir, relative_path, doc, *, ignore=("generatedAt",)):
    """무시할 키를 뺀 내용이 파일과 같으면 쓰지 않는다. 썼으면 True."""
    path = data_dir / relative_path
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = None
        if previous is not None and _comparable(previous, ignore) == _comparable(doc, ignore):
            return False
    save_document(data_dir, relative_path, doc)
    return True
