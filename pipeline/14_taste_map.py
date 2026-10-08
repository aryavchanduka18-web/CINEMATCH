"""Step 14 (advanced, lab only): taste map = PCA of the SVD film vectors to 2D (spec section 14.2).

PCA, not t-SNE: PCA is a fixed linear projection, so a user's folded-in vector can be placed on the
same map later without redrawing it. The map is a picture of the model, not a recommender.
"""
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from pipeline.common import ARTIFACTS, PROCESSED, get_logger, write_json
from pipeline.models_io import MODELS

log = get_logger("14_taste_map")
N_POINTS = 2500


def main() -> None:
    f = np.load(MODELS / "fitted.npz")
    Q, counts, tmdb = f["svd_Q"], f["item_counts"], f["item_tmdb"]
    pca = PCA(n_components=2, random_state=42).fit(Q[counts > 0])
    xy = pca.transform(Q)
    movies = pd.read_parquet(PROCESSED / "movies_clean.parquet", columns=["tmdb_id", "title", "year", "genres"])
    meta = movies.set_index("tmdb_id")
    top = np.argsort(-counts)[:N_POINTS]
    points = []
    for i in top:
        m = meta.loc[tmdb[i]]
        points.append({"tmdb_id": int(tmdb[i]), "title": m["title"], "year": None if pd.isna(m["year"]) else int(m["year"]),
                       "genre": (list(m["genres"]) or ["Other"])[0], "x": round(float(xy[i, 0]), 4), "y": round(float(xy[i, 1]), 4)})
    write_json(ARTIFACTS / "lab" / "taste_map.json", {
        "points": points, "components": pca.components_.tolist(), "mean": pca.mean_.tolist(),
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "note": "PCA of Funk SVD film vectors (films with the most training ratings). A user is placed by projecting "
                "their folded-in SVD vector with the same components."})
    log.info("taste map: %d points, explained variance %s", len(points), pca.explained_variance_ratio_.round(3).tolist())


if __name__ == "__main__":
    main()