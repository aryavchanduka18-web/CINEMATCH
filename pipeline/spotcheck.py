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


if __name__ == "__main__":
    main()