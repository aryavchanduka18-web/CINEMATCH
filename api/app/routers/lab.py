"""Research Lab: read-only, every number comes from an artifacts/ file (spec section 13)."""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import recommender as rec

router = APIRouter(prefix="/lab", tags=["lab"])
ROOT = Path(__file__).resolve().parents[3] / "artifacts"


def read(rel: str):
    p = ROOT / rel
    if not p.exists():
        raise HTTPException(404, f"{rel} has not been produced yet")
    return json.loads(p.read_text(encoding="utf-8"))


@router.get("/models")
def models() -> dict:
    names = ("bias", "popularity", "content", "user_cf", "item_cf", "svd", "als")
    return {n: read(f"models/{n}.json")["settings"] for n in names if (ROOT / f"models/{n}.json").exists()}


@router.get("/metrics")
def metrics() -> dict:
    out = {}
    for name in ("validation_baselines", "validation_mf", "validation_hybrid", "test_comparison", "global_cutoff"):
        if (ROOT / f"metrics/{name}.json").exists():
            out[name] = read(f"metrics/{name}.json")
    return out


@router.get("/cold-start")
def cold_start() -> dict:
    return read("metrics/cold_start.json")


@router.get("/new-movies")
def new_movies() -> dict:
    return read("metrics/new_movies.json")


@router.get("/diversity")
def diversity() -> dict:
    return read("metrics/diversity.json")


@router.get("/calibration")
def calibration() -> dict:
    return read("metrics/calibration_check.json")


@router.get("/weights")
def weights() -> dict:
    return read("models/hybrid_weights.json")


@router.get("/catalog-audit")
def catalog_audit() -> dict:
    return read("metrics/catalog_audit.json")


@router.get("/user/{user_id}/candidates")
def user_candidates(user_id: int, db: Session = Depends(get_db)) -> dict:
    """User Inspector: stage, counts and per-source scores behind each top pick."""
    engine = rec.load_engine(db)
    st = rec.user_state(db, user_id, engine)
    picks = engine.top_picks(st, "balanced", k=20)
    cat = engine.cat
    return {"user_id": user_id, "stage": st.stage, "behavioral_count": st.behavioral_count,
            "onboarding_count": len(st.picks), "weights": engine.weights[st.stage],
            "items": [{"movie_id": int(cat.movie_ids[p["row"]]), "title": cat.titles[p["row"]], "final_score": p["score"],
                       "match_pct": p["match_pct"], "shares": p["shares"],
                       "reasons": engine.reasons(st, p["row"], p["shares"], p["reranked"])} for p in picks]}

@router.get("/shilling")
def shilling() -> dict:
    return read("lab/shilling.json")


@router.get("/ncf")
def ncf() -> dict:
    return read("lab/ncf.json")


@router.get("/taste-map")
def taste_map(user_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    """The precomputed map, plus "You": the user's SVD vector folded in from their ratings and
    projected with the same PCA components."""
    import numpy as np
    data = read("lab/taste_map.json")
    out = {k: data[k] for k in ("points", "explained_variance_ratio", "note")}
    if user_id is not None and rec.artifacts_ready():
        engine = rec.load_engine(db)
        st = rec.user_state(db, user_id, engine)
        cat, svd = engine.cat, engine.src.svd
        items = [(cat.universe_of_row[r], v) for r, v in st.ratings.items() if cat.universe_of_row[r] >= 0]
        if items:
            idx = np.array([i for i, _ in items])
            r = np.array([v for _, v in items], dtype=np.float64)
            X = np.hstack([svd["Q"][idx], np.ones((len(idx), 1))])
            sol = np.linalg.solve(X.T @ X + svd["reg"] * len(idx) * np.eye(X.shape[1]), X.T @ (r - svd["mu"] - svd["bi"][idx]))
            p = sol[:-1]
            comp, mean = np.array(data["components"]), np.array(data["mean"])
            # A user vector lives in the same space as film vectors: place it with the film projection.
            xy = comp @ (p - mean)
            out["you"] = {"x": float(xy[0]), "y": float(xy[1]), "ratings_used": len(idx)}
    return out