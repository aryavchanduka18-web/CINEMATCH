from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.services import events as ev
from app.services.events import IMPLICIT_EVENTS
from app.services.movies import cards

router = APIRouter(tags=["feedback"])


def exists(db: Session, movie_id: int) -> None:
    if not db.execute(text("SELECT 1 FROM movies WHERE id = :m"), {"m": movie_id}).first():
        raise HTTPException(404, "Unknown movie")


class RatingBody(BaseModel):
    rating: int = Field(ge=1, le=10)
    source: str | None = None


class ReactionBody(BaseModel):
    value: int
    source: str | None = None


class SourceBody(BaseModel):
    source: str | None = None


@router.put("/ratings/{movie_id}")
def rate(movie_id: int, body: RatingBody, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    exists(db, movie_id)
    ev.set_rating(db, user["id"], movie_id, body.rating, body.source)
    db.commit()
    return {"ok": True}


@router.delete("/ratings/{movie_id}")
def unrate(movie_id: int, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ev.clear_rating(db, user["id"], movie_id)
    db.commit()
    return {"ok": True}


@router.put("/reactions/{movie_id}")
def react(movie_id: int, body: ReactionBody, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if body.value not in (1, -1):
        raise HTTPException(422, "value must be 1 (like) or -1 (dislike)")
    exists(db, movie_id)
    ev.set_reaction(db, user["id"], movie_id, body.value, body.source)
    db.commit()
    return {"ok": True}


@router.delete("/reactions/{movie_id}")
def unreact(movie_id: int, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ev.clear_reaction(db, user["id"], movie_id)
    db.commit()
    return {"ok": True}


@router.put("/list/{movie_id}")
def list_add(movie_id: int, body: SourceBody | None = None, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    exists(db, movie_id)
    ev.add_to_list(db, user["id"], movie_id, body.source if body else None)
    db.commit()
    return {"ok": True}


@router.delete("/list/{movie_id}")
def list_remove(movie_id: int, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ev.remove_from_list(db, user["id"], movie_id)
    db.commit()
    return {"ok": True}


@router.get("/list")
def get_list(sort: str = "recent", user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    order = {"recent": "l.added_at DESC", "rating": "m.popularity_score DESC NULLS LAST", "year": "m.year DESC NULLS LAST",
             "title": "m.title"}.get(sort, "l.added_at DESC")
    ids = [r[0] for r in db.execute(text(f"""SELECT m.id FROM user_movie_list l JOIN movies m ON m.id = l.movie_id
        WHERE l.user_id = :u ORDER BY {order}"""), {"u": user["id"]})]
    items = cards(db, ids, user["id"])
    if sort == "genre":
        items.sort(key=lambda c: (c["movie"]["genres"] or ["~"])[0])
    return {"items": items}


@router.put("/watched/{movie_id}")
def watched(movie_id: int, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    exists(db, movie_id)
    ev.mark_watched(db, user["id"], movie_id)
    db.commit()
    return {"ok": True}


@router.delete("/watched/{movie_id}")
def unwatched(movie_id: int, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    ev.unmark_watched(db, user["id"], movie_id)
    db.commit()
    return {"ok": True}


class EventBody(BaseModel):
    movie_id: int | None = None
    event_type: str
    source: str | None = None
    position: int | None = None


@router.post("/events")
def event(body: EventBody, user=Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Lightweight implicit events. Hover is never logged; detail_view counts once per film per day."""
    if body.event_type not in IMPLICIT_EVENTS:
        raise HTTPException(422, f"event_type must be one of {sorted(IMPLICIT_EVENTS)}")
    if body.event_type == "detail_view" and body.movie_id and ev.detail_view_logged_today(db, user["id"], body.movie_id):
        return {"ok": True, "deduplicated": True}
    ev.log(db, user["id"], body.movie_id, body.event_type, None, body.source, body.position)
    db.commit()
    return {"ok": True}