import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import ROOT_DIR, get_settings
from app.routers import activity, auth, catalog, feedback, health, lab, me, onboarding, recs

settings = get_settings()
log = logging.getLogger("uvicorn.error")      # shows in the server log next to uvicorn's own lines
WEB_DIST = ROOT_DIR / "web" / "dist"


def _preload_engine() -> None:
    """Hosted copy: build the recommender in the background so the first visitor does not wait for it."""
    from app.db import SessionLocal
    from app.services import recommender as rec
    try:
        if rec.artifacts_ready():
            with SessionLocal() as db:
                rec.load_engine(db)
            log.info("recommender engine ready")
    except Exception as e:      # e.g. catalog not restored yet; requests will retry
        log.warning("engine preload skipped: %s", e)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.preload_engine:
        threading.Thread(target=_preload_engine, daemon=True).start()
    yield


app = FastAPI(title="CineMatch API", version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health, auth, me, onboarding, catalog, feedback, recs, activity, lab):
    app.include_router(r.router, prefix="/api")


if WEB_DIST.is_dir():
    # One service hosts both: built web files, and index.html for every client-side route (SPA fallback).
    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(404, "Not found")
        file = (WEB_DIST / path).resolve()
        if path and file.is_file() and file.is_relative_to(WEB_DIST.resolve()):
            cache = "public, max-age=31536000, immutable" if path.startswith("assets/") else "no-cache"
            return FileResponse(file, headers={"Cache-Control": cache})
        return FileResponse(WEB_DIST / "index.html", headers={"Cache-Control": "no-cache"})
