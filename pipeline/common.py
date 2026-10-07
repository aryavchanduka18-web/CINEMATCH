"""Shared paths, settings and logging for the pipeline steps."""
import json
import logging
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
ARTIFACTS = ROOT / "artifacts"

ML_DIR = RAW / "ml-32m"
TMDB_DIR = RAW / "tmdb"            # one JSON per film: <tmdb_id>.json
DISCOVER_DIR = RAW / "tmdb_discover"
IMAGES_DIR = RAW / "images"
WIKIDATA_DIR = RAW / "wikidata"

SEED = 42


def env(name: str, default: str = "") -> str:
    """Read a value from the process environment, else from cinematch/.env. Never logged."""
    if name in os.environ:
        return os.environ[name]
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip()
    return default


def build_date() -> date:
    """The catalog build date (override with CATALOG_BUILD_DATE=YYYY-MM-DD for reproducible rebuilds)."""
    value = env("CATALOG_BUILD_DATE")
    return date.fromisoformat(value) if value else date.today()


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # per-request lines are noise
    return logging.getLogger(name)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))