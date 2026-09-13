"""data/*.json 읽기·쓰기. 쓰기는 임시 파일 → os.replace로 원자적으로 교체한다."""

import json
import os
import tempfile

SCHEMA = 1
GAMES = ("lotto645", "pension720")


def _path(data_dir, game):
    return data_dir / f"{game}.json"


def load_draws(data_dir, game):
    path = _path(data_dir, game)
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
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
