# Phase 2: The Data Pipeline (viva notes)

## 1. What was built

An offline pipeline (`pipeline/`) that turns three public data sources into the CineMatch catalog
and the training data. Run it with `scripts\data.ps1` (or `python -m pipeline.run_all`).

| Step | What it does | Result on 2026-10-08 |
|---|---|---|
| 1 | Download MovieLens 32M and check its MD5 checksum | 32 million ratings, md5 verified |
| 2 | Collect candidate films for parts A, B, C and D | 16,012 A + 6,221 B + 911 C + 5,007 D candidates |
| 3 | One TMDB call per candidate (details, credits, keywords, certifications, logos) | every candidate cached |
| 4 | Awards from Wikidata in bulk queries | 15,634 award rows for the catalog |
| 5 | Metadata gate, final cut, cleaning, dominant colors, report per language, catalog audit | 13,987 films (14,292 after the gate was relaxed, section 3) |
| 6 | Ratings sample, scaled to 1-10 | 30,000 users, 4.61 million ratings |
| 7 | Time splits and new-movie holdout | 70/10/20 per user; 500 holdout films |
| 8 | Content features (TF-IDF + structured blocks) | 13,987 x 115,181 sparse matrix (+305 rows served, section 3) |
| 12 | Load the catalog into PostgreSQL | movies, genres, people, credits, keywords, awards |

Every download is cached on disk, so re-running the pipeline never fetches anything twice.

## 2. The catalog in four parts

- **Part A, MovieLens films (9,995).** Films with enough MovieLens ratings to train collaborative
  filtering. We started at 50 ratings and raised the threshold until part A landed near 10,000:
  the final rule is **at least 154 ratings**.
- **Part B, international enrichment (3,302).** TMDB "discover" per language (Hindi, Tamil, Telugu,
  Malayalam, Kannada, Bengali, Marathi, Korean, Japanese, Spanish, French, German, Italian,
  Mandarin, Cantonese, Portuguese, Turkish, Persian), most-voted first, at most 300 per language.
  Tamil, Telugu, Malayalam and Kannada use a lower vote minimum (Aryav, 2026-10-08) so they can reach
  the 150-film onboarding rule: the pipeline picks the highest minimum that gets each language to 150
  films (Tamil 44 votes, Telugu 27, Malayalam 31). Kannada stops at the floor of 5 votes with 127 films (133 with the relaxed gate),
  because TMDB simply has no more Kannada films that pass the gate.
- **Part C, recent releases (474).** Releases from the 18 months before the catalog build date
  (2025-04-08 to 2026-10-08) with at least 110 TMDB votes. MovieLens 32M stops in October 2023.
- **Part D, Hollywood enrichment (216).** Famous US films missing from A, B and C. A US production
  (co-productions count) qualifies with at least 2,000 TMDB votes, or at least 1,000 votes if it was
  released before 1990 or belongs to a TMDB collection (a franchise). Most famous US films are already
  in part A, so D is mainly the films released between mid-2023 and April 2025 (96 of the 216), which are
  too new for MovieLens and too old for part C: for example Dune: Part Two, Deadpool & Wolverine,
  Inside Out 2 and Wicked. The catalog audit (docs/catalog-audit.md) measures coverage: with the
  relaxed gate (section 3) **all 1,000 of the 1,000 most-voted US films are in the catalog** (995 with
  the original gate).

The **product catalog** (what the website shows) is all four parts. The **evaluation universe** (what
the models are compared on) is only part A, so a bigger catalog never makes the model comparison unfair.

Parts B, C and D have **no MovieLens ratings**. Only their content (genres, story, cast, director),
their TMDB vote counts and live feedback on our site can recommend them. That is the
**new-item cold-start problem**, and the content-based model is how we solve it.

## 3. The metadata gate (why some films are dropped)

A film enters the catalog only if TMDB has: a poster, an English overview of at least 10 words,
at least one genre, a director, and at least one cast member. 280 eligible candidates still fail;
162 of them no longer exist on TMDB.

