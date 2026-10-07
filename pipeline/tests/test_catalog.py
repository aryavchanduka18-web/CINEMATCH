from pipeline.catalog import certification, gate_failures, parse_credits, parse_movie
from pipeline.tests.fixtures import good


def test_complete_film_passes_gate():
    assert gate_failures(good()) == []


def test_gate_rules_each_fail():
    assert gate_failures(good(poster_path=None)) == ["no_poster"]
    assert gate_failures(good(overview="Too short to describe the film.")) == ["short_overview"]
    assert gate_failures(good(genres=[])) == ["no_genre"]
    no_dir = good()
    no_dir["credits"] = {**no_dir["credits"], "crew": [c for c in no_dir["credits"]["crew"] if c["job"] != "Director"]}
    assert gate_failures(no_dir) == ["no_director"]
    few = good()
    few["credits"] = {**few["credits"], "cast": few["credits"]["cast"][:2]}
    assert gate_failures(few) == ["few_cast"]


def test_overview_of_exactly_15_words_passes():
    assert gate_failures(good(overview=" ".join(["word"] * 15))) == []
    assert gate_failures(good(overview=" ".join(["word"] * 14))) == ["short_overview"]


def test_backdrop_is_optional():
    assert gate_failures(good(backdrop_path=None)) == []


def test_certification_prefers_india_then_us():
    assert certification(good()) == "A"
    us_only = good(release_dates={"results": [good()["release_dates"]["results"][0]]})
    assert certification(us_only) == "R"
    assert certification(good(release_dates={"results": []})) is None


def test_parse_movie_fields():
    m = parse_movie(good())
    assert m["year"] == 1995 and m["original_language"] == "en"
    assert m["logo_path"] == "/en.png"
    assert m["genres"] == ["Crime", "Thriller"]
    assert m["keywords"] == ["detective", "serial killer"]


def test_parse_credits_top15_cast_directors_writers_no_duplicates():
    rows = parse_credits(good())
    roles = [r["role"] for r in rows]
    assert roles.count("cast") == 15
    assert roles.count("director") == 1          # the duplicate crew entry is collapsed
    assert roles.count("writer") == 1
    assert len({(r["tmdb_person_id"], r["role"]) for r in rows}) == len(rows)