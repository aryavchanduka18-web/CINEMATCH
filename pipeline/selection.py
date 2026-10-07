"""Final catalog cut (spec 4.2), as pure functions over the gated candidate table."""
import pandas as pd


def pick_threshold(counts: pd.Series, target: int, floor: int) -> int:
    """Smallest rating-count threshold >= floor whose catalog size is closest to `target`."""
    best_t, best_gap = floor, None
    for t in sorted(set(counts[counts >= floor].tolist()) | {floor}):
        gap = abs(int((counts >= t).sum()) - target)
        if best_gap is None or gap < best_gap:
            best_t, best_gap = t, gap
    return int(best_t)


def pick_part_c_threshold(votes: pd.Series, start: int, lo: int, hi: int, floor: int) -> int:
    """Start at `start` votes; raise it while more than `hi` films qualify, lower it (not below
    `floor`) while fewer than `lo` qualify."""
    t = start
    while (votes >= t).sum() > hi:
        t += 10
    while (votes >= t).sum() < lo and t - 10 >= floor:
        t -= 10
    return t


def select(gated: pd.DataFrame, cfg: dict, window_start, window_end) -> tuple[pd.DataFrame, dict]:
    """gated: one row per candidate (tmdb_id, part, ml_rating_count, tmdb_vote_count,
    discover_language, release_date, status, passed). Returns (catalog rows, chosen settings)."""
    ok = gated[gated["passed"]]

    a_pool = ok[ok["part"] == "A"]
    t_a = pick_threshold(a_pool["ml_rating_count"], cfg["part_a"]["target"], cfg["part_a"]["min_ratings"])
    a = a_pool[a_pool["ml_rating_count"] >= t_a]

    b_pool = ok[(ok["part"] == "B") & ~ok["tmdb_id"].isin(a["tmdb_id"])]
    b = (b_pool.sort_values("tmdb_vote_count", ascending=False)
         .drop_duplicates("tmdb_id")
         .groupby("discover_language", group_keys=False)
         .head(cfg["part_b"]["max_per_language"]))

    c_pool = ok[(ok["part"] == "C") & ~ok["tmdb_id"].isin(a["tmdb_id"]) & ~ok["tmdb_id"].isin(b["tmdb_id"])]
    c_pool = c_pool[(c_pool["status"] == "Released")
                    & (pd.to_datetime(c_pool["release_date"]).dt.date >= window_start)
                    & (pd.to_datetime(c_pool["release_date"]).dt.date <= window_end)]
    pc = cfg["part_c"]
    t_c = pick_part_c_threshold(c_pool["tmdb_vote_count"], pc["start_min_votes"], pc["target_min"],
                                pc["target_max"], pc["pool_min_votes"])
    c = c_pool[c_pool["tmdb_vote_count"] >= t_c]

    catalog = pd.concat([a, b, c], ignore_index=True).drop_duplicates("tmdb_id")
    return catalog, {"part_a_min_ratings": t_a, "part_c_min_votes": t_c}