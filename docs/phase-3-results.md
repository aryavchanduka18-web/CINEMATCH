# Phase 3 results: baseline models

Generated from `artifacts/metrics/validation_baselines.json` by `pipeline/report_validation.py`.

Validation split, 5,000 evaluated users (fixed sample, seed 42), full ranking over 9,495 part-A films, relevant = rating >= 7/10. Brackets are 95% bootstrap confidence intervals over users. The test split is not used yet.

| Model | P@10 | R@10 | MAP@10 | NDCG@10 | MAE | RMSE |
|---|---|---|---|---|---|---|
| Bias baseline | n/a | n/a | n/a | n/a | 1.297 [1.266, 1.329] | 1.719 [1.681, 1.756] |
| Popularity | 0.0375 [0.0352, 0.0397] | 0.0611 [0.0568, 0.0654] | 0.0286 [0.0262, 0.0309] | 0.0571 [0.0533, 0.0605] | n/a | n/a |
| Content-based | 0.0140 [0.0129, 0.0152] | 0.0242 [0.0216, 0.0270] | 0.0116 [0.0101, 0.0131] | 0.0235 [0.0213, 0.0257] | n/a | n/a |
| Item CF | 0.0553 [0.0525, 0.0579] | 0.0900 [0.0845, 0.0949] | 0.0482 [0.0450, 0.0512] | 0.0892 [0.0847, 0.0934] | 1.270 [1.244, 1.298] | 1.714 [1.678, 1.754] |
| User CF | 0.0518 [0.0492, 0.0542] | 0.0915 [0.0866, 0.0968] | 0.0459 [0.0428, 0.0491] | 0.0853 [0.0810, 0.0898] | 1.266 [1.239, 1.295] | 1.692 [1.656, 1.727] |

| Model | Coverage | Intra-list diversity | Novelty (bits) | Long-tail share | Mean popularity percentile |
|---|---|---|---|---|---|
| Popularity | 1.2% | 0.676 | 1.68 | 0.0% | 99.9 |
| Content-based | 46.8% | 0.622 | 6.86 | 52.1% | 67.6 |
| Item CF | 13.4% | 0.686 | 2.52 | 0.3% | 98.8 |
| User CF | 5.5% | 0.700 | 2.23 | 0.0% | 99.3 |

| Model | Tuned settings | Runtime (s) |
|---|---|---|
| Bias baseline | reg_item=10, reg_user=5 | 2.9 |
| Popularity | m=1000000 | 8.0 |
| Content-based | ngram_max=2, weights_preset=cast_director, thin_text_scale=1.0, like_min=7, dislike_max=5 | 109.9 |
| Item CF | shrinkage=3200, neighbors=50, beta=50.0 | 186.8 |
| User CF | min_overlap=2, k=50, beta=50.0, significance=50 | 236.3 |

Peak memory of the run: 1,457 MB.
