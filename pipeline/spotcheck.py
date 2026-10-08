"""Write docs/phase-2-spotcheck.md: 20 random catalog films for a by-hand check against TMDB."""
import pandas as pd

from pipeline.common import PROCESSED, ROOT, SEED


def main(n: int = 20) -> None:
    movies = pd.read_parquet(PROCESSED / "movies_clean.parquet")
    credits = pd.read_parquet(PROCESSED / "credits_clean.parquet")
    directors = credits[credits["role"] == "director"].groupby("tmdb_id")["name"].apply(", ".join)
    sample = movies.sample(n, random_state=SEED).sort_values(["catalog_part", "year"])
    lines = [
        "# Phase 2 spot-check: 20 random catalog films",
        "",
        f"Drawn with seed {SEED} from `movies_clean.parquet` ({len(movies):,} films). Open each TMDB link and",
        "check the title, year, language and director match. Tick the last column when it does.",
        "",
        "| # | Title | Year | Language | Part | Director | Genres | TMDB | OK? |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, m in enumerate(sample.itertuples(), 1):
        lines.append(
            f"| {i} | {m.title} | {m.year or ''} | {m.original_language} | {m.catalog_part} | "
            f"{directors.get(m.tmdb_id, '')} | {', '.join(m.genres)} | "
            f"[{m.tmdb_id}](https://www.themoviedb.org/movie/{m.tmdb_id}) | |"
        )
    lines += ["", "Parts: A = MovieLens film, B = curated international, C = new & notable.", ""]
    (ROOT / "docs" / "phase-2-spotcheck.md").write_text("\n".join(lines), encoding="utf-8")


ORIGINAL_FLOOR = {"ta": 50, "te": 50, "ml": 50, "kn": 20}


def followup() -> None:
    """Append 6 films from the 2026-10-08 expansion: 3 from part D, 3 from the boosted Indian languages."""
    movies = pd.read_parquet(PROCESSED / "movies_clean.parquet")
    credits = pd.read_parquet(PROCESSED / "credits_clean.parquet")
    directors = credits[credits["role"] == "director"].groupby("tmdb_id")["name"].apply(", ".join)
    boosted = movies[(movies["catalog_part"] == "B") & movies["original_language"].isin(list(ORIGINAL_FLOOR))]
    # Films that only entered because the vote minimum was lowered for these languages.
    boosted = boosted[boosted["tmdb_vote_count"] < boosted["original_language"].map(ORIGINAL_FLOOR)]
    picks = pd.concat([movies[movies["catalog_part"] == "D"].sample(3, random_state=SEED),
                       boosted.sample(3, random_state=SEED)])
    lines = [
        "", "## Follow-up check: 6 films from the 2026-10-08 catalog expansion", "",
        "Drawn with seed 42 from the new films only: 3 from part D (Hollywood enrichment) and 3 from the",
        "expanded Tamil, Telugu, Malayalam and Kannada set. Same check as above.", "",
        "| # | Title | Year | Language | Part | Director | Genres | TMDB | OK? |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, m in enumerate(picks.itertuples(), 1):
        lines.append(
            f"| {i} | {m.title} | {m.year or ''} | {m.original_language} | {m.catalog_part} | "
            f"{directors.get(m.tmdb_id, '')} | {', '.join(m.genres)} | "
            f"[{m.tmdb_id}](https://www.themoviedb.org/movie/{m.tmdb_id}) | |"
        )
    path = ROOT / "docs" / "phase-2-spotcheck.md"
    path.write_text(path.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print(boosted["original_language"].value_counts().to_dict())


if __name__ == "__main__":
    import sys
    followup() if "--followup" in sys.argv else main()