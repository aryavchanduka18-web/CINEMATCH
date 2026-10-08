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


def boost_floor(pool_votes: pd.Series, already: int, target: int, start: int, floor: int, cap: int) -> int:
    """Highest vote floor (start, start-1, ..., floor) at which `already` + the films kept from the
    pool (at most `cap`) reaches `target`. Returns `floor` if even that is not enough."""
    for v in range(start, floor - 1, -1):
        if already + min(int((pool_votes >= v).sum()), cap) >= target:
            return v
    return floor


def select(gated: pd.DataFrame, cfg: dict, window_start, window_end) -> tuple[pd.DataFrame, dict]:
    """gated: one row per candidate (tmdb_id, part, ml_rating_count, tmdb_vote_count,
    discover_language, release_date, status, passed). Returns (catalog rows, chosen settings)."""
    ok = gated[gated["passed"]]

    a_pool = ok[ok["part"] == "A"]
    t_a = pick_threshold(a_pool["ml_rating_count"], cfg["part_a"]["target"], cfg["part_a"]["min_ratings"])
    a = a_pool[a_pool["ml_rating_count"] >= t_a]

    pb = cfg["part_b"]
    b_pool = (ok[(ok["part"] == "B") & ~ok["tmdb_id"].isin(a["tmdb_id"])]
              # Ties on votes are broken by TMDB id so the per-language cap is deterministic.
              .sort_values(["tmdb_vote_count", "tmdb_id"], ascending=[False, True]).drop_duplicates("tmdb_id"))
    boost_floors = {}
    for lang in pb.get("boost_languages", []):
        in_lang = b_pool["discover_language"] == lang
        already = int((a["original_language"] == lang).sum())
        v = boost_floor(b_pool.loc[in_lang, "tmdb_vote_count"], already, pb["boost_target"],
                        pb["min_votes"], pb["boost_floor"], pb["max_per_language"])
        boost_floors[lang] = v
        b_pool = b_pool[~in_lang | (b_pool["tmdb_vote_count"] >= v)]
    b = b_pool.groupby("discover_language", group_keys=False).head(pb["max_per_language"])

    c_pool = ok[(ok["part"] == "C") & ~ok["tmdb_id"].isin(a["tmdb_id"]) & ~ok["tmdb_id"].isin(b["tmdb_id"])]
    c_pool = c_pool[(c_pool["status"] == "Released")
                    & (pd.to_datetime(c_pool["release_date"]).dt.date >= window_start)
                    & (pd.to_datetime(c_pool["release_date"]).dt.date <= window_end)]
    pc = cfg["part_c"]
    t_c = pick_part_c_threshold(c_pool["tmdb_vote_count"], pc["start_min_votes"], pc["target_min"],
                                pc["target_max"], pc["pool_min_votes"])
    c = c_pool[c_pool["tmdb_vote_count"] >= t_c]

    d = pd.DataFrame(columns=ok.columns)
    if "hollywood" in cfg:
        d = hollywood_pick(ok[ok["part"] == "D"], cfg["hollywood"], window_end,
                           exclude=set(a["tmdb_id"]) | set(b["tmdb_id"]) | set(c["tmdb_id"]))

    catalog = pd.concat([a, b, c, d], ignore_index=True).drop_duplicates("tmdb_id")
    return catalog, {"part_a_min_ratings": t_a, "part_c_min_votes": t_c, "part_b_boost_vote_floors": boost_floors}


def hollywood_rule(df: pd.DataFrame, h: dict) -> pd.Series:
    """Part D rule: votes >= min_vote_count, OR an old classic, OR part of a franchise collection."""
    votes = df["tmdb_vote_count"].fillna(0)
    year = df["year"].astype("float").fillna(9999)          # unknown year is never a "classic"
    in_collection = df["in_collection"].fillna(False).astype(bool)
    return ((votes >= h["min_vote_count"])
            | ((votes >= h["classic_min_vote_count"]) & (year < h["classic_before_year"]))
            | ((votes >= h["collection_min_vote_count"]) & in_collection))


def hollywood_pick(pool: pd.DataFrame, h: dict, window_end, exclude: set) -> pd.DataFrame:
    """US productions (co-productions count) that are released, meet the rule, and are not in A/B/C."""
    released = (pool["status"] == "Released") & (pd.to_datetime(pool["release_date"]).dt.date <= window_end)
    keep = pool["us_production"].fillna(False).astype(bool) & released & hollywood_rule(pool, h) & ~pool["tmdb_id"].isin(exclude)
    return pool[keep].drop_duplicates("tmdb_id")