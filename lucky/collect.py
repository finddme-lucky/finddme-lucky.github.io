"""신규 회차 수집 → 검증 → 페이지마다 저장 (중간에 끊겨도 다음 실행이 이어받는다)."""

from lucky import store
from lucky.sources import lotto645, pension720
from lucky.validate import check_unchanged, validate_lotto, validate_pension

SOURCES = {
    "lotto645": (lotto645.fetch_after, validate_lotto),
    "pension720": (pension720.fetch_after, validate_pension),
}


def collect(game, data_dir, get, *, full=False, log=print):
    fetch_after, validate = SOURCES[game]
    draws = store.load_draws(data_dir, game)
    last = draws[-1]["round"] if draws else 0

    if full:
        refetched = [draw for page in fetch_after(get, 0) for draw in page]
        check_unchanged(game, draws, refetched)
        pages = [[draw for draw in refetched if draw["round"] > last]]
    else:
        pages = fetch_after(get, last)

    added = 0
    for page in pages:
        if not page:
            continue
        validate(draws, page)
        draws = draws + page
        store.save_draws(data_dir, game, draws)
        added += len(page)
        log(f"{game}: {page[0]['round']}~{page[-1]['round']}회 저장")
    return added
