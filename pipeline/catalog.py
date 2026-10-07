"""Turn one raw TMDB detail JSON into catalog fields, and the metadata gate (spec 4.2).

Pure functions only (no I/O), so they are unit-tested in pipeline/tests.
"""
import re
from datetime import date

MIN_OVERVIEW_WORDS = 15
MIN_CAST = 3
MAX_CAST_STORED = 15
WRITER_JOBS = {"Screenplay", "Writer", "Story", "Novel", "Author"}

GATE_REASONS = ("no_poster", "short_overview", "no_genre", "no_director", "few_cast")


def overview_words(text: str | None) -> int:
    return len(re.findall(r"\w+", text or ""))


def directors(detail: dict) -> list[dict]:
    return [c for c in detail.get("credits", {}).get("crew", []) if c.get("job") == "Director"]


def gate_failures(detail: dict) -> list[str]:
    """Return why a film fails the metadata gate (empty list = it passes).

    Gate: poster, English overview >= 15 words, >= 1 genre, a director, >= 3 cast members.
    A backdrop is optional. Missing data is never filled in: the film is dropped instead.
    """
    reasons = []
    if not detail.get("poster_path"):
        reasons.append("no_poster")
    if overview_words(detail.get("overview")) < MIN_OVERVIEW_WORDS:
        reasons.append("short_overview")
    if not detail.get("genres"):
        reasons.append("no_genre")
    if not directors(detail):
        reasons.append("no_director")
    if len(detail.get("credits", {}).get("cast", [])) < MIN_CAST:
        reasons.append("few_cast")
    return reasons


def certification(detail: dict) -> str | None:
    """India first, else US, else None. Prefers the theatrical (type 3) release in that country."""
    by_country = {r["iso_3166_1"]: r["release_dates"] for r in detail.get("release_dates", {}).get("results", [])}
    for country in ("IN", "US"):
        entries = by_country.get(country, [])
        ranked = sorted(entries, key=lambda e: (e.get("type") != 3, e.get("release_date", "")))
        for entry in ranked:
            cert = (entry.get("certification") or "").strip()
            if cert:
                return cert
    return None


def english_logo(detail: dict) -> str | None:
    for logo in detail.get("images", {}).get("logos", []):
        if logo.get("iso_639_1") == "en":
            return logo["file_path"]
    return None


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_movie(detail: dict) -> dict:
    """Movie-level catalog fields from a TMDB detail response."""
    raw_date = detail.get("release_date") or None
    release = date.fromisoformat(raw_date) if raw_date else None
    return {
        "tmdb_id": int(detail["id"]),
        "imdb_id": detail.get("imdb_id") or None,
        "title": detail.get("title") or detail.get("original_title"),
        "original_title": detail.get("original_title"),
        "overview": (detail.get("overview") or "").strip() or None,
        "release_date": release,
        "year": release.year if release else None,
        "runtime_min": detail.get("runtime") or None,
        "original_language": (detail.get("original_language") or "").lower() or None,
        "spoken_languages": sorted({l["iso_639_1"].lower() for l in detail.get("spoken_languages", []) if l.get("iso_639_1")}),
        "countries": [c["iso_3166_1"] for c in detail.get("production_countries", [])],
        "certification": certification(detail),
        "poster_path": detail.get("poster_path"),
        "backdrop_path": detail.get("backdrop_path"),
        "tagline": (detail.get("tagline") or "").strip() or None,
        "studios": [c["name"] for c in detail.get("production_companies", [])],
        "logo_path": english_logo(detail),
        "tmdb_vote_count": detail.get("vote_count"),
        "status": detail.get("status"),
        "genres": [g["name"] for g in detail.get("genres", [])],
        "keywords": sorted({k["name"].strip().lower() for k in detail.get("keywords", {}).get("keywords", [])}),
    }


def parse_credits(detail: dict) -> list[dict]:
    """Directors, writers and the top 15 cast, one row per (person, role)."""
    tmdb_id = int(detail["id"])
    credits = detail.get("credits", {})
    rows, seen = [], set()

    def add(person: dict, role: str, character=None, order=None):
        key = (person["id"], role)
        if key in seen:
            return
        seen.add(key)
        rows.append({
            "tmdb_id": tmdb_id, "tmdb_person_id": person["id"], "name": person["name"],
            "profile_path": person.get("profile_path"), "role": role,
            "character": character, "credit_order": order,
        })

    for c in sorted(credits.get("cast", []), key=lambda c: c.get("order", 999))[:MAX_CAST_STORED]:
        add(c, "cast", (c.get("character") or None), c.get("order"))
    for c in credits.get("crew", []):
        if c.get("job") == "Director":
            add(c, "director")
    for c in credits.get("crew", []):
        if c.get("department") == "Writing" and c.get("job") in WRITER_JOBS:
            add(c, "writer")
    return rows