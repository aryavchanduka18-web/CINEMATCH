"""Content features (spec section 5, model 2).

TF-IDF over overview + keywords + tagline, plus one-hot blocks for genres, language, country,
director, top-5 cast and studio. Each block is L2-normalized per film and multiplied by its
weight, then the whole row is L2-normalized, so the cosine similarity of two rows is a
weighted mix of the block similarities. Phase 3 tunes the block weights.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer, normalize

BLOCKS = ("text", "genres", "language", "country", "director", "cast", "studio")
DEFAULT_WEIGHTS = {b: 1.0 for b in BLOCKS}
TOP_CAST = 5


@dataclass
class ContentFeatures:
    matrix: sp.csr_matrix
    tmdb_ids: np.ndarray
    vectorizer: TfidfVectorizer
    block_columns: dict[str, tuple[int, int]]
    block_vocab: dict[str, list[str]] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)


def film_text(movies: pd.DataFrame) -> pd.Series:
    kw = movies["keywords"].map(lambda ks: " ".join(ks) if ks is not None else "")
    return (movies["overview"].fillna("") + " " + kw + " " + movies["tagline"].fillna("")).str.strip()


def _labels(movies: pd.DataFrame, credits: pd.DataFrame) -> dict[str, list[list[str]]]:
    ids = movies["tmdb_id"].tolist()
    directors = credits[credits["role"] == "director"].groupby("tmdb_id")["name"].apply(list)
    cast = (credits[credits["role"] == "cast"].sort_values("credit_order")
            .groupby("tmdb_id")["name"].apply(lambda s: list(s)[:TOP_CAST]))
    return {
        "genres": [list(g) for g in movies["genres"]],
        "language": [[l] if l else [] for l in movies["original_language"]],
        "country": [list(c) for c in movies["countries"]],
        "director": [directors.get(i, []) for i in ids],
        "cast": [cast.get(i, []) for i in ids],
        "studio": [list(s) for s in movies["studios"]],
    }


def build_content_features(movies: pd.DataFrame, credits: pd.DataFrame,
                           weights: dict[str, float] | None = None) -> ContentFeatures:
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True, max_df=0.5, min_df=2,
                                 ngram_range=(1, 2), dtype=np.float32)
    blocks = {"text": vectorizer.fit_transform(film_text(movies))}
    vocab = {"text": vectorizer.get_feature_names_out().tolist()}
    for name, labels in _labels(movies, credits).items():
        mlb = MultiLabelBinarizer(sparse_output=True)
        blocks[name] = mlb.fit_transform(labels).astype(np.float32)
        vocab[name] = [str(c) for c in mlb.classes_]

    parts, columns, start = [], {}, 0
    for name in BLOCKS:
        block = normalize(sp.csr_matrix(blocks[name]), norm="l2") * weights[name]
        parts.append(block)
        columns[name] = (start, start + block.shape[1])
        start += block.shape[1]
    matrix = normalize(sp.hstack(parts, format="csr"), norm="l2").astype(np.float32)
    return ContentFeatures(matrix, movies["tmdb_id"].to_numpy(), vectorizer, columns, vocab, weights)