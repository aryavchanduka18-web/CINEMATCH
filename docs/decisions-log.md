# Decisions log

Choices made during the build where the spec left room. Each entry: date, choice, why, how to undo.

| Date | Area | Choice | Why | How to undo |
|---|---|---|---|---|
| 2026-10-07 | API port | FastAPI runs on 8010 | Port 8000 was already used by another program on the laptop | Change `API_PORT` in `.env` |
| 2026-10-08 | Search | `search_vector` = title + original title + director + cast, filled by the loader (migration 0002) | Spec section 10; cast and director live in other tables, so it cannot be a generated column | Revert migration 0002 |
| 2026-10-08 | Catalog step order | Final `catalog_ids.csv` is written by step 5, step 2 writes the candidate pool | The final cut needs the TMDB metadata gate | n/a |
| 2026-10-08 | New-movie holdout | Holdout films' ratings removed from train, val AND test; kept only in `newmovie_test.parquet` | Keeps the main test about known films and the new-movie test clean | `pipeline/07_split.py` |
| 2026-10-08 | Awards | `award` = award series (Wikidata P361), `category` = specific prize; "X Award for Y" split by pattern | Consistent names for the Awards rail | `pipeline/04_fetch_awards_wikidata.py::split_prize` |
| 2026-10-08 | Awards rail | Golden Raspberry awards are stored but must be excluded from "Award Winners & Nominees" | They are anti-awards | Rail filter (Phase 7+) |
| 2026-10-08 | Per-language cap | Ties on vote count broken by TMDB id | Deterministic catalog | `pipeline/selection.py` |
| 2026-10-08 | Loader | Removes films that left the catalog unless user data references them | Keeps the DB equal to the catalog without touching user data | `load_catalog(prune=False)` |
| 2026-10-08 | Part D films | `ml_movie_id` left empty even when MovieLens has a few ratings | Part D is outside the evaluation universe, like B and C | `pipeline/05_clean.py` |