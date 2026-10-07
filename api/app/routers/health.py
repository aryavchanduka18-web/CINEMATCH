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