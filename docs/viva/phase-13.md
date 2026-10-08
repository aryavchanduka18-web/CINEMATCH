# Phase 13: Final validation and demo (viva notes)

## What was validated
- Every unit test (metrics checked against hand-computed values, models on tiny data, fold-in,
  hybrid logic), the pipeline tests (gate, x2 scaling, split order, holdout, loader idempotency),
  the API tests, the web tests, and the **12 scenario tests of spec section 16** on the real catalog.
- The final evaluation ran once on the test split (`docs/phase-6-results.md`).
- The website was checked at desktop and phone widths (no horizontal overflow, bottom tab bar on
  phones, nothing hover-only on touch devices).

## The demo (docs/demo-script.md)
1. Fresh account: onboarding with 5 crime thrillers. The user is "cold" (5 onboarding picks, 0
   behavioral actions), so popularity, content, user CF and ALS (from the picks) drive the list.
2. Rate *Prisoners*, *Se7en*, *Zodiac*: 3 real actions -> "warming"; fold-in updates the profile
   without retraining; the User Inspector in the Lab shows the stage and the new weights.
3. "Why you're seeing this": reasons only from sources that gave 20%+ of the score.
4-7. Prepared account (40 ratings): Because You Liked (item CF), People With Your Taste (user CF),
   Familiar -> Discover (MMR), Hidden Gems and New & Notable (popularity bias, new-movie cold start).
8. The Research Lab: every number read from `artifacts/`.

## Likely examiner questions
**Q1. Is the hybrid better than ALS?** On accuracy their confidence intervals overlap, so we call
them comparable. The hybrid is better overall: it handles new users and new films, explains itself,
and offers diversity control. That is the claim we make.

**Q2. How do you know the explanations are honest?** Each reason comes from a source that contributed
at least 20% of the film's score, and its evidence is real data; scenario test 12 checks this.

**Q3. What happens if the website gets a new film?** It enters the catalog with content features and
TMDB popularity; content and popularity can recommend it immediately; collaborative models start using
it after the next retraining with site feedback (`pipeline/export_site_feedback.py` in the spec).

**Q4. How long would retraining take?** About 15 minutes for every model on the laptop (step 9),
plus about 9 minutes for the stage weights (step 10).

**Q5. What would you do next?** Retrain with site feedback, A/B test the stage weights using the
recommendation logs, and add more Indian-language films as TMDB coverage grows.