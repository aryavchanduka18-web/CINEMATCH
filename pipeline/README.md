# Offline data pipeline

Builds the CineMatch catalog and training data (spec section 4.5). Run from the repo root:

```powershell
.\.venv\Scripts\python.exe -m pipeline.run_all            # every implemented step, in order
.\.venv\Scripts\python.exe -m pipeline.run_all --from 3   # resume from step 3
.\.venv\Scripts\python.exe -m pipeline.run_all --only 12  # one step
```

Every download is cached under `data/raw/`, so re-running never fetches anything twice.
Outputs: `data/processed/` (catalog, ratings, splits, reports) and `artifacts/` (features).
Neither folder is committed: the MovieLens license forbids redistribution.