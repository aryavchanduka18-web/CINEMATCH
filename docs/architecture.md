# CineMatch architecture

```
             OFFLINE (pipeline/, run by us)
  MovieLens 32M + TMDB + Wikidata
        -> 01-05 catalog (parts A-D), gate, colors, awards
        -> 06-07 ratings sample (30,000 users), time splits, new-movie holdout
        -> 08    content features
        -> 09    tune + train models on validation      -> artifacts/models/*.json, fitted.npz
        -> 10    stage blend weights + Match % calibration
        -> 11    final evaluation + experiments           -> artifacts/metrics/*.json
        -> 12    load catalog into PostgreSQL
        -> 13-15 shilling, taste map, NCF (lab only)      -> artifacts/lab/*.json

             ONLINE (the website)
  Browser (React, Vite)  <-- /api -->  FastAPI  <-->  PostgreSQL (catalog, users, feedback, logs)
                                          |
                                          +-- loads artifacts/models once (OnlineEngine)
                                          +-- cinematch_engine: profile -> 6 sources -> candidate pool
                                              -> percentile normalization -> stage blend -> Match %
                                              -> MMR / Discovery Mode -> explanations -> rails
```

- `engine/cinematch_engine` is one package used by the pipeline (evaluation) and the API (serving):
  the model that is evaluated is the model that is served.
- Product catalog = parts A-D (~14,000 films). Evaluation universe = part A minus the holdout
  (~9,500 MovieLens films), so comparisons stay fair.
- Explicit feedback: ratings, likes, dislikes. Implicit: views, Quick Views, search clicks, list,
  watched (weights in `engine/cinematch_engine/config/event_weights.yaml`).
- Stage = behavioral count only (onboarding never counts): cold 0-2, warming 3-10, established 11+.