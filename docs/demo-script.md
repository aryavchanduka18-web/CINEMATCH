# Demo script (spec section 17)

Before the demo: start Docker Desktop, then `scripts\db.ps1`, `scripts\api.ps1`, `scripts\web.ps1`,
open http://localhost:5173 (or the live site, https://cinematch-16hy.onrender.com; open it a few
minutes early, the free plan sleeps after 15 minutes). The prepared account is `demo@cinematch.local` (password in `.env`,
`DEMO_PASSWORD`; rebuild it with `.\.venv\Scripts\python.exe -m pipeline.demo_accounts`).

| # | What to do | Account | What to say |
|---|---|---|---|
| 1 | Open the site in a private window (new guest), pick 5 crime thrillers, languages, genres | Fresh | Cold start: 5 onboarding picks, 0 real actions, so the stage is still "cold" and onboarding + content + popularity drive the list. |
| 2 | Rate *Prisoners* 9, *Se7en* 10, *Zodiac* 9, go back Home | Fresh | 3 real actions: the stage becomes "warming" (show it in the Lab User Inspector); fold-in updated the profile without retraining. |
| 3 | Open a recommended film, scroll to "Why you're seeing this" | Fresh | Reasons come only from sources that gave at least 20% of the score, with real evidence. |
| 4 | Sign in as the demo account, find "Because You Liked ..." | Prepared | Item-based CF, adjusted cosine with shrinkage. |
| 5 | "People With Your Taste Loved" | Prepared | User-based CF, Pearson with significance weighting. |
| 6 | Switch Familiar -> Discover | Prepared | MMR reranking; show the diversity chart in the Lab. |
| 7 | Hidden Gems and New & Notable | Prepared | Popularity bias and new-movie cold start (part C has no MovieLens ratings). |
| 8 | Open /lab | either | Model table with CIs, cold-start chart, new-movie panel, weights, User Inspector, catalog audit. |
| 9 | Open a franchise film (John Wick, Iron Man) | either | "More from John Wick" lists every part in release order; Iron Man also gets "More from Marvel". 470 missing franchise parts were added without changing the evaluation (fingerprint check). |
| 10 | Search *Sholay*, open it, scroll to More Like This | either | Similarity only: content + genre + language + era, the same for every user. |
| 11 | Click a cast photo | either | Person page: their films the recommender scores highest first, then the filmography. |
| 12 | On a film page, "Recommendation confidence" | Prepared | Model agreement from the spread of the models' ranks; Technical details map the words to SVD, ALS, CF, TF-IDF. |
| 13 | Home: Tune (move "More adventurous" up), Why? on the hero, dislike a film and pick a reason | Prepared | The engine re-ranks with the sliders; Why? shows what each model contributed; each dislike reason changes something real. |

## Answers to Aryav's questions

- **The hero banner on Home** is the top 5 of the hybrid recommender (`OnlineEngine.home`: `hero = picks[:5]`),
  not My List. My List, ratings, likes and dislikes feed the recommender as signals.
- **Bottom tab bar on phones, top bar on a laptop**: by design. Under 768 px the tabs move to a floating pill
  at the bottom, within thumb reach.

Backup: record the full demo once with the Windows Game Bar (Win + G) in case the laptop or network fails.