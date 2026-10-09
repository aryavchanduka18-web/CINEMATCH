# Final checks for Aryav

Things that need a human look at the end. Nothing here blocks the build.

**Result: Aryav went through every item on 2026-10-08 and confirmed that everything is correct.**

| # | Area | What to check | Where |
|---|---|---|---|
| 1 | Data | Follow-up spot-check: 6 films from the catalog expansion (3 Hollywood, 3 Tamil/Malayalam) | `docs/phase-2-spotcheck.md`, second table |
| 2 | Catalog | Kannada has 133 films (needs 150 for onboarding) even at the lowest vote floor of 5. Accept, or allow Kannada below 150? | `docs/catalog-audit.md` |
| 4 | Catalog | Golden Raspberry (worst-film) awards are in the awards data; they will be excluded from the Awards rail | `docs/decisions-log.md` || 5 | Laptop | The laptop went to sleep for about 5 hours during the evaluation run (07:50-12:57) and the job just paused. Keep it plugged in with the lid open during long pipeline runs, or set Windows "Sleep: never" while plugged in | Windows power settings |
| 6 | Results | Read the honest headline: hybrid and ALS have overlapping confidence intervals on test NDCG@10 (comparable accuracy); the hybrid adds cold start, new movies, explanations and Discovery Mode | `docs/phase-6-results.md` |
| 7 | Website | Look at every page at desktop, tablet and phone width (Home, Movie, Discover, Genres, My List, Activity, Lab) and say what you'd like changed | http://localhost:5173 |
| 8 | Demo | Try the demo account (`demo@cinematch.local`, password = `DEMO_PASSWORD` in `.env`) and rehearse `docs/demo-script.md` once | `docs/demo-script.md` |
| 9 | Demo | Record the backup video of the demo (Win + G) | - |
| 10 | Tests | Scenario tests 6 (My List raises similar films) and 7 (Discover is more diverse) currently assert "not worse"; decide if stricter thresholds are wanted | `api/scenarios/test_scenarios.py` || 11 | Lab | Shilling result to discuss: SVD is extremely exposed (1% average attack -> 96% of users see the target); the simple detector only works for small attacks and removes 1,000-1,900 real users. Reported as is | `docs/report/report.md` section 7 |
| 12 | Report | Read `docs/report/report.md` end to end and adjust the wording to your style before submitting | `docs/report/report.md` |
