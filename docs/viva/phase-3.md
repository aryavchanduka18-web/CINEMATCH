# Phase 3: Baseline models and the evaluation code (viva notes)

The numbers are in [docs/phase-3-results.md](../phase-3-results.md). This page explains what each
model does, why it was built that way, and how it is measured.

## 1. How we measure (the evaluation protocol)

- **Data:** 30,000 MovieLens users. For each user, the oldest 70% of ratings train the models,
  the next 10% (validation) tune them, and the newest 20% (test) are kept for one final run later.
- **Relevant film:** one the user rated 7/10 or higher.
- **Evaluated users:** a fixed sample of 5,000 users who have at least one relevant validation film,
  drawn once with seed 42. Every model is scored on exactly the same users.
- **Full ranking:** each model ranks *every* film in the evaluation universe (9,495 part-A films)
  that the user has not rated in training, and we look at the top 10. We do **not** use the shortcut
  "hide one relevant film among 100 random ones": Krichene and Rendle (2020) showed that sampled
  metrics can even change which model looks best.
- **Confidence intervals:** we resample the 5,000 users 1,000 times (bootstrap) and report the
  middle 95% of the results. Two models are only called different if their intervals do not overlap.

### Metrics in plain English
- **Precision@10:** of the 10 films shown, the share the user liked.
- **Recall@10:** of all the films the user liked, the share that made the top 10.
- **MAP@10:** rewards putting liked films *near the top*: average of the precision at each hit.
- **NDCG@10:** like MAP, but each hit is worth 1/log2(position + 1), so position 1 counts most;
  divided by the best possible score, so 1.0 means a perfect list.
- **MAE / RMSE:** how far predicted ratings are from real ones (only for models that predict a rating).
  RMSE punishes big mistakes more.
- **Coverage:** the share of the catalog that appears in anyone's top 10.
- **Intra-list diversity:** 1 minus the average content similarity of the 10 films (higher = more varied).
- **Novelty:** the average of -log2(share of users who rated the film): rare films score high.
- **Long-tail share / popularity percentile:** how often the list uses less-known films.

## 2. The models

### Bias baseline (the reference for MAE/RMSE)
prediction = global mean + user bias + film bias. A tough user gets a negative bias, a loved film a
positive one. Biases are regularized so a user with 3 ratings is not pushed to the extremes.

### Popularity (Bayesian average)
score = v/(v+m) x R + m/(v+m) x C, where R is the film's mean rating, v its number of ratings,
C the global mean and m a constant. A film with very few ratings is pulled toward the global mean,
so one 10/10 cannot put an unknown film at the top. **m is tuned on validation.** Everyone gets the
same list. This is the baseline every personal model must beat.

### Content-based
Each film is a vector: TF-IDF of its story (overview + keywords + tagline) plus one-hot blocks for
genres, language, country, director, top-5 cast and studio. A user's taste profile is the weighted
average of films they liked (7+, weight rating - 6) minus the weighted average of films they
disliked (5 or less). A film's score is its cosine similarity to the profile.
**Tuned:** the block weights and whether TF-IDF uses single words or also word pairs.
It is the only model that can recommend a film nobody has rated yet.

### User-based CF
Find users with similar taste, recommend what they liked. Similarity is the **Pearson correlation**
on films both users rated, multiplied by **min(n, 50)/50** where n is the number of films in common
(significance weighting): a correlation built on 3 shared films is weak evidence. Prediction =
the user's own mean + the similarity-weighted average of the neighbors' ratings, each taken
relative to that neighbor's mean (so a harsh rater's 6 counts like a generous rater's 8).
**Tuned:** k (number of neighbors) and the minimum overlap.
Memory: the 30,000 x 30,000 similarity matrix is never built; neighbors are computed in batches of
500 users and only the top k are kept.

### Item-based CF
Find films that are rated alike, recommend films similar to ones the user liked. Similarity is the
**adjusted cosine**: ratings are first centered on each user's mean (removing "this person rates
everything high"), then compared over the users who rated both films. **Shrinkage** multiplies it by
n/(n + lambda), n = users who rated both, so a similarity from a handful of users is trusted less.
Each film keeps its top neighbors. **Tuned:** lambda and the number of neighbors.

## 3. Why these choices
- **Full ranking instead of sampled negatives:** closer to what the website does (rank the whole
  catalog) and does not distort the model comparison.
- **Significance weighting and shrinkage:** both fix the same weakness, similarity estimated from
  too little data.
- **Bayesian average:** stops films with one or two perfect ratings from dominating "Most Loved".
- **Validation only:** every setting is chosen on validation; the test set stays untouched so the
  final numbers are honest.

## 4. Likely examiner questions

**Q1. Why does popularity score so well?**
Most people like the famous films, and the top-10 lists are judged on what users actually rated
next, which is biased toward famous films. That is why we also report coverage, novelty and
long-tail share: popularity shows almost no variety and almost no long-tail films.

**Q2. Why NDCG and not just precision?**
Precision ignores order. NDCG rewards putting the liked films at the top of the list, which is
what a user sees first.

**Q3. What is significance weighting?**
Multiplying a user-user correlation by min(n, 50)/50: two users who agree on 3 films are not
treated as soulmates.

**Q4. Why not use the test set to choose settings?**
Then the test score would be tuned to the test set and would overstate real performance. The test
set is used once, at the end.

**Q5. Why do the CF models predict ratings only slightly better (or worse) than the bias baseline?**
Rating prediction and ranking are different jobs. Most of the variation in ratings is explained by
"this user rates high" and "this film is liked", which is exactly what the bias baseline captures;
neighbors add a little on top. We optimize ranking (NDCG) because the site shows lists, not numbers.