# Phases 7-10: The website (viva notes)

## 1. How a page is built
1. The browser (React) calls the API (FastAPI) with a session cookie. Every visitor is a user:
   on the first visit a **guest** account is created; registering later keeps everything the guest did.
2. For the home page the API reads the user's current state from PostgreSQL (ratings, likes,
   dislikes, list, watched, onboarding answers, recent events), builds their profile, and asks the
   engine (the same `cinematch_engine` code that was evaluated offline) for the whole page at once.
3. The engine scores the **whole product catalog** (about 14,000 films): content and popularity score
   every film; item CF, user CF, SVD and ALS score the MovieLens films. It then builds the hero, Top
   Picks and the other rails, removes duplicates and hides rails with fewer than 8 films.
4. Every shown card is written to `recommendation_logs` with its rail, position, scores and reason.

## 2. Feedback
- **Explicit:** star rating (5 stars with half steps = 1-10), like, dislike.
- **Implicit:** opening a film page (once per film per day), Quick View, search clicks, list adds and
  removals, marking watched. Hover is never logged.
- Every action writes the **current-state** table (fast reads) and the **interactions** log (history).
- Changes take effect on the next page load: nothing personal is cached.

## 3. Design decisions
- Large 16:9 cards, 2-3 per row on desktop (Aryav's decision), the title over a dark gradient or the
  film's own TMDB logo. Hover (desktop only, after a short delay) shows actions and a one-line reason;
  touch devices get a visible chevron instead, never hover-only controls.
- Hero: blurred artwork tinted with the film's dominant color (computed offline with Pillow, because
  reading pixels in the browser from another site is blocked). No Play button: CineMatch recommends,
  it does not stream.
- One accent color (crimson) only for Match %, stars and focus rings; no gradients, neon or glow.

## 4. Likely examiner questions
**Q1. Where does the recommendation happen, browser or server?** On the server, in the same engine
package that was evaluated; the browser only displays results.

**Q2. How does a guest become a user?** The guest is a real database row; registering adds an email
and password to that row, so all ratings and lists stay.

**Q3. How do you stop the same film appearing twice on the home page?** The server plans the whole
page in one call and keeps a set of films already placed; each rail skips them.

**Q4. Why log impressions (recommendation_logs)?** To measure click-through per rail and per model
later, and to show in the lab exactly what a user was shown and why.

**Q5. Why is a new user still "cold" after onboarding?** Onboarding picks are preferences, not
behavior. The stage counts only real actions (ratings, likes, dislikes, list adds, watched).