# Phase 4: Matrix factorization (viva notes)

Numbers: [docs/phase-4-results.md](../phase-4-results.md).

## 1. The idea
Collaborative filtering with neighbors (Phase 3) compares users or films directly. Matrix
factorization instead learns a short list of hidden "taste dimensions" (for example, how dark,
how funny, how arty a film is). Every user and every film gets a vector of, say, 50 numbers, and
the predicted liking is how well the two vectors line up (their dot product). Nobody tells the model
what the dimensions mean; it discovers them from the ratings.

## 2. Funk SVD (explicit ratings)
prediction = global mean + user bias + film bias + p_user . q_film

The vectors and biases are learned by **stochastic gradient descent**: go through the known
ratings many times (epochs), and nudge the numbers a little (the learning rate) to reduce the
error, with a penalty on large numbers (regularization) so the model does not memorize noise.
Only known ratings are used; missing ratings are not treated as zeros.
**Tuned on validation:** number of factors, epochs, learning rate, regularization.
Library: scikit-surprise `SVD`. It powers the "Based On Your Ratings" rail.

## 3. Implicit ALS (implicit feedback)
Weighted alternating least squares (Hu, Koren and Volinsky, 2008). Every user-film pair has a
**preference** p (1 if there is a positive signal, else 0) and a **confidence** c = 1 + alpha x w,
where w is the signal strength. Offline, w = rating - 6 for ratings of 7 or more (a 10/10 is a
stronger signal than a 7/10). On the live site, w comes from the event weights (like +4, list add +3,
watched +2, detail view +0.5 ...). The model minimizes the confidence-weighted squared error
between p and x_user . y_film. **Alternating:** fix the film vectors and the best user vectors
have an exact formula; then fix users and solve for films; repeat.
**Tuned:** factors, regularization, alpha. Library: `implicit`.

## 4. Fold-in: new users without retraining
Retraining on every rating is too slow for a website. With the film vectors fixed, a single
user's vector has a closed-form solution from only that user's ratings or signals:
- SVD: [p, b_user] = (X^T X + lambda I)^-1 X^T y, with X = [q_film, 1] and y = rating - mean - film bias.
- ALS: x = (Y^T Y + Y^T (C_u - I) Y + lambda I)^-1 Y^T C_u p_u.
This is a tiny linear system (about 50 x 50), solved in milliseconds per request.

**Check:** we removed 20 users from training, retrained, folded them back in from their own
ratings, and compared with the model that saw them in training (top-10 overlap, NDCG@10, RMSE).
See the results page.

## 5. Likely examiner questions

**Q1. Why can SVD have a better RMSE but a worse NDCG than simpler models?**
It is trained to predict the rating of films people chose to rate, not to rank all films. Ranking
the whole catalog also needs knowing which films a person would even look at, which popularity and
ALS capture better.

**Q2. What is the difference between explicit and implicit feedback?**
Explicit = the user says how much they liked it (a rating). Implicit = we infer interest from
behavior (opening, saving, watching). Implicit data has no real negatives: not clicking may mean
"not interested" or "never saw it", which is why ALS uses confidence weights instead of ratings.

**Q3. Why fold-in instead of retraining?**
Retraining takes minutes; fold-in takes milliseconds and gives nearly the same user vector, so a
new rating changes the recommendations on the next page load.

**Q4. What does alpha do in ALS?**
It sets how much more a strong signal counts than an unobserved pair. Large alpha trusts the
signals more.

**Q5. Why both SVD and ALS?**
They use different evidence. SVD learns from rating values (including low ones); ALS learns from
what people engage with. The hybrid (Phase 5) blends them, and each also has its own role on the
site.