"""Move what the hosted site needs from this laptop into the hosted database.

    .venv\\Scripts\\python.exe scripts\\deploy_data.py export     # writes deploy-out\\ and prints sizes
    .venv\\Scripts\\python.exe scripts\\deploy_data.py upload     # asks for the Render database URL

export makes three files in deploy-out/ (git-ignored, never commit them):
  catalog.dump        pg_dump (custom format, data only) of the film catalog and content tables:
                      movies, genres, movie_genres, people, movie_credits, keywords, movie_keywords, movie_awards
  demo_user.json      the prepared demo account and its ratings, likes, list and history (password hash only)
  artifacts.tar.gz    what the recommender reads at serve time: artifacts/models, artifacts/metrics, artifacts/lab
                      (the training feature files in artifacts/features are not needed by the server)

upload restores them into a database whose schema the web service has already created
(it runs `alembic upgrade head` on start), so deploy the service first, then upload.
Needs Docker Desktop running (pg_restore runs in the postgres:17 image).
"""
import argparse
import getpass
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deploy-out"
CATALOG_TABLES = ["movies", "genres", "movie_genres", "people", "movie_credits", "keywords", "movie_keywords",
                  "movie_awards"]
DEMO_EMAIL = "demo@cinematch.local"
# Tables that belong to one user, in insert order (the users row first, then the rows that point to it).
USER_TABLES = ["user_preferences", "onboarding_picks", "ratings", "reactions", "user_movie_list", "watched",
               "interactions"]
ARTIFACT_DIRS = ["models", "metrics", "lab"]

sys.path.insert(0, str(ROOT / "api"))


def _env(name: str, default: str = "") -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip()
    return os.environ.get(name, default)


def _local_url() -> str:
    from app.config import get_settings
    return get_settings().database_url


def _mb(p: Path) -> str:
    return f"{p.stat().st_size / 1e6:.1f} MB"


def export() -> None:
    OUT.mkdir(exist_ok=True)
    user, db = _env("POSTGRES_USER", "cinematch"), _env("POSTGRES_DB", "cinematch")
    dump = OUT / "catalog.dump"
    cmd = ["docker", "exec", "cinematch-db", "pg_dump", "-U", user, "-d", db, "-Fc", "--data-only", "--no-owner",
           "--no-privileges"] + [a for t in CATALOG_TABLES for a in ("-t", t)]
    with dump.open("wb") as f:
        subprocess.run(cmd, stdout=f, check=True)

    engine = create_engine(_local_url())
    with engine.connect() as conn:
        uid = conn.execute(text("SELECT id FROM users WHERE email = :e"), {"e": DEMO_EMAIL}).scalar()
        demo = {}
        if uid is not None:
            demo["users"] = [conn.execute(text("""SELECT email, password_hash, display_name, is_guest, created_at,
                onboarded_at FROM users WHERE id = :u"""), {"u": uid}).mappings().one()]
            for t in USER_TABLES:
                demo[t] = list(conn.execute(text(f"SELECT * FROM {t} WHERE user_id = :u"), {"u": uid}).mappings())
        counts = {t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in CATALOG_TABLES}
    (OUT / "demo_user.json").write_text(json.dumps({t: [dict(r) for r in rows] for t, rows in demo.items()}, default=str))

    bundle = OUT / "artifacts.tar.gz"
    with tarfile.open(bundle, "w:gz", compresslevel=9) as tar:
        for d in ARTIFACT_DIRS:
            tar.add(ROOT / "artifacts" / d, arcname=d)

    print("Exported to deploy-out/:")
    print(f"  catalog.dump      {_mb(dump)}   rows: " + ", ".join(f"{t} {n:,}" for t, n in counts.items()))
    print(f"  demo_user.json    {_mb(OUT / 'demo_user.json')}   " +
          (", ".join(f"{t} {len(r)}" for t, r in demo.items()) if demo else "no demo account found"))
    print(f"  artifacts.tar.gz  {_mb(bundle)}   (" + ", ".join(ARTIFACT_DIRS) + ")")


