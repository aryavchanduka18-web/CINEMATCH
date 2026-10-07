"""Step 4: awards (won / nominated) for catalog candidates from Wikidata, in bulk SPARQL queries.

Films are matched by TMDB movie id (P4947). Award received = P166, nominated for = P1411,
year = point in time (P585) on the statement. `award` is the award series the prize belongs
to (P361 "part of", e.g. "Academy Awards") when Wikidata has it, and `category` is the
specific prize (e.g. "Academy Award for Best Picture"). Without a series, `award` is the prize.
"""
import hashlib
import json
import re
import time

import httpx
import pandas as pd

from pipeline.common import PROCESSED, WIKIDATA_DIR, get_logger

log = get_logger("04_awards")
ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "CineMatchCollegeProject/0.1 (https://github.com/aryavchanduka18-web/CINEMATCH; student recommender-systems project)"
BATCH = 300

QUERY = """
SELECT ?tmdb ?st ?kind ?award ?awardLabel ?series ?seriesLabel ?year WHERE {
  VALUES ?tmdb { %s }
  ?film wdt:P4947 ?tmdb .
  { ?film p:P166 ?st . ?st ps:P166 ?award . BIND("won" AS ?kind) }
  UNION
  { ?film p:P1411 ?st . ?st ps:P1411 ?award . BIND("nominated" AS ?kind) }
  OPTIONAL { ?st pq:P585 ?date . BIND(YEAR(?date) AS ?year) }
  OPTIONAL { ?award wdt:P361 ?series . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""


def run_batch(client: httpx.Client, ids: list[int]) -> list[dict]:
    key = hashlib.sha1(",".join(map(str, ids)).encode()).hexdigest()[:16]
    cache = WIKIDATA_DIR / f"awards_{key}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    query = QUERY % " ".join(f'"{i}"' for i in ids)
    for attempt in range(6):
        try:
            resp = client.post(ENDPOINT, data={"query": query})
        except httpx.TransportError:
            time.sleep(5 * 2 ** attempt)
            continue
        if resp.status_code == 200:
            rows = resp.json()["results"]["bindings"]
            WIKIDATA_DIR.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(rows), encoding="utf-8")
            time.sleep(1.0)  # be polite between batches
            return rows
        wait = float(resp.headers.get("retry-after", 5 * 2 ** attempt))
        log.info("wikidata HTTP %s, retrying in %.0fs", resp.status_code, wait)
        time.sleep(min(wait, 120))
    raise RuntimeError("Wikidata query kept failing")


PRIZE_PATTERN = re.compile(r"^(?P<award>.+?\b(?:Awards?|Prize|Globe|Oscar))\s+for\s+(?P<category>.+)$")


def split_prize(prize: str, series: str | None, known_series: set[str]) -> tuple[str, str | None]:
    """'Academy Award for Best Actor' -> ('Academy Awards', 'Best Actor').

    The award name comes from the Wikidata series ("part of") when present, else from the
    prize label, matched to a known series name when one exists ('Academy Award' -> 'Academy Awards').
    """
    m = PRIZE_PATTERN.match(prize)
    if m:
        base = m.group("award")
        award = series or next((s for s in (base + "s", base) if s in known_series), base)
        return award, m.group("category")
    return (series, prize) if series else (prize, None)


def to_rows(bindings: list[dict]) -> pd.DataFrame:
    def val(b, k):
        return b[k]["value"] if k in b else None

    known_series = {val(b, "seriesLabel") for b in bindings if val(b, "seriesLabel")}
    rows = []
    for b in bindings:
        award, category = split_prize(val(b, "awardLabel"), val(b, "seriesLabel"), known_series)
        rows.append({
            "tmdb_id": int(val(b, "tmdb")),
            "statement": val(b, "st"),
            "award": award,
            "category": category,
            "year": int(val(b, "year")) if val(b, "year") else None,
            "result": val(b, "kind"),
            "wikidata_id": val(b, "award").rsplit("/", 1)[-1],
        })
    cols = ["tmdb_id", "statement", "award", "category", "year", "result", "wikidata_id"]
    df = pd.DataFrame(rows, columns=cols)
    if df.empty:
        return df.drop(columns="statement")
    # A prize can be "part of" several series: keep one row per Wikidata statement.
    df = df.sort_values(["statement", "award"]).drop_duplicates("statement")
    # Drop unlabeled items (the label falls back to the Q-id) and a nomination that was also won.
    df = df[~df["award"].str.fullmatch(r"Q\d+")]
    df = df.assign(won=df["result"].eq("won")).sort_values("won", ascending=False)
    df = df.drop_duplicates(["tmdb_id", "wikidata_id", "year"])
    df["year"] = df["year"].astype("Int16")
    return df.drop(columns=["statement", "won"]).sort_values(["tmdb_id", "year"]).reset_index(drop=True)

def main() -> None:
    cand = pd.read_csv(PROCESSED / "catalog_candidates.csv")
    ids = sorted(cand["tmdb_id"].unique().tolist())
    n_batches = (len(ids) + BATCH - 1) // BATCH
    bindings: list[dict] = []
    headers = {"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"}
    with httpx.Client(headers=headers, timeout=120) as client:
        for i, start in enumerate(range(0, len(ids), BATCH)):
            bindings += run_batch(client, ids[start:start + BATCH])
            if i % 10 == 0:
                log.info("batch %d/%d", i + 1, n_batches)
    awards = to_rows(bindings)
    awards.to_parquet(PROCESSED / "awards.parquet", index=False)
    log.info("%d award rows for %d films (%d won, %d nominated)", len(awards), awards["tmdb_id"].nunique(),
             (awards["result"] == "won").sum(), (awards["result"] == "nominated").sum())


if __name__ == "__main__":
    main()