The first build used a stricter gate (15 words, 3 cast members). It dropped 920 candidates, among them
famous films with a short TMDB overview or a short listed cast (The Graduate, Annie Hall, The Big
Short, Furious 7, Little Women 2019, the Wallace & Gromit shorts), so Aryav relaxed it on 2026-10-08.
To keep the evaluation exactly as it was, step 5 still makes the cut with the original gate first and
then adds the 305 films that only the relaxed gate lets in (235 A, 68 B, 2 C), using the same
thresholds. Those films are flagged `relaxed_gate` and are **not** in the evaluation backbone: the
ratings sample, splits, trained models and results did not change. They are served through content
and popularity (`pipeline/extend_serving.py` adds their content rows with the vocabulary learned from
the original films, plus new columns for people only they have, so every existing row stays identical), like parts B, C and D.

We **drop** a film instead of filling in missing fields. Inventing data would make the
recommendations and the explanations dishonest.

## 4. Ratings preparation and splits

- MovieLens stars (0.5 to 5.0) are multiplied by 2, giving the CineMatch 1-10 scale. Half stars
  map exactly to whole numbers, so nothing is lost.
- We keep ratings on the evaluation backbone only (part A films that passed the original gate), keep users with at least 20 of them, and sample
  **30,000 users** with a fixed random seed (42). All models train on the same sample, so the
  comparison is fair. A fixed seed means anyone re-running the pipeline gets the same sample.
- **Per-user time split:** for each user, the oldest 70% of their ratings are training data,
  the next 10% validation, the newest 20% test. This copies real life: we predict a user's
  future from their past, never the other way round.
- **Global time cutoff (robustness check):** every rating after 2018-08-14 is test data
  (about 20% of the sample).
- **New-movie holdout:** 500 part-A films (5%) have all their ratings removed from training.
  Later we test whether content features alone can still recommend them.
- The test set is used **once**, at the end of tuning.

## 5. Content features

Each film becomes one long vector made of blocks:
- **Text:** TF-IDF of overview + keywords + tagline. TF-IDF gives a word a high weight when it is
  frequent in this film but rare across the catalog ("heist" says more than "man").
- **Structured blocks:** genres, original language, production country, director, top-5 cast,
  studio, one column per value.

Each block is scaled to length 1 and given a weight (all equal for now; Phase 3 tunes them).
The cosine similarity of two films is then a weighted mix of "similar story", "same genres",
"same director" and so on.

## 6. What goes into PostgreSQL

The catalog (movies, genres, people, credits, keywords, awards), plus per-film MovieLens
aggregates for display: rating count, mean on the 1-10 scale, and the 10-bucket histogram. The
loader is **idempotent**: running it twice gives exactly the same rows, never duplicates.
MovieLens ratings themselves stay in Parquet files (see the Phase 1 notes for why).

Search: the `search_vector` column holds the title, director and cast, so searching "Nolan"
finds Christopher Nolan's films.

## 7. Likely examiner questions

**Q1. Why split by time instead of randomly?**
A random split lets the model peek at a user's future ratings while predicting their past, which
makes results look better than they would be in real use. A time split only lets the model learn
from the past, like the live site.

**Q2. Why did you remove 500 films from training?**
To measure new-movie cold start honestly. Those films have real ratings we can test against,
but the models never saw them, so only content features can find them.

**Q3. Why 30,000 users and not all of MovieLens?**
It is enough data to train and compare every model fairly, and it fits in the laptop's memory.
Every model uses the same sample, so the comparison stays fair.

**Q4. Why drop films with missing metadata instead of filling the gaps?**
Content-based recommendation and our explanations depend on that metadata. A made-up overview or
director would produce wrong recommendations and fake reasons.

**Q5. Why does onboarding only offer some languages?**
A language must have at least 150 films so a new user who picks it gets a full list. Fifteen
languages qualify, including Hindi, Tamil, Telugu and Malayalam. Kannada has 133 films even at the
lowest vote floor, so it is honestly reported as below the line rather than padded with weak data.