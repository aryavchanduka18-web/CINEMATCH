"""Step 8: content feature matrix (TF-IDF + structured blocks) -> artifacts/features/."""
import joblib
import pandas as pd
import scipy.sparse as sp

from cinematch_engine.models.content import build_content_features
from pipeline.common import ARTIFACTS, PROCESSED, get_logger, write_json

log = get_logger("08_features")
OUT = ARTIFACTS / "features"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    movies = pd.read_parquet(PROCESSED / "movies_clean.parquet")
    credits = pd.read_parquet(PROCESSED / "credits_clean.parquet")
    feats = build_content_features(movies, credits)
    sp.save_npz(OUT / "content.npz", feats.matrix)
    joblib.dump(feats.vectorizer, OUT / "vectorizer.joblib")
    pd.DataFrame({"row": range(len(feats.tmdb_ids)), "tmdb_id": feats.tmdb_ids,
                  "thin_text": movies["thin_text"].to_numpy()}).to_parquet(OUT / "content_index.parquet", index=False)
    write_json(OUT / "content_blocks.json", {
        "weights": feats.weights,
        "block_columns": feats.block_columns,
        "block_sizes": {k: v[1] - v[0] for k, v in feats.block_columns.items()},
        "block_vocab": {k: v for k, v in feats.block_vocab.items() if k != "text"},
    })
    log.info("content matrix %s, nnz=%d, blocks=%s", feats.matrix.shape, feats.matrix.nnz,
             {k: v[1] - v[0] for k, v in feats.block_columns.items()})


if __name__ == "__main__":
    main()