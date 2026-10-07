# Phase 2: The Data Pipeline (viva notes)

## 1. What was built

An offline pipeline (`pipeline/`) that turns three public data sources into the CineMatch catalog
and the training data. Run it with `scripts\data.ps1` (or `python -m pipeline.run_all`).

| Step | What it does | Result on 2026-10-08 |
|---|---|---|
| 1 | Download MovieLens 32M and check its MD5 checksum | 32 million ratings, md5 verified |
| 2 | Collect candidate films for parts A, B and C | 16,012 A + 4,544 B + 911 C candidates |
| 3 | One TMDB call per candidate (details, credits, keywords, certifications, logos) | ~19,900 films cached |
| 4 | Awards from Wikidata in bulk queries | 15,513 award rows for 3,933 catalog films |
| 5 | Metadata gate, final cut, cleaning, dominant colors, report per language | 13,442 films |
| 6 | Ratings sample, scaled to 1-10 | 30,000 users, 4.61 million ratings |
| 7 | Time splits and new-movie holdout | 70/10/20 per user; 500 holdout films |
| 8 | Content features (TF-IDF + structured blocks) | 13,442 x 111,902 sparse matrix |
| 12 | Load the catalog into PostgreSQL | movies, genres, people, credits, keywords, awards |

Every download is cached on disk, so re-running the pipeline never fetches anything twice.

## 2. The catalog in three parts

- **Part A, MovieLens films (9,995).** Films with enough MovieLens ratings to train collaborative
  filtering. We started at 50 ratings and raised the threshold until part A landed near 10,000:
  the final rule is **at least 154 ratings**.
- **Part B, curated international (2,973).** TMDB "discover" per language (Hindi, Tamil, Telugu,
  Malayalam, Kannada, Bengali, Marathi, Korean, Japanese, Spanish, French, German, Italian,
  Mandarin, Cantonese, Portuguese, Turkish, Persian), most-voted first, at most 300 per language.
- **Part C, New & Notable (474).** Releases from the last 18 months (2025-04-08 to 2026-10-08)
  with at least 110 TMDB votes.

Parts B and C have **no MovieLens ratings**. Only their content (genres, story, cast, director),
their TMDB vote counts and live feedback on our site can recommend them. That is the
**new-item cold-start problem**, and the content-based model is how we solve it.

## 3. The metadata gate (why some films are dropped)

A film enters the catalog only if TMDB has: a poster, an English overview of at least 15 words,
at least one genre, a director, and at least three cast members. 862 candidates failed, mostly
for too few cast members (365) or a too-short overview (342); 162 no longer exist on TMDB.

We **drop** a film instead of filling in missing fields. Inventing data would make the
recommendations and the explanations dishonest.

## 4. Ratings preparation and splits

- MovieLens stars (0.5 to 5.0) are multiplied by 2, giving the CineMatch 1-10 scale. Half stars
  map exactly to whole numbers, so nothing is lost.
- We keep ratings on part-A films only, keep users with at least 20 of them, and sample
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
A language must have at least 150 films so a new user who picks it gets a full list. Twelve
languages qualify (English, French, Italian, Japanese, Spanish, Mandarin, Korean, German,
Portuguese, Hindi, Cantonese, Turkish). Tamil has 132, so it is just below the line.