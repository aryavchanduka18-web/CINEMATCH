# CineMatch

An explainable hybrid movie recommendation website (college Recommender Systems project).
It recommends movies; it does not stream them.

| Part | Folder | Tech |
| --- | --- | --- |
| Website | `web/` | React, TypeScript, Vite, Tailwind, React Router, TanStack Query, Framer Motion |
| API | `api/` | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, psycopg 3 |
| Database | `docker-compose.yml` | PostgreSQL 17 in Docker |
| Recommendation engine | `engine/` | Python package `cinematch_engine`, shared by the API and the pipeline |
| Offline pipeline | `pipeline/` | Builds data and trains models (Phase 2) |

Other folders: `notebooks/` (experiments), `data/` and `artifacts/` (big local files, not in git), `docs/viva/` (viva notes).

## What you need installed (once)

- Docker Desktop (with WSL 2)
- Python 3.12 (`py -3.12 --version` should work)
- Node.js 20 or newer
- Git

## First-time setup

Open PowerShell in the `cinematch` folder.

1. Create your secrets file (skip this if `.env` already exists):
   ```powershell
   Copy-Item .env.example .env
   ```
   Open `.env` and replace the `change-me` values with long random strings, and paste your TMDB key after `TMDB_API_KEY=`.
   Use the same password in `POSTGRES_PASSWORD` and inside `DATABASE_URL`.

2. Create the Python environment and install the API and engine:
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e ".\engine[dev]" -e ".\api[dev]"
   ```

3. Install the website packages:
   ```powershell
   cd web; npm install; cd ..
   ```

If PowerShell refuses to run the scripts below, allow local scripts for your user once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Running it every day

1. **Start Docker Desktop** from the Start menu and wait until it says "Engine running".
2. **Start the database:**
   ```powershell
   .\scripts\db.ps1
   ```
3. **Create or update the tables** (safe to run any time):
   ```powershell
   .\scripts\migrate.ps1
   ```
4. **Start the API** (leave this window open):
   ```powershell
   .\scripts\api.ps1
   ```
   Check it: http://127.0.0.1:8010/api/health should show `"db": "ok"`.
   API docs: http://127.0.0.1:8010/docs
5. **Start the website** in a second PowerShell window (leave it open):
   ```powershell
   .\scripts\web.ps1
   ```
6. **Open http://localhost:5173** in your browser. The Home page should say `API: ok, DB: ok`.

To stop: press `Ctrl+C` in the API and website windows, then run `.\scripts\db.ps1 stop`.

## Building the data and the models (once, about 1-2 hours)

The website needs the catalog in the database and the trained models in `artifacts/`. With the
database running:

```powershell
.\scripts\data.ps1              # steps 1-12: download, TMDB, Wikidata, clean, ratings, splits,
                                # features, train + tune models, hybrid weights, evaluation, DB load
.\.venv\Scripts\python.exe -m pipeline.13_shilling     # optional lab experiments
.\.venv\Scripts\python.exe -m pipeline.14_taste_map
.\.venv\Scripts\python.exe -m pipeline.15_ncf
.\.venv\Scripts\python.exe -m pipeline.report_validation   # refresh docs/phase-*-results.md
.\.venv\Scripts\python.exe -m pipeline.demo_accounts       # the prepared demo account
```

Everything downloaded is cached in `data/raw/`, so re-running never fetches twice. Keep the laptop
plugged in with the lid open during long runs (sleep pauses the jobs).

## Where things are

| What | Where |
|---|---|
| The approved spec | `docs/spec.md` |
| Results tables per phase | `docs/phase-3-results.md` ... `docs/phase-6-results.md` |
| Viva notes per phase | `docs/viva/` |
| Architecture overview | `docs/architecture.md` |
| Demo script | `docs/demo-script.md` |
| Decisions made during the build | `docs/decisions-log.md` |
| Things to check by hand at the end | `docs/final-checks.md` |
| Catalog coverage audit | `docs/catalog-audit.md` |
| Research Lab (in the app) | http://localhost:5173/lab |

## Tests

With the database running:
```powershell
.\scripts\test.ps1
```
This runs the engine, pipeline and API tests (the API tests use a separate `cinematch_test` database\nthat is rebuilt on every run), the 12 scenario tests of spec section 16 (on the real catalog, with\nthrowaway users that are deleted afterwards) and the website tests.

## Ports

| What | Address |
| --- | --- |
| Website (Vite) | http://localhost:5173 |
| API (FastAPI) | http://127.0.0.1:8010 (change with `API_PORT` in `.env`) |
| PostgreSQL | localhost:5432 |