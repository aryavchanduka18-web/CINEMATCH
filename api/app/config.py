from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the repository root (cinematch/.env)
ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    database_url: str
    jwt_secret: str = ""
    tmdb_api_key: str = ""
    web_origin: str = "http://localhost:5173"
    app_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
