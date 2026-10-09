"""Themed collections (services/collections.py): rails for Home and a page per collection."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import user_id_from
from app.db import get_db
from app.services import collections as col
from app.services import recommender as rec
from app.services.movies import cards

router = APIRouter(tags=["collections"])
RAIL = 20
PAGE = 40


@router.get("/collections")
def collections(request: Request, db: Session = Depends(get_db)) -> dict:
    """Every collection with at least MIN_FILMS films, each with its first RAIL films for this user."""
    uid = user_id_from(request, db)
    members = {c["key"]: col.member_ids(db, c) for c in col.COLLECTIONS}
    members = {k: v for k, v in members.items() if len(v) >= col.MIN_FILMS}
    match = rec.match_for(db, uid, sorted({i for ids in members.values() for i in ids}))
    out = []
    for c in col.COLLECTIONS:
        if c["key"] not in members:
            continue
        ids = col.ordered(db, c, match, members[c["key"]])
        out.append({"key": c["key"], "title": c["title"], "count": len(ids),
                    "items": cards(db, ids[:RAIL], uid, match)})
    return {"collections": out}


@router.get("/collections/{key}")
def collection(key: str, request: Request, page: int = 1, db: Session = Depends(get_db)) -> dict:
    c = col.BY_KEY.get(key)
    if c is None:
        raise HTTPException(404, "Unknown collection")
    uid = user_id_from(request, db)
    members = col.member_ids(db, c)
    match = rec.match_for(db, uid, members)
    ids = col.ordered(db, c, match, members)
    page = max(page, 1)
    return {"key": key, "title": c["title"], "count": len(ids), "page": page,
            "items": cards(db, ids[(page - 1) * PAGE: page * PAGE], uid, match)}
