"""Tiny hand-made TMDB detail responses for tests."""
import copy

GOOD = {
    "id": 101, "imdb_id": "tt0000101", "title": "Test Film", "original_title": "Test Film",
    "overview": "A detective in a rainy city hunts a patient killer whose crimes follow the seven deadly sins one by one.",
    "release_date": "1995-09-22", "runtime": 127, "original_language": "en", "adult": False,
    "spoken_languages": [{"iso_639_1": "en"}], "production_countries": [{"iso_3166_1": "US"}],
    "poster_path": "/p.jpg", "backdrop_path": "/b.jpg", "tagline": "Seven deadly sins.",
    "production_companies": [{"name": "New Line"}], "vote_count": 20000, "status": "Released",
    "genres": [{"id": 80, "name": "Crime"}, {"id": 53, "name": "Thriller"}],
    "keywords": {"keywords": [{"name": "Serial Killer"}, {"name": "detective"}]},
    "credits": {
        "cast": [{"id": i, "name": f"Actor {i}", "character": f"C{i}", "order": i, "profile_path": None}
                 for i in range(1, 21)],
        "crew": [{"id": 900, "name": "Dir One", "job": "Director", "department": "Directing"},
                 {"id": 901, "name": "Writer One", "job": "Screenplay", "department": "Writing"},
                 {"id": 900, "name": "Dir One", "job": "Director", "department": "Directing"}],
    },
    "release_dates": {"results": [
        {"iso_3166_1": "US", "release_dates": [{"type": 3, "certification": "R", "release_date": "1995-09-22"}]},
        {"iso_3166_1": "IN", "release_dates": [{"type": 3, "certification": "A", "release_date": "1996-01-01"}]},
    ]},
    "images": {"logos": [{"iso_639_1": "fr", "file_path": "/fr.png"}, {"iso_639_1": "en", "file_path": "/en.png"}]},
}


def good(**changes) -> dict:
    d = copy.deepcopy(GOOD)
    d.update(changes)
    return d