# Final checks for Aryav

Things that need a human look at the end. Nothing here blocks the build.

| # | Area | What to check | Where |
|---|---|---|---|
| 1 | Data | Follow-up spot-check: 6 films from the catalog expansion (3 Hollywood, 3 Tamil/Malayalam) | `docs/phase-2-spotcheck.md`, second table |
| 2 | Catalog | Kannada has 127 films (needs 150 for onboarding) even at the lowest vote floor of 5. Accept, or allow Kannada below 150? | `docs/catalog-audit.md` |
| 3 | Catalog | 5 famous US films are excluded because their TMDB English overview is under 15 words: Furious 7, The Big Short, It Follows, Little Women (2019), The Passion of the Christ. Keep the rule, or make an exception? | `docs/catalog-audit.md` |
| 4 | Catalog | Golden Raspberry (worst-film) awards are in the awards data; they will be excluded from the Awards rail | `docs/decisions-log.md` |