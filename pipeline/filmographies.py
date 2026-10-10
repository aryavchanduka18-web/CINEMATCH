"""Filmography completion: the missing feature films of the catalog's leading stars and directors.

    python -m pipeline.filmographies [--dry]   (after step 5 has built a catalog; then rerun 5, 12, extend_serving)

A person qualifies when they are top-billed (cast order <= lead_max_order) in at least min_lead_films
catalog films, or directed at least min_director_films (catalog_config.yaml, filmography). Their TMDB
movie credits are fetched once (cached as data/raw/tmdb_people/<id>.json). A film they lead or direct
that is not in the catalog becomes a candidate when it is released by the build date, is not adult and
has at least min_vote_count TMDB votes (min_vote_count_en for English-language films); its detail is fetched like step 3 and it must run
min_runtime_min minutes. Candidates go to data/processed/filmography_candidates.csv. Step 5 adds the ones
that pass the (relaxed) metadata gate as part D with filmography_rule=True: outside the evaluation
universe, so ratings, splits, models and results do not change (pipeline/eval_fingerprint.py checks it).
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path

import pandas as pd
import yaml

from pipeline.common import PROCESSED, RAW, TMDB_DIR, build_date, get_logger, read_json, write_json
from pipeline.tmdb import TMDB

log = get_logger("filmographies")
PEOPLE_DIR = RAW / "tmdb_people"
CFG = yaml.safe_load((Path(__file__).parent / "catalog_config.yaml").read_text())["filmography"]
OUT = PROCESSED / "filmography_candidates.csv"


def qualifying_people(credits: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Leading stars and directors of the catalog."""
    lead = credits[(credits["role"] == "cast") & (credits["credit_order"] <= cfg["lead_max_order"])]
    leads = lead.groupby("tmdb_person_id")["tmdb_id"].nunique()
    dirs = credits[credits["role"] == "director"].groupby("tmdb_person_id")["tmdb_id"].nunique()
    people = sorted(set(leads[leads >= cfg["min_lead_films"]].index) | set(dirs[dirs >= cfg["min_director_films"]].index))
    names = credits.drop_duplicates("tmdb_person_id").set_index("tmdb_person_id")["name"]
    return pd.DataFrame({"person_id": people, "name": [names[p] for p in people]})


def fetch_people(ids: list[int]) -> dict[int, dict]:
    tmdb = TMDB(rate=18)

    def one(pid: int):
        return pid, tmdb.cached(PEOPLE_DIR / f"{pid}.json", f"/person/{pid}/movie_credits", language="en-US")

    with ThreadPoolExecutor(12) as pool:
        return {pid: data for pid, data in pool.map(one, ids) if data}


def missing_films(people: pd.DataFrame, credits: dict[int, dict], in_catalog: set[int], cutoff: str,
                  cfg: dict) -> pd.DataFrame:
    """Films each person leads or directs that are not in the catalog, with the reason they are skipped
    (None = candidate). A film found through several people is listed once per person."""
    name = dict(zip(people["person_id"], people["name"]))
    rows = []
    for pid, data in credits.items():
        led = [(f, "cast") for f in data.get("cast", [])
               if (f.get("order") if f.get("order") is not None else 99) <= cfg["lead_max_order"]]
        directed = [(f, "director") for f in data.get("crew", []) if f.get("job") == "Director"]
        for f, role in led + directed:
            if f["id"] in in_catalog:
                continue
            released = bool(f.get("release_date")) and f["release_date"] <= cutoff
            votes = f.get("vote_count") or 0
            floor = cfg["min_vote_count_en"] if f.get("original_language") == "en" else cfg["min_vote_count"]
            reason = ("adult" if f.get("adult") else "not released" if not released
                      else f"fewer than {floor} votes" if votes < floor else None)
            rows.append({"tmdb_id": f["id"], "title": f.get("title"), "release_date": f.get("release_date") or None,
                         "tmdb_vote_count": votes, "language": f.get("original_language"), "person_id": pid, "person": name.get(pid), "role": role,
                         "skip_reason": reason})
    return pd.DataFrame(rows, columns=["tmdb_id", "title", "release_date", "tmdb_vote_count", "language", "person_id", "person",
                                       "role", "skip_reason"])


def main(dry: bool = False) -> None:
    catalog = set(pd.read_parquet(PROCESSED / "movies_clean.parquet", columns=["tmdb_id"])["tmdb_id"])
    # People and films come from the catalog without earlier filmography additions, so a rerun finds the same set.
    base = catalog - (set(pd.read_csv(OUT)["tmdb_id"]) if OUT.exists() else set())
    credits = pd.read_parquet(PROCESSED / "credits_clean.parquet")
    people = qualifying_people(credits[credits["tmdb_id"].isin(base)], CFG)
    log.info("qualifying people: %d", len(people))
    fetched = fetch_people(people["person_id"].tolist())
    miss = missing_films(people, fetched, base, build_date().isoformat(), CFG)
    films = miss.drop_duplicates("tmdb_id").copy()
    todo = sorted(films.loc[films["skip_reason"].isna(), "tmdb_id"].tolist())
    log.info("missing films: %d; above the vote floor: %d", len(films), len(todo))
    if dry:
        return
    import_module("pipeline.03_fetch_tmdb").fetch_all(todo)
    # Shorts, concert films and TV specials are credits too; the runtime comes from the detail.
    runtime = films["tmdb_id"].map(lambda t: (read_json(TMDB_DIR / f"{t}.json").get("runtime") or 0)
                                   if (TMDB_DIR / f"{t}.json").exists() else 0)
    short = films["skip_reason"].isna() & (runtime < CFG["min_runtime_min"])
    films.loc[short, "skip_reason"] = f"shorter than {CFG['min_runtime_min']} minutes"
    cand = films[films["skip_reason"].isna()]
    cand[["tmdb_id", "tmdb_vote_count", "person_id"]].assign(part="D").to_csv(OUT, index=False)
    log.info("candidates: %d; skipped: %s", len(cand),
             films["skip_reason"].dropna().str.replace(r"\d+", "N", regex=True).value_counts().to_dict())
    write_json(PROCESSED / "filmography_report.json", {
        "build_date": build_date().isoformat(), "settings": CFG, "people": int(len(people)),
        "missing_films": int(len(films)), "candidates": int(len(cand)),
        "candidates_by_language": cand["language"].value_counts().to_dict(),
        "candidate_list": cand[["tmdb_id", "title", "release_date", "tmdb_vote_count", "language", "person", "role"]]
        .to_dict("records"),
    })


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
