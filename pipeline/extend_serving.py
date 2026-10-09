"""Serve catalog films that were added after the models were trained (the relaxed metadata gate).

Nothing is retrained. The tuned content matrix is rebuilt with vocabularies learned from the
original-gate films only; labels (directors, cast, ...) seen only in the new films get extra columns.
Every existing row must come out identical on the original columns and zero on the extra ones
(checked; the step stops otherwise), so all similarities between existing films are unchanged. The
new films get content rows in the same feature space: they are reachable through
the content and cold-start sources like any part B/C/D film. They also get the display popularity
score (TMDB Bayesian average with the m and C stored by step 9). Safe to re-run.

    python -m pipeline.extend_serving        (after steps 5 and 12)
"""
from importlib import import_module

import numpy as np
import pandas as pd
import scipy.sparse as sp

from cinematch_engine.models.popularity import bayesian_average
from pipeline.common import ARTIFACTS, PROCESSED, TMDB_DIR, get_logger, read_json, write_json
from pipeline.models_io import MODELS, content_layout

log = get_logger("extend_serving")


def main() -> None:
    old_rows = pd.read_parquet(MODELS / "content_rows.parquet")
    old_x = sp.load_npz(MODELS / "content_matrix.npz").tocsr()
    x, tmdb, feats, stage = content_layout()
    x = x.tocsr()
    row_of = {t: r for r, t in enumerate(tmdb)}
    missing = [t for t in old_rows["tmdb_id"] if t not in row_of]
    if missing:
        raise RuntimeError(f"{len(missing)} films with content rows left the catalog (e.g. {missing[:5]}); not extending")
    old_idx = [row_of[t] for t in old_rows["tmdb_id"]]
    same = x[old_idx]
    # The saved matrix has the columns of the stages its films came from; extra labels are ordered by stage,
    # so those columns sit at the same positions and every later column must be empty for the saved films.
    old_cols = feats.columns_up_to(int(stage[old_idx].max()))
    extra_cols = np.setdiff1d(np.arange(x.shape[1]), feats.fit_columns())
    later_cols = np.setdiff1d(np.arange(x.shape[1]), old_cols)
    unchanged = (same[:, old_cols].shape == old_x.shape and abs(same[:, old_cols] - old_x).max() == 0
                 and same[:, later_cols].nnz == 0)
    if not unchanged:
        raise RuntimeError("rebuilt content rows differ from the saved ones; not extending")
    new = sorted(set(tmdb) - set(old_rows["tmdb_id"]))
    sp.save_npz(MODELS / "content_matrix.npz", x)
    pd.DataFrame({"row": range(len(tmdb)), "tmdb_id": tmdb}).to_parquet(MODELS / "content_rows.parquet", index=False)
    log.info("content matrix: %d existing rows unchanged, %d films added, %d label columns added",
             len(old_rows), len(new), len(extra_cols))

    pop = read_json(MODELS / "popularity_display.json")
    va = [read_json(TMDB_DIR / f"{t}.json") for t in new]
    votes = np.array([d.get("vote_count") or 0 for d in va], dtype=float)
    avg = np.array([d.get("vote_average") or 0 for d in va], dtype=float)
    scores = pd.DataFrame({"tmdb_id": new, "popularity_score": bayesian_average(avg * votes, votes, pop["c_tmdb"], pop["m_tmdb"])})
    updated = import_module("pipeline.09_train_models").write_popularity_to_db(scores) if new else 0

    movies = pd.read_parquet(PROCESSED / "movies_clean.parquet", columns=["tmdb_id", "catalog_part"])
    write_json(ARTIFACTS / "metrics" / "serving_extension.json", {
        "content_rows_unchanged": int(len(old_rows)), "films_added": len(new), "label_columns_added": int(len(extra_cols)),
        "films_added_by_part": movies[movies["tmdb_id"].isin(new)]["catalog_part"].value_counts().to_dict(),
        "popularity_scores_written": int(updated),
    })
    log.info("popularity scores written for %d films", updated)


if __name__ == "__main__":
    main()
