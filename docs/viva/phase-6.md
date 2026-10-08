# Phase 6: Final evaluation and experiments (viva notes)

Numbers: [docs/phase-6-results.md](../phase-6-results.md). Produced by `pipeline/11_evaluate.py`.

## 1. The final run
All settings were chosen on validation. For the final run every model is retrained on train +
validation and evaluated **once** on the test split (the newest 20% of each user's ratings), with
the same 5,000-user sample for every model and full ranking.

## 2. The experiments
1. **Model comparison:** the table of section 12.2 with 95% bootstrap confidence intervals.
   We only claim a difference when the intervals do not overlap.
2. **Cold-start users:** pretend we know only k = 0, 2, 5, 10, 20 of a user's ratings, with and
   without simulated onboarding (5 picked films). The gap between the two lines is what onboarding
   is worth; the hybrid uses the stage weights that match k.
3. **New movies:** 500 films had all ratings removed from training. Hit rate@50 = how often a
   held-out film the user later rated 7+ appears in their top 50. CF models cannot score a film
   nobody rated, so they get 0; the content model finds them; random would be about 0.5%.
4. **Diversity trade-off:** MMR lambda from 0.5 to 1.0. Lower lambda = more varied lists, slightly
   lower NDCG. The three Discovery Modes are points on this curve.
5. **Calibration:** does "80% match" mean that about 80% of such films are liked? Checked on test.
6. **Global time cutoff:** everything after one date is the test set. A second, harder check
   (future users and films), reported for robustness.

## 3. How to read the main result honestly
The hybrid is at least as accurate as the best single model (implicit ALS) and adds what single
models lack: it works for cold users, it can recommend new films, it explains itself and it lets the
user trade accuracy for variety. Where the confidence intervals overlap we say "comparable", not
"better". That is the claim in spec section 1.

## 4. Likely examiner questions
**Q1. Why does popularity beat SVD on ranking?** SVD is trained to predict rating values of films
people chose to rate; ranking the whole catalog also needs to know which films people engage with,
which popularity and ALS capture. SVD still wins on RMSE, the job it was trained for.

**Q2. What is a bootstrap confidence interval?** Resample the 5,000 users with replacement 1,000
times, recompute the average each time, and take the middle 95% of those averages.

**Q3. Why is the cold-start hybrid better with onboarding?** Five picked films give the content model
and ALS a taste profile before the user has done anything; without them only popularity is left.

**Q4. Why do CF models score zero on new movies?** They learn only from ratings; a film with no
ratings has no neighbors and no factor vector. That is the new-item cold-start problem, and it is why
the hybrid keeps a content source.

**Q5. Why use the test set only once?** Every extra look at the test set is a chance to tune to it by
accident, which would make the reported numbers optimistic.