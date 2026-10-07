# Phase 1: The Foundation (viva notes)

## 1. The three parts and how they talk

CineMatch has three running parts:

1. **The website** (React). This is what the user sees in the browser: the pages, the tabs, the movie cards.
2. **The API** (FastAPI, Python). This is the "brain" in the middle. The website asks it questions like
   "give me recommendations for user 5" and it answers with data (JSON).
3. **The database** (PostgreSQL). This is the long-term memory: the movies, the users, their ratings, their lists.

How they talk:

```
Browser (React website)  --HTTP request /api/...-->  FastAPI  --SQL query-->  PostgreSQL
                         <--JSON response--------           <--rows-------
```

The website never talks to the database directly. Only the API does. This keeps passwords and
business rules in one safe place.

In Phase 1 there is one real endpoint, `/api/health`. It runs `select 1` on the database, which
proves the whole chain works: website -> API -> database -> back.

There is also a fourth piece, the **recommendation engine** (`cinematch_engine`). It is a Python
package, not a running server. Both the API and the offline training pipeline import it, so the
same code is used for training and for serving.

## 2. Why these technologies

- **FastAPI**: Python is the language of machine learning (NumPy, pandas, scikit-learn), so the
  API can call the recommendation code directly. FastAPI is fast, checks request data
  automatically, and creates interactive API documentation at `/docs` for free.
- **React**: lets us build the site from reusable pieces (a card, a rail of cards, a nav bar).
  The homepage is many rails of the same card, so reuse matters. TypeScript catches mistakes
  before the code runs.
- **PostgreSQL**: a reliable, free relational database. Our data is naturally relational
  (users rate movies, movies have genres and cast). It also has features we use directly:
  full-text search for the search box, arrays (a movie's languages), JSON (recommendation
  explanations), and case-insensitive text for emails.
- **Docker**: runs PostgreSQL in a container, so we do not install it on Windows. Anyone can
  start the exact same database version with one command.

## 3. "Current state" tables vs the interactions log

We store user behaviour in two different ways on purpose.

**Current-state tables** (`ratings`, `reactions`, `user_movie_list`, `watched`): one row per
user and movie, holding the *answer right now*. If I rate a movie 6 and later change it to 9,
the `ratings` row just says 9. These tables answer simple questions fast: "what is my rating?",
"what is in my list?".

**The interactions log** (`interactions`): append-only, a new row for every event, never edited.
Rating 6 and then 9 gives two rows. Opening a movie page, adding to the list, removing from the
list: every action is a row with a time.

Why keep both?

- The page needs the current answer quickly. Rebuilding it from thousands of events every time would be slow.
- The recommender needs the history. Implicit feedback (views, list adds, removals) only exists as
  events, each with a weight (for example `like = 4`, `dislike = -5`, `detail_view = 0.5`).
- The history lets us count a user's real behaviour to decide whether they are a cold, warming or
  established user, and to evaluate the system later.

Onboarding picks are kept in their own table. They tell us the user's taste, but they are not
behaviour, so they do not move the user out of the cold-start stage.

## 4. What Alembic migrations are

A migration is a small Python file that describes one change to the database structure, for
example "create the movies table" or "add a column". Alembic keeps them in order and records in
the database which ones have already been applied.

Running `scripts\migrate.ps1` (`alembic upgrade head`) brings any database up to the latest
structure. Benefits: the schema lives in git with the code, every computer gets exactly the same
tables, and changes can be undone (`downgrade`). Our first migration creates all 17 tables.
A test checks that the migration and the Python models describe exactly the same schema.

## 5. Why MovieLens ratings stay outside the database

MovieLens is a public research dataset with millions of ratings from thousands of users. We use it
to **train and evaluate** the models offline. It stays as files in `data/` because:

- It is only read in bulk by the training pipeline. Loading files straight into pandas and NumPy
  is much faster than querying millions of rows from a database.
- Those users are not real users of our site. Mixing them into the `users` and `ratings` tables would
  confuse the website's data with research data.
- The database stays small and fast for what the website really needs.
- The evaluation stays reproducible: the same files give the same train and test split every time.

What does go into the database from MovieLens is a summary per movie (`ml_rating_count`,
`ml_rating_mean`, `rating_hist`) so the website can show it.

## 6. Likely examiner questions

**Q1. Why not let React talk to PostgreSQL directly?**
The browser is not trusted. Database passwords would be exposed and anyone could run any query.
The API checks every request and only exposes safe operations.

**Q2. What is the difference between explicit and implicit feedback in your schema?**
Explicit feedback is the user telling us their opinion directly: `ratings` (1 to 10) and
`reactions` (like or dislike). Implicit feedback is what we infer from behaviour: page views,
list adds and removals, marking as watched. Both are logged in `interactions` with weights.

**Q3. Why is the interactions table append-only?**
So we never lose history. The order and timing of events is itself a signal, and we need the full
history to train, to judge whether a user is cold or established, and to evaluate.

**Q4. What happens to a user's data when the user is deleted?**
All user-owned tables use `ON DELETE CASCADE`, so their ratings, reactions, list, watched,
preferences, interactions and recommendation logs are deleted automatically. A test checks this.

**Q5. How do you know the setup works?**
Automated tests: the health endpoint returns `db: ok` against a real database; the migration
creates all tables; the migration matches the models; full-text search works; deleting a user
cascades. There is also a website test for the status line. `scripts\test.ps1` runs everything.