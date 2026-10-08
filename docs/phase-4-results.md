# Phase 4 results: matrix factorization

Generated from `artifacts/metrics/validation_mf.json` by `pipeline/report_validation.py`.

Validation split, 5,000 evaluated users (fixed sample, seed 42), full ranking over 9,495 part-A films, relevant = rating >= 7/10. Brackets are 95% bootstrap confidence intervals over users. The test split is not used yet.

| Model | P@10 | R@10 | MAP@10 | NDCG@10 | MAE | RMSE |
|---|---|---|---|---|---|---|
| Funk SVD | 0.0154 [0.0142, 0.0166] | 0.0265 [0.0237, 0.0296] | 0.0119 [0.0106, 0.0134] | 0.0253 [0.0232, 0.0277] | 1.224 [1.197, 1.253] | 1.633 [1.598, 1.668] |
| Implicit ALS | 0.0716 [0.0690, 0.0744] | 0.1313 [0.1254, 0.1377] | 0.0600 [0.0566, 0.0634] | 0.1149 [0.1101, 0.1194] | n/a | n/a |

| Model | Coverage | Intra-list diversity | Novelty (bits) | Long-tail share | Mean popularity percentile |
|---|---|---|---|---|---|
| Funk SVD | 33.1% | 0.828 | 6.24 | 51.1% | 73.9 |
| Implicit ALS | 11.9% | 0.704 | 3.06 | 0.1% | 98.0 |

| Model | Tuned settings | Runtime (s) |
|---|---|---|
| Funk SVD | n_factors=100, n_epochs=30, lr_all=0.005, reg_all=0.05, fold_in_reg=reg_all x number of the user's ratings | 324.2 |
| Implicit ALS | factors=64, regularization=0.3, alpha=1.0, iterations=15, signal=rating - 6 for ratings >= 7, confidence=1 + alpha * signal | 118.2 |

Peak memory of the run: 1,457 MB.

## Fold-in check

A few users are removed from training, the model is retrained, and the users are folded back in from their own ratings. Compared with the model that saw them in training:

| Model | Users | Top-10 overlap | NDCG@10 full training | NDCG@10 fold-in | RMSE full | RMSE fold-in |
|---|---|---|---|---|---|---|
| Funk SVD | 20 | 57% | 0.0064 | 0.0032 | 1.391 | 1.387 |
| Implicit ALS | 20 | 94% | 0.0513 | 0.0508 | nan | n/a |
