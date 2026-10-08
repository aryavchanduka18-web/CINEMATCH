"""Content-based model (spec section 5, model 2).

Features: TF-IDF over overview + keywords + tagline, plus one-hot blocks for genres, language,
country, director, top-5 cast and studio. Each block is L2-normalized per film and multiplied by
its weight, then the whole row is L2-normalized, so the cosine similarity of two films is a
weighted mix of the block similarities.

User profile: weighted mean of liked films (rating >= 7, weight rating - 6) minus the weighted mean
of disliked films (rating <= 5, weight 6 - rating). A film's score is its similarity to the profile.
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
LIKE_MIN, DISLIKE_MAX, NEUTRAL = 7, 5, 6


@dataclass
class ContentFeatures:
    matrix: sp.csr_matrix
    tmdb_ids: np.ndarray
    vectorizer: TfidfVectorizer
    block_columns: dict[str, tuple[int, int]]
    block_vocab: dict[str, list[str]] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)


@dataclass
class ContentBlocks:
    """Raw (unweighted) feature blocks, built once and recombined cheaply while tuning."""
    blocks: dict[str, sp.csr_matrix]
    tmdb_ids: np.ndarray
    vectorizer: TfidfVectorizer
    vocab: dict[str, list[str]]


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


def build_blocks(movies: pd.DataFrame, credits: pd.DataFrame, ngram_max: int = 2) -> ContentBlocks:
    # min_df=2 drops one-off words; skipped for tiny corpora (tests), where it would remove everything.
    min_df = 2 if len(movies) >= 50 else 1
    vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True, max_df=0.5, min_df=min_df,
                                 ngram_range=(1, ngram_max), dtype=np.float32)
    blocks = {"text": sp.csr_matrix(vectorizer.fit_transform(film_text(movies)))}
    vocab = {"text": vectorizer.get_feature_names_out().tolist()}
    for name, labels in _labels(movies, credits).items():
        mlb = MultiLabelBinarizer(sparse_output=True)
        blocks[name] = sp.csr_matrix(mlb.fit_transform(labels), dtype=np.float32)
        vocab[name] = [str(c) for c in mlb.classes_]
    return ContentBlocks(blocks, movies["tmdb_id"].to_numpy(), vectorizer, vocab)


def combine(cb: ContentBlocks, weights: dict[str, float] | None = None) -> ContentFeatures:
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    parts, columns, start = [], {}, 0
    for name in BLOCKS:
        block = cb.blocks[name]
        if block.shape[1]:  # an empty block (no labels at all) has nothing to normalize
            block = normalize(block, norm="l2") * weights[name]
        parts.append(block)
        columns[name] = (start, start + block.shape[1])
        start += block.shape[1]
    matrix = normalize(sp.hstack(parts, format="csr"), norm="l2").astype(np.float32)
    return ContentFeatures(matrix, cb.tmdb_ids, cb.vectorizer, columns, cb.vocab, weights)


def build_content_features(movies: pd.DataFrame, credits: pd.DataFrame,
                           weights: dict[str, float] | None = None, ngram_max: int = 2) -> ContentFeatures:
    return combine(build_blocks(movies, credits, ngram_max), weights)


def profile_weights(ratings: sp.csr_matrix) -> sp.csr_matrix:
    """Per-user film weights: liked films sum to +1, disliked films sum to -1, neutral ones are 0."""
    r = ratings.tocsr().astype(np.float32)
    liked = r.copy()
    liked.data = np.where(liked.data >= LIKE_MIN, liked.data - NEUTRAL, 0).astype(np.float32)
    disliked = r.copy()
    disliked.data = np.where((disliked.data > 0) & (disliked.data <= DISLIKE_MAX), NEUTRAL - disliked.data, 0).astype(np.float32)
    liked.eliminate_zeros()
    disliked.eliminate_zeros()
    liked = normalize(liked, norm="l1")
    disliked = normalize(disliked, norm="l1")
    return (liked - disliked).tocsr()


class ContentModel:
    """Scores = profile weights x (film-film content similarity)."""

    def __init__(self, item_matrix: sp.csr_matrix):
        self.item_matrix = item_matrix                     # rows = universe films, L2-normalized
        self.sim = (item_matrix @ item_matrix.T).toarray().astype(np.float32)

    def fit(self, train: sp.csr_matrix) -> "ContentModel":
        self.weights = profile_weights(train)
        return self

    def score(self, users: np.ndarray) -> np.ndarray:
        return np.asarray(self.weights[users] @ self.sim, dtype=np.float32)