"""Step 3: one TMDB detail call per candidate film (credits, keywords, release dates, images).

Cached as data/raw/tmdb/<tmdb_id>.json; resumable (already-cached films are skipped).
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm

from pipeline.common import PROCESSED, TMDB_DIR, get_logger
from pipeline.tmdb import TMDB

log = get_logger("03_fetch_tmdb")
APPEND = "credits,keywords,release_dates,images"


def fetch_all(ids: list[int], workers: int = 24) -> int:
    tmdb = TMDB(rate=18)
    todo = [i for i in ids if not (TMDB_DIR / f"{i}.json").exists()]
    log.info("%d films, %d already cached, %d to fetch", len(ids), len(ids) - len(todo), len(todo))

    def one(tmdb_id: int):
        return tmdb.cached(
            TMDB_DIR / f"{tmdb_id}.json", f"/movie/{tmdb_id}",
            language="en-US", append_to_response=APPEND, include_image_language="en,null",
        )

    missing = 0
    with ThreadPoolExecutor(workers) as pool:
        futures = [pool.submit(one, i) for i in todo]
        for f in tqdm(as_completed(futures), total=len(futures), mininterval=10):
            if f.result() is None:
                missing += 1
    return missing


def main() -> None:
    cand = pd.read_csv(PROCESSED / "catalog_candidates.csv")
    missing = fetch_all(sorted(cand["tmdb_id"].unique().tolist()))
    log.info("done; %d films returned 404 in this run", missing)


if __name__ == "__main__":
    main()