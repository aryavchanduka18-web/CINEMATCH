# Phase 5 results: hybrid engine

Generated from `artifacts/metrics/validation_hybrid.json`. Validation split, simulated users (4,885): onboarding = 5 earliest films rated 8+, cold = onboarding + 0-2 ratings, warming = onboarding + 3-10, established = full history.

## Tuned blend weights per stage

| Stage | Popularity | Content | Item CF | User CF | SVD | ALS | NDCG@10 |
|---|---|---|---|---|---|---|---|
| cold | 0.5 | 0.3 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0640 |
| warming | 0.1 | 0.3 | 0.0 | 0.4 | 0.0 | 0.2 | 0.0721 |
| established | 0.0 | 0.1 | 0.1 | 0.1 | 0.0 | 0.7 | 0.1204 |

## Match % calibration (fitted on validation)

| Stage | Pairs | Share rated 7+ | ECE | Match % range |
|---|---|---|---|---|
| cold | 14,257 | 77.2% | 0.0132 | 70-92% |
| warming | 16,720 | 77.8% | 0.0122 | 72-93% |
| established | 20,880 | 80.2% | 0.0259 | 75-88% |

## Discovery Modes (established users)

| Mode | NDCG@10 | Intra-list diversity | Coverage |
|---|---|---|---|
| familiar | 0.1205 [0.1153, 0.1260] | 0.834 | 11.4% |
| balanced | 0.1199 [0.1149, 0.1252] | 0.844 | 11.5% |
| discover | 0.1177 [0.1127, 0.1229] | 0.855 | 11.8% |
