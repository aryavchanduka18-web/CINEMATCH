# Phase 5: The hybrid engine (viva notes)

Numbers: `artifacts/metrics/validation_hybrid.json` (summarized in docs/phase-5-results.md).

## 1. The pipeline for one user (a cascade)
1. **Profile:** the user's ratings, likes/onboarding picks and implicit signals. The **stage** comes
   from the behavioral count b only (distinct films rated, liked, disliked, listed or watched):
   cold (0-2), warming (3-10), established (11+). Onboarding picks never count toward b.
2. **Candidates:** the top 50 films from each of the six sources (popularity, content, item CF,
   user CF, SVD, ALS), merged into one pool of up to 300.
3. **Filters:** films already rated, watched or disliked, disliked genres, and films already shown
   higher on the page are removed.
4. **Normalization:** each source's scores become a 0-1 percentile rank among the films it proposed.
   A source that did not propose a film gives it 0. (A 4.2 from SVD and a 0.31 from content are
   on different scales, so they are never added raw.)
5. **Blend:** final = sum of weight[stage][source] x normalized score. The weights depend on the
   stage: a **switching hybrid** inside a **weighted hybrid** inside a **cascade**.
6. **Match %:** a one-feature logistic regression per stage turns the blend score into the
   probability that the user rates the film 7/10 or higher. Capped at 99, never stretched.
7. **Rerank (MMR):** from the top 100, pick films one at a time, trading relevance against similarity
   to the films already picked, plus a novelty bonus. Discovery Mode sets the trade-off.
8. **Explanations:** each film keeps its per-source contributions; a reason is shown only for a
   source that gave at least 20% of the final score, with real evidence, at most 3 reasons.

## 2. How the stage weights were tuned
Every MovieLens user has 20+ ratings, so real cold users do not exist offline. We **simulate** them
like the live site: onboarding = the user's 5 earliest films rated 8+, then cold = onboarding +
0-2 more ratings, warming = onboarding + 3-10, established = full history. For each stage, a grid
search over all weight combinations (steps of 0.1, summing to 1) picks the weights with the best
validation NDCG@10.

## 3. MMR in one line
next = argmax [ lambda x relevance - (1 - lambda) x (similarity to the most similar film already
picked) + beta x novelty ]. Familiar: lambda 0.95, beta 0. Balanced: 0.75, 0.05.
Discover: 0.55, 0.20, plus a small boost for other languages and rare genres.

## 4. Surprise Me and For Tonight
- **Surprise Me:** unseen candidates with Match % >= 60 and community rating >= 6.5, whose main genre
  is outside the user's top 3 and that are below the 70th popularity percentile; one is drawn at
  random, weighted by Match %.
- **For Tonight** is the **knowledge-based (constraint-based)** recommender: mood, runtime, language
  and genres become hard filters using the rule table `moods.yaml` (the knowledge base), the
  survivors are ranked by the hybrid score, and if nothing matches the constraints are relaxed in a
  fixed order (runtime, genres, mood, language), and the user is told what was relaxed.

## 5. Likely examiner questions

**Q1. Why percentile ranks instead of raw scores?**
Each model has its own scale (predicted ratings, cosine similarities, dot products). Percentiles put
them on one 0-1 scale without assuming anything about their distribution.

**Q2. Why do the weights change with the stage?**
With few ratings, CF and SVD know almost nothing about the user, so content and popularity carry the
list; as ratings accumulate, the collaborative models become reliable. The tuned weights show this.

**Q3. Is Match % a real probability?**
Yes: it is calibrated with logistic regression on validation and checked on test (predicted vs
observed share of liked films per bin). We do not stretch it to look impressive.

**Q4. Why MMR?**
Pure relevance often returns ten near-identical films. MMR keeps the list relevant but avoids
near-duplicates, and Discovery Mode lets the user choose how adventurous it is.

**Q5. Which part is the knowledge-based recommender?**
For Tonight: explicit rules (mood -> genres/keywords) plus constraint relaxation. No ML model.