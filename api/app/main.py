from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import activity, auth, catalog, feedback, health, lab, me, onboarding, recs

settings = get_settings()

app = FastAPI(title="CineMatch API", version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health, auth, me, onboarding, catalog, feedback, recs, activity, lab):
    app.include_router(r.router, prefix="/api")