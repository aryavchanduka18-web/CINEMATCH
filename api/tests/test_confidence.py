"""Recommendation confidence: percentiles from real scores, agreement from their spread, honest gaps."""
from types import SimpleNamespace

import numpy as np

from app.services.confidence import confidence, label, percentiles

INF = -np.inf


def engine(weights: dict) -> SimpleNamespace:
    return SimpleNamespace(weights={"warm": weights})


def test_percentile_counts_only_films_the_model_can_score():
    p = percentiles({"svd": np.array([0.1, 0.9, INF, 0.5])}, row=1)
    assert p == {"svd": 1.0}                       # top of the 3 scorable films
    assert percentiles({"svd": np.array([0.1, INF])}, row=1) == {}


def test_models_that_agree_give_high_agreement():
    scores = {s: np.array([0.0, 1.0, 0.5]) for s in ("svd", "content", "als", "popularity")}
    c = confidence(engine({"svd": .25, "content": .25, "als": .25, "popularity": .25}), SimpleNamespace(stage="warm"), 1, 90, scores)
    assert c["agreement"] == 100 and c["label"] == "High"
    assert {g["key"]: g["score"] for g in c["groups"]} == {"collaborative": 100, "content": 100, "behavioral": 100,
                                                           "popularity": 100, "hybrid": 90}
    assert "strong match" in c["sentence"]


def test_split_models_give_low_agreement_and_name_the_disagreement():
    n = 100
    up, down = np.arange(n, dtype=float), -np.arange(n, dtype=float)
    scores = {"content": up, "svd": down}
    c = confidence(engine({"content": .5, "svd": .5}), SimpleNamespace(stage="warm"), n - 1, 50, scores)
    assert c["agreement"] < 10 and c["label"] == "Low"
    assert c["sentence"].startswith("It is close to films you like, but people with similar taste are less keen")


def test_one_model_is_not_enough_to_claim_agreement():
    c = confidence(engine({"content": 1.0}), SimpleNamespace(stage="warm"), 0, None, {"content": np.array([1.0, 0.0])})
    assert c["agreement"] is None and c["label"] is None
    assert [g["score"] for g in c["groups"] if g["key"] == "collaborative"] == [None]


def test_models_with_zero_weight_are_listed_but_not_counted():
    scores = {"svd": np.array([0.0, 1.0]), "content": np.array([0.0, 1.0]), "als": np.array([1.0, 0.0])}
    c = confidence(engine({"svd": .5, "content": .5, "als": 0}), SimpleNamespace(stage="warm"), 1, 70, scores)
    assert c["agreement"] == 100
    assert {t["source"]: t["counted"] for t in c["technical"]} == {"svd": True, "content": True, "als": False}


def test_labels():
    assert [label(x) for x in (None, 90, 75, 74, 50, 49)] == [None, "High", "High", "Moderate", "Moderate", "Low"]
