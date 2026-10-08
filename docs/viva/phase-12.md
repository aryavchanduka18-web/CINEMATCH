# Phase 12: Advanced modules (viva notes)

All three are **lab only**: the website never runs them live.

## Shilling attack and defense
A shilling attack is fake profiles created to push (or bury) a film. We inject two classic attacks
against 5 little-known films, at 1%, 3% and 5% of the user base:
- **Average attack:** each fake profile rates the target 10/10 and about 5% of the catalog close to
  those films' real averages, so it looks ordinary.
- **Bandwagon attack:** fake profiles also give 10/10 to a few very popular films, to look like
  many real users.
We measure the **prediction shift** (how much the targets' predicted rating rose) and the **hit
ratio** (share of real users who now get a target in their top 10) for user CF, item CF and SVD.
**Defense:** three classic detection features (RDMA, similarity to nearest neighbors, rating
variance) combine into an anomaly score; the most anomalous profiles are removed and the models
retrained. We report the cost honestly: precision, recall and real users wrongly removed.

## Taste map
PCA projects the 100-dimensional SVD film vectors to 2D. A user is placed by projecting their
folded-in vector with the same projection ("You"). PCA, not t-SNE, because t-SNE cannot add a new
point without redrawing the map. The two axes explain only a few percent of the variance, so the map
is a rough picture of the model, not a recommender.

## Neural Collaborative Filtering
NeuMF combines a dot-product part (GMF) and a small neural network (MLP) over user and film
embeddings, trained on positives (7+) with 4 random negatives each. Evaluated with exactly the same
full-ranking protocol. It is not served on the website: it has one vector per training user and no
cheap fold-in for new users. If it does not beat ALS, we say so (Rendle et al., 2020 found that
well-tuned matrix factorization often beats NCF).

## Likely examiner questions
**Q1. Which CF type is most vulnerable to shilling?** See the table: user CF is usually hit hardest,
because fake profiles become "neighbors".
**Q2. What does the defense cost?** Some real users are flagged and removed; we report how many.
**Q3. Why PCA for the map?** It is a fixed linear projection, so new users can be placed consistently.
**Q4. Why not serve NCF?** No fold-in: a new user would need retraining.
**Q5. Is deep learning always better?** No. On this data the simpler implicit ALS is a strong baseline.