def _target_url(arg: str | None) -> str:
    url = arg or os.environ.get("TARGET_DATABASE_URL") or getpass.getpass(
        "Paste the External Database URL from Render (input is hidden): ")
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def refresh_catalog(engine) -> None:
    """Bring an existing hosted catalog up to date without touching accounts: every film is upserted by
    its TMDB id (hosted ids stay, so users' ratings and lists still point at the same films), new films
    are added, nothing is deleted. Then the display popularity is copied from the laptop's database."""
    import pandas as pd
    sys.path.insert(0, str(ROOT))
    from pipeline.loader import load_catalog
    processed = ROOT / "data" / "processed"
    counts = load_catalog(engine, pd.read_parquet(processed / "movies_clean.parquet"),
                          pd.read_parquet(processed / "credits_clean.parquet"), pd.read_parquet(processed / "awards.parquet"),
                          pd.read_parquet(processed / "ml_aggregates.parquet"), prune=False)
    with create_engine(_local_url()).connect() as local:
        pop = [{"t": t, "s": s} for t, s in local.execute(text(
            "SELECT tmdb_id, popularity_score FROM movies WHERE popularity_score IS NOT NULL"))]
    with engine.begin() as conn:
        conn.execute(text("CREATE TEMP TABLE pop (tmdb_id int PRIMARY KEY, score real) ON COMMIT DROP"))
        conn.execute(text("INSERT INTO pop VALUES (:t, :s)"), pop)
        conn.execute(text("UPDATE movies m SET popularity_score = p.score FROM pop p WHERE p.tmdb_id = m.tmdb_id"))
    print(f"    films: {counts['movies']:,}; credits: {counts['movie_credits']:,}")


def upload(target: str | None, refresh: bool = False) -> None:
    for f in ("catalog.dump", "demo_user.json", "artifacts.tar.gz"):
        if not (OUT / f).exists():
            sys.exit(f"deploy-out/{f} is missing. Run the export step first.")
    url = _target_url(target)
    engine = create_engine(make_url(url).set(drivername="postgresql+psycopg"))
    with engine.connect() as conn:
        if conn.execute(text("SELECT to_regclass('alembic_version')")).scalar() is None:
            sys.exit("That database has no CineMatch tables yet. Deploy the web service first (it creates them), "
                     "wait until it is live, then run this again.")
        has_movies = conn.execute(text("SELECT count(*) FROM movies")).scalar() > 0

    if has_movies and refresh:
        print("1/3 Catalog: refreshing from this laptop (upsert by TMDB id; accounts and their ratings are kept)...")
        refresh_catalog(engine)
    elif has_movies:
        print("1/3 Catalog: already there, skipped (add --refresh-catalog to bring it up to date).")
    else:
        print("1/3 Catalog: restoring with pg_restore (a few minutes)...")
        subprocess.run(["docker", "run", "--rm", "-e", "TARGET", "-v", f"{OUT}:/dump:ro", "postgres:17", "sh", "-c",
                        'pg_restore --data-only --no-owner --no-privileges --single-transaction -d "$TARGET" '
                        "/dump/catalog.dump"], check=True, env={**os.environ, "TARGET": url})

    demo = json.loads((OUT / "demo_user.json").read_text())
    with engine.begin() as conn:
        if not demo:
            print("2/3 Demo account: none in the export, skipped.")
        elif conn.execute(text("SELECT 1 FROM users WHERE email = :e"), {"e": DEMO_EMAIL}).first():
            print("2/3 Demo account: already there, skipped.")
        else:
            u = demo["users"][0]
            uid = conn.execute(text("""INSERT INTO users (email, password_hash, display_name, is_guest, created_at,
                onboarded_at) VALUES (:email, :password_hash, :display_name, :is_guest, :created_at, :onboarded_at)
                RETURNING id"""), u).scalar()
            for t in USER_TABLES:
                for row in demo.get(t, []):
                    row = {k: v for k, v in row.items() if k != "id"} | {"user_id": uid}
                    cols = ", ".join(row)
                    conn.execute(text(f"INSERT INTO {t} ({cols}) SELECT {cols} FROM json_populate_record(NULL::{t}, :j)"),
                                 {"j": json.dumps(row)})
            print("2/3 Demo account: created with its ratings, likes, list and history.")

    from app.services.artifact_store import BUNDLE, TABLE_SQL
    data = (OUT / "artifacts.tar.gz").read_bytes()
    with engine.begin() as conn:
        conn.execute(text(TABLE_SQL))
        conn.execute(text("""INSERT INTO deploy_artifacts (name, sha256, data) VALUES (:n, :s, :d)
            ON CONFLICT (name) DO UPDATE SET sha256 = :s, data = :d, uploaded_at = now()"""),
                     {"n": BUNDLE, "s": hashlib.sha256(data).hexdigest(), "d": data})
        conn.execute(text("ANALYZE"))
    print(f"3/3 Model bundle: uploaded ({len(data) / 1e6:.1f} MB).")
    print("Done. In Render, open the web service and choose Manual Deploy > Restart service, then open the site.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export")
    up = sub.add_parser("upload")
    up.add_argument("--target", help="database URL (otherwise TARGET_DATABASE_URL or a hidden prompt)")
    up.add_argument("--refresh-catalog", action="store_true",
                    help="update a catalog that is already there (new films, franchise data); accounts are kept")
    a = p.parse_args()
    export() if a.cmd == "export" else upload(a.target, a.refresh_catalog)
