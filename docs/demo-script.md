# Demo script (spec section 17)

Before the demo: start Docker Desktop, then `scripts\db.ps1`, `scripts\api.ps1`, `scripts\web.ps1`,
open http://localhost:5173. The prepared account is `demo@cinematch.local` (password in `.env`,
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

Backup: record the full demo once with the Windows Game Bar (Win + G) in case the laptop or network fails.