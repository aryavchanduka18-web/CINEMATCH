from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Liveness check that also runs a real query against PostgreSQL."""
    try:
        db.execute(text("select 1")).scalar_one()
        db_status = "ok"
    except SQLAlchemyError:
        db_status = "error"
    return {"status": "ok", "db": db_status, "version": get_settings().app_version}

@router.get("/ping")
def ping() -> dict:
    """Keep-awake check for uptime monitors. It never touches the database, so pinging it every few
    minutes keeps the web service awake without keeping the Neon database awake (Neon's free plan
    counts the hours the database is awake)."""
    return {"status": "ok"}
