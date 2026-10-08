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
| 2026-10-08 | Part D films | `ml_movie_id` left empty even when MovieLens has a few ratings | Part D is outside the evaluation universe, like B and C | `pipeline/05_clean.py` || 2026-10-08 | Popularity m | Tuned m ends at the top of the grid (1,000,000): validation keeps rewarding "much-rated and above average" | That limit ranks films by count x (mean - global mean); it is the honest tuning result | `pipeline/09_train_models.py` grid |
| 2026-10-08 | Display popularity | `movies.popularity_score` uses the same Bayesian formula with m = median part-A rating count (TMDB counts for B/C/D and the holdout films) | The ranking-optimal m squashes every displayed score to the global mean | `popularity_scores()` in step 9 |
| 2026-10-08 | Item CF / user CF tuning | Shrinkage, beta and k settle at the edges of wide grids (strong preference for well-supported, popular neighbors) | Same popularity effect; reported, not chased further | step 9 grids |
| 2026-10-08 | Model selection metric | Every ranking model is tuned on validation NDCG@10; SVD's RMSE is reported alongside | The site shows ranked lists | step 9 |
| 2026-10-08 | Fold-in regularization (SVD) | lambda = reg_all x number of the user's ratings | Matches the per-rating SGD penalty | `models/svd.py` |
| 2026-10-08 | Content profile | likes and onboarding picks count as 10/10, dislikes as 1/10 | Spec 6.1 "same weight as a like" | `sources.py`, `online.py` |
| 2026-10-08 | ALS signal (live) | strength = sum of event weights + (rating - 6) for 7+, likes/picks at least 4; negative totals dropped | ALS needs positive confidence; dislikes are filtered anyway | `online.py` |
| 2026-10-08 | Candidates | A source with no information about the user (flat scores) proposes nothing | Otherwise empty sources added arbitrary films (bug found in the k=0 cold-start experiment) | `blend.py` |
| 2026-10-08 | Rails on filtered sets | Rails that filter the catalog (languages, awards, popcorn, genre pages) rank by a catalog-wide hybrid score: each source's percentile over all films it scores, blended with the stage weights | The 300-film pool is too small to fill filtered rails | `online.py::rail_scores` |
| 2026-10-08 | Match % outside the pool | Calibrator applied to the catalog-wide hybrid score | Same 0-1 percentile scale as the pool score | `online.py` |
| 2026-10-08 | Community rating | popularity_score acts as 20 prior votes, site ratings add to it | Spec 6.7 "Bayesian average of MovieLens and site ratings" | `services/movies.py` |
| 2026-10-08 | Served models | The website serves models fitted on the training split (same files the hybrid was tuned with) | Keeps evaluated == served; a full-data refit is a one-line change (`10_tune_hybrid --refit` on a split with all ratings) | `pipeline/models_io.py` |
| 2026-10-08 | Scenario tests | Run against the development database with throwaway users that are deleted afterwards | The test database has no catalog | `api/scenarios/` |
| 2026-10-08 | Demo account | `demo@cinematch.local`, password generated into `.env` (DEMO_PASSWORD) | Spec 17 prepared account; no secret in git | `pipeline/demo_accounts.py` |