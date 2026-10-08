"""Diversity reranking (MMR) and Discovery Mode (spec section 6.8).

From the top 100 films by blend score, pick one film at a time:
    next = argmax [ lambda * relevance(i) - (1 - lambda) * max_similarity(i, picked) + beta * novelty(i) ]
relevance = blend score scaled 0-1, similarity = content cosine, novelty = -log(popularity share)
scaled 0-1. Discover also gives a small boost to films outside the user's languages and to genres
that are rare in the user's history.
"""
import numpy as np

MODES = {"familiar": {"lambda": 0.95, "beta": 0.0, "explore_boost": 0.0},
         "balanced": {"lambda": 0.75, "beta": 0.05, "explore_boost": 0.0},
         "discover": {"lambda": 0.55, "beta": 0.20, "explore_boost": 0.05}}
TOP_N = 100


def mmr(items: np.ndarray, relevance: np.ndarray, sim: np.ndarray, novelty: np.ndarray, k: int,
        lam: float, beta: float, boost: np.ndarray | None = None) -> np.ndarray:
    """items: candidate indices (sorted by relevance, at most TOP_N); sim: item x item similarity."""
    rel = relevance - relevance.min()
    rel = rel / rel.max() if rel.max() > 0 else rel
    extra = beta * novelty[items] + (boost if boost is not None else 0)
    picked: list[int] = []
    max_sim = np.zeros(len(items), dtype=np.float32)
    available = np.ones(len(items), dtype=bool)
    for _ in range(min(k, len(items))):
        score = lam * rel - (1 - lam) * max_sim + extra
        score[~available] = -np.inf
        j = int(np.argmax(score))
        picked.append(j)
        available[j] = False
        max_sim = np.maximum(max_sim, sim[items, items[j]])
    return items[picked]


def scaled_novelty(item_counts: np.ndarray, n_users: int) -> np.ndarray:
    share = np.clip(item_counts / max(n_users, 1), 1e-9, None)
    nov = -np.log(share)
    return ((nov - nov.min()) / (nov.max() - nov.min())).astype(np.float32)