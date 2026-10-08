from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db

router = APIRouter(tags=["activity"])
TYPES = {"views": ("detail_view", "quick_view", "search_click"), "ratings": ("rate", "unrate"),
         "likes": ("like", "dislike", "clear_reaction"), "list": ("list_add", "list_remove"),
         "watched": ("watched", "unwatched"), "onboarding": ("onboarding_pick",)}


@router.get("/activity")
def activity(type: str | None = None, cursor: int | None = None, user=Depends(current_user),
             db: Session = Depends(get_db)) -> dict:
    where, p = ["i.user_id = :u"], {"u": user["id"]}
    if type in TYPES:
        where.append("i.event_type = ANY(:types)"); p["types"] = list(TYPES[type])
    if cursor:
        where.append("i.id < :c"); p["c"] = cursor
    rows = db.execute(text(f"""SELECT i.id, i.event_type, i.value, i.source, i.created_at, m.id AS movie_id, m.title,
        m.poster_path, m.backdrop_path, m.year FROM interactions i LEFT JOIN movies m ON m.id = i.movie_id
        WHERE {' AND '.join(where)} ORDER BY i.id DESC LIMIT 50"""), p).mappings().all()
    items = [{**dict(r), "created_at": r["created_at"].isoformat()} for r in rows]
    return {"items": items, "next_cursor": items[-1]["id"] if len(items) == 50 else None}