"""Test setup: run every API test against a separate, freshly migrated database.

The tests never touch the development database. They create `<dbname>_test` on the same
PostgreSQL server, apply all Alembic migrations to it, and point the app at it.
"""
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.config import get_settings

API_DIR = Path(__file__).resolve().parents[1]

dev_url = make_url(get_settings().database_url)
TEST_URL = dev_url.set(database=f"{dev_url.database}_test")

# Must happen before app.db is imported, so the app engine uses the test database.
os.environ["DATABASE_URL"] = TEST_URL.render_as_string(hide_password=False)
get_settings.cache_clear()


def _recreate_test_database() -> None:
    admin = create_engine(dev_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_URL.database}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{TEST_URL.database}"'))
    admin.dispose()


def alembic_config() -> Config:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "alembic"))
    cfg.attributes["database_url"] = os.environ["DATABASE_URL"]
    return cfg


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    _recreate_test_database()
    command.upgrade(alembic_config(), "head")
    yield


@pytest.fixture(scope="session")
def test_engine(migrated_db):
    engine = create_engine(os.environ["DATABASE_URL"])
    yield engine
    engine.dispose()