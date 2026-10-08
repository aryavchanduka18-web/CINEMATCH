"""Hybrid engine logic on tiny hand-made inputs (spec section 6)."""
import numpy as np
import pytest

from cinematch_engine.blend import blend, candidate_pool, contributions, ranked
from cinematch_engine.calibrate import MatchCalibrator
from cinematch_engine.explain import explain
from cinematch_engine.profile import behavioral_count, stage_of
from cinematch_engine.rerank import mmr
from cinematch_engine.sources import SOURCES
from cinematch_engine.tonight import Request, recommend


def test_stage_comes_from_behavior_only():
    assert [stage_of(b) for b in (0, 2, 3, 10, 11)] == ["cold", "cold", "warming", "warming", "established"]
    # 5 onboarding picks and 11 page views: still b = 0 (spec scenario 1 and 2)
    events = [("onboarding_pick", m) for m in range(5)] + [("detail_view", m) for m in range(11)]
    assert behavioral_count(events) == 0
    events += [("rate", 1), ("like", 1), ("list_add", 2), ("dislike", 3)]
    assert behavioral_count(events) == 3 and stage_of(behavioral_count(events)) == "warming"


def test_percentile_normalization_and_unproposed_zero():
    n_items = 6
    scores = {s: np.zeros((1, n_items), dtype=np.float32) for s in SOURCES}
    scores["content"][0] = [0.9, 0.1, 0.5, 0, 0, 0]
    pool, norm = candidate_pool(scores, [np.array([3, 4, 5])], per_source=3)
    ci = SOURCES.index("content")
    pos = {int(i): j for j, i in enumerate(pool[0]) if i >= 0}
    assert norm[ci, 0, pos[0]] == pytest.approx(1.0)        # best of the 3 proposed
    assert norm[ci, 0, pos[1]] == pytest.approx(1 / 3)      # worst of the 3 proposed
    assert all(i not in (3, 4, 5) for i in pool[0])          # excluded films never enter the pool


def test_blend_and_contributions():
    norm = np.zeros((len(SOURCES), 1, 2), dtype=np.float32)
    norm[SOURCES.index("content"), 0] = [1.0, 0.5]
    norm[SOURCES.index("svd"), 0] = [0.0, 1.0]
    w = {"content": 0.25, "svd": 0.75}
    final = blend(norm, w)
    assert final[0].tolist() == pytest.approx([0.25, 0.875])
    assert ranked(np.array([[10, 20]]), final, 1)[0, 0] == 20
    share = contributions(norm[:, 0, :], w)
    assert share[SOURCES.index("svd"), 1] == pytest.approx(0.75 / 0.875)


def test_mmr_trades_relevance_for_diversity():
    # Film 1 is a near-copy of film 0; film 2 is slightly less relevant but different; film 3 anchors
    # the 0-1 relevance scale.
    items = np.array([0, 1, 2, 3])
    rel = np.array([1.0, 0.95, 0.9, 0.2])
    sim = np.array([[1, 0.99, 0, 0], [0.99, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
    nov = np.zeros(4, dtype=np.float32)
    assert mmr(items, rel, sim, nov, 2, lam=0.95, beta=0).tolist() == [0, 1]    # Familiar: relevance wins
    assert mmr(items, rel, sim, nov, 2, lam=0.55, beta=0).tolist() == [0, 2]    # Discover: the near-copy is skipped


def _film(genres, runtime, lang="en", keywords=()):
    return {"genres": genres, "keywords": list(keywords), "runtime_min": runtime, "original_language": lang}


def test_for_tonight_relaxes_runtime_first_and_says_so():
    films = [_film(["Horror"], 110, "ml"), _film(["Horror"], 115, "ml"), _film(["Comedy"], 80, "ml")]
    scores = np.array([0.5, 0.9, 1.0])
    out, relaxed, note = recommend(films, scores, Request("Scary", runtime="short", language="ml"), min_results=1)
    assert out == [1, 0] and relaxed == ["runtime"]
    assert "runtime" in note


def test_for_tonight_keyword_rule_from_knowledge_base():
    films = [_film(["Thriller"], 100, keywords=["serial killer"]), _film(["Thriller"], 100)]
    out, relaxed, _ = recommend(films, np.array([0.1, 0.9]), Request("Scary"), min_results=1)
    assert out == [0] and relaxed == []


def test_explanations_respect_the_20_percent_rule_and_cap():
    sim = np.eye(5, dtype=np.float32)
    sim[4, 1] = sim[1, 4] = 0.8
    reasons = explain(4, {"content": 0.5, "popularity": 0.15, "user_cf": 0.35}, np.array([1]), sim,
                      None, neighbor_votes=14, top_genre=None, title_of=lambda i: f"Film {i}")
    codes = [r.code for r in reasons]
    assert codes == ["similar_themes", "similar_people"]          # popularity (15%) is not shown
    assert "14 people" in reasons[1].text
    many = explain(4, {s: 0.25 for s in ("content", "user_cf", "svd", "popularity")}, np.array([1]), sim, None,
                   14, "Crime", lambda i: "X")
    assert len(many) <= 3


def test_match_pct_is_capped_and_monotonic():
    cal = MatchCalibrator().fit("cold", np.linspace(0, 1, 200), np.linspace(0, 1, 200) > 0.4)
    pct = cal.match_pct("cold", np.array([0.0, 0.5, 1.0]))
    assert pct[0] < pct[1] <= pct[2] <= 99

def test_a_source_with_no_information_proposes_nothing():
    scores = {s: np.zeros((1, 6), dtype=np.float32) for s in SOURCES}     # empty profile everywhere
    scores["popularity"][0] = [5, 4, 3, 2, 1, 0]
    pool, norm = candidate_pool(scores, [np.array([], dtype=np.int64)], per_source=3)
    assert sorted(pool[0][pool[0] >= 0].tolist()) == [0, 1, 2]              # only popularity proposed
    assert norm[SOURCES.index("content")].max() == 0