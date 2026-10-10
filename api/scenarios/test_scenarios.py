"""The 12 scenario tests of spec section 16."""
import numpy as np

from conftest import CREATED, films_in, find, genre_ids, genres_of, onboard, top_ids

CRIME_LIKE = {"Crime", "Thriller", "Mystery"}


def test_1_new_user_is_cold_and_gets_relevant_films(client):
    onboard(client, films_in("Crime", "Thriller"), liked=genre_ids("Crime", "Thriller"))
    me = client.get("/api/me").json()["counts"]
    assert (me["stage"], me["onboarding_count"], me["behavioral_count"]) == ("cold", 5, 0)
    home = client.get("/api/recs/home").json()
    ids = top_ids(home)
    g = genres_of(ids)
    share = np.mean([bool(g[i] & CRIME_LIKE) for i in ids])
    assert share >= 0.5, f"only {share:.0%} of the top 20 are crime, thriller or mystery"


def test_2_views_never_change_the_stage_but_3_ratings_do(client):
    onboard(client, films_in("Crime", "Thriller"))
    for m in films_in("Comedy", n=11):
        client.post("/api/events", json={"movie_id": m, "event_type": "detail_view"})
    assert client.get("/api/me").json()["counts"]["stage"] == "cold"
    cold_weights = client.get(f"/api/lab/user/{client.user_id}/candidates").json()["weights"]
    for m in films_in("Drama", n=3):
        client.put(f"/api/ratings/{m}", json={"rating": 8})
    assert client.get("/api/me").json()["counts"]["stage"] == "warming"
    assert client.get(f"/api/lab/user/{client.user_id}/candidates").json()["weights"] != cold_weights


def test_3_established_users_lean_on_collaborative_sources(client):
    onboard(client, films_in("Crime", "Thriller"))
    for m in films_in("Drama", n=16, min_votes=2000):
        client.put(f"/api/ratings/{m}", json={"rating": 8})
    insp = client.get(f"/api/lab/user/{client.user_id}/candidates").json()
    assert insp["stage"] == "established"
    w = insp["weights"]
    assert w["item_cf"] + w["user_cf"] + w["svd"] + w["als"] > 0.5


def test_4_rating_changes_the_list(client):
    onboard(client, films_in("Comedy", "Romance"))
    before = top_ids(client.get("/api/recs/home").json())
    for m in films_in("Crime", "Thriller", n=3):
        client.put(f"/api/ratings/{m}", json={"rating": 10})
    after = top_ids(client.get("/api/recs/home").json())
    assert before != after
    g = genres_of(after)
    assert sum(bool(g[i] & {"Crime", "Thriller"}) for i in after) >= 5


def test_5_disliked_film_and_genre_disappear(client):
    onboard(client, films_in("Crime", "Thriller"), disliked=genre_ids("Horror"))
    home = client.get("/api/recs/home").json()
    victim = top_ids(home)[0]
    client.put(f"/api/reactions/{victim}", json={"value": -1})
    home = client.get("/api/recs/home").json()
    shown = [i["movie"]["id"] for r in home["rails"] for i in r["items"]] + [i["movie"]["id"] for i in home["hero"]]
    assert victim not in shown
    personal = [i["movie"]["id"] for r in home["rails"] if r["key"] in ("top_picks", "different") for i in r["items"]]
    assert not any("Horror" in g for g in genres_of(personal).values())


def test_6_my_list_raises_similar_films(client):
    onboard(client, films_in("Comedy"))
    film = films_in("Animation", "Family", n=1)[0]
    sim = client.get(f"/api/movies/{film}/similar").json()["items"][0]["movie"]["id"]
    before = client.get(f"/api/recs/explain/{sim}").json()["match_pct"] or 0
    client.put(f"/api/list/{film}")
    after = client.get(f"/api/recs/explain/{sim}").json()["match_pct"] or 0
    assert after >= before


def test_7_discover_mode_is_more_diverse(client):
    onboard(client, films_in("Action", "Adventure"))
    for m in films_in("Action", n=12):
        client.put(f"/api/ratings/{m}", json={"rating": 9})
    def diversity(mode):
        home = client.get(f"/api/recs/home?mode={mode}").json()
        ids = top_ids(home, 15)
        g = genres_of(ids)
        return len(set().union(*g.values()))
    assert diversity("discover") >= diversity("familiar")


def test_8_new_movie_can_reach_rails_through_content(client):
    onboard(client, films_in("Action", "Science Fiction"))
    home = client.get("/api/recs/home").json()
    parts = [i["movie"]["catalog_part"] for r in home["rails"] for i in r["items"]]
    assert "C" in parts


def test_9_because_you_liked_prisoners_is_sensible(client):
    prisoners = find("SELECT id FROM movies WHERE title = 'Prisoners' AND year = 2013")
    assert prisoners, "Prisoners (2013) is in the catalog"
    sims = client.get(f"/api/movies/{prisoners[0]}/similar").json()["items"]
    g = genres_of([s["movie"]["id"] for s in sims[:10]])
    assert sum(bool(x & CRIME_LIKE) for x in g.values()) >= 6


def test_10_prepared_account_has_neighbors(client):
    onboard(client, films_in("Crime", "Thriller"))
    for m in films_in("Drama", n=25, min_votes=2000) + films_in("Crime", n=15, min_votes=2000):
        client.put(f"/api/ratings/{m}", json={"rating": 9})
    home = client.get("/api/recs/home").json()
    assert any(r["key"] == "people_like_you" and len(r["items"]) >= 8 for r in home["rails"])


def test_11_no_duplicates_on_home(client):
    onboard(client, films_in("Crime", "Thriller"))
    home = client.get("/api/recs/home").json()
    ids = [i["movie"]["id"] for r in home["rails"] for i in r["items"]] + [i["movie"]["id"] for i in home["hero"]]
    assert len(ids) == len(set(ids))


def test_12_every_reason_has_at_least_20_percent(client):
    onboard(client, films_in("Crime", "Thriller"))
    for m in films_in("Crime", n=5):
        client.put(f"/api/ratings/{m}", json={"rating": 9})
    home = client.get("/api/recs/home").json()
    for item in home["hero"] + [i for r in home["rails"] if r["key"] == "top_picks" for i in r["items"]]:
        for reason in item["reasons"]:
            if reason["source"] not in ("preferences", "rerank"):
                assert reason["share"] >= 0.2

def test_13_more_like_this_is_similarity_alone(client):
    """Sholay: other Hindi films, not Hollywood hits that MovieLens users also rated. The same list for
    every user (nothing personal), and franchise parts surface for a franchise film."""
    sholay = find("SELECT id FROM movies WHERE title = 'Sholay' AND year = 1975")
    assert sholay, "Sholay (1975) is in the catalog"
    sims = client.get(f"/api/movies/{sholay[0]}/similar").json()["items"]
    assert all(s["movie"]["language"] == "hi" for s in sims[:10])
    other = client.__class__(client.app)
    CREATED.append(other.post("/api/auth/guest").json()["id"])
    assert [s["movie"]["id"] for s in other.get(f"/api/movies/{sholay[0]}/similar").json()["items"]] == \
        [s["movie"]["id"] for s in sims]
    iron_man = find("SELECT id FROM movies WHERE title = 'Iron Man' AND year = 2008")
    titles = [s["movie"]["title"] for s in client.get(f"/api/movies/{iron_man[0]}/similar").json()["items"][:5]]
    assert "Iron Man 2" in titles


def test_14_pages_of_films_you_liked_or_rated_open(client):
    """Regression: a film the user liked or rated 8+ used to crash its own explanation (500, shown as
    'Film not found'). Every such page must open, with reasons."""
    films = find("SELECT id FROM movies WHERE title IN ('Inception', 'Zodiac', 'The Pursuit of Happyness') ORDER BY id")
    client.put(f"/api/reactions/{films[0]}", json={"value": 1})
    client.put(f"/api/ratings/{films[1]}", json={"rating": 9})
    client.put(f"/api/ratings/{films[2]}", json={"rating": 10})
    for f in films:
        res = client.get(f"/api/movies/{f}")
        assert res.status_code == 200, f


def test_15_a_disliked_film_leaves_home(client):
    onboard(client, find("SELECT id FROM movies WHERE title IN ('Inception', 'Zodiac', 'Heat', 'Se7en', 'Memento')"))
    first = client.get("/api/recs/home").json()["hero"][0]["movie"]["id"]
    client.put(f"/api/reactions/{first}", json={"value": -1})
    home = client.get("/api/recs/home").json()
    shown = {i["movie"]["id"] for i in home["hero"]} | {i["movie"]["id"] for r in home["rails"] for i in r["items"]}
    assert first not in shown


def test_16_films_you_acted_on_are_not_recommended_back(client):
    """Disliked, rated, liked or watched films leave every Home row, even right after you opened them
    (which puts a film into Continue Exploring)."""
    onboard(client, find("SELECT id FROM movies WHERE title IN ('Inception', 'Zodiac', 'Heat', 'Se7en', 'Memento')"))
    home = client.get("/api/recs/home").json()
    picks = [i["movie"]["id"] for i in home["hero"]] + top_ids(home)
    acts = {
        "dislike": lambda m: client.put(f"/api/reactions/{m}", json={"value": -1}),
        "like": lambda m: client.put(f"/api/reactions/{m}", json={"value": 1}),
        "rate": lambda m: client.put(f"/api/ratings/{m}", json={"rating": 6}),
        "watched": lambda m: client.put(f"/api/watched/{m}"),
    }
    done = {}
    for (name, act), m in zip(acts.items(), dict.fromkeys(picks)):
        client.post("/api/events", json={"movie_id": m, "event_type": "detail_view"})
        assert act(m).status_code < 300, name
        done[name] = m
    home = client.get("/api/recs/home").json()
    shown = {i["movie"]["id"]: r["title"] for r in home["rails"] for i in r["items"]}
    shown.update({i["movie"]["id"]: "hero" for i in home["hero"]})
    back = {name: shown[m] for name, m in done.items() if m in shown}
    assert not back, f"recommended back: {back}"


def test_17_a_film_shows_the_same_match_everywhere(client):
    """The Match % on Home (hero and Top Picks) equals the one on the film page and in Why?."""
    onboard(client, find("SELECT id FROM movies WHERE title IN ('Inception', 'Zodiac', 'Heat', 'Se7en', 'Memento')"))
    home = client.get("/api/recs/home").json()
    items = home["hero"] + next(r["items"] for r in home["rails"] if r["key"] == "top_picks")[:5]
    for it in items:
        m = it["movie"]["id"]
        assert client.get(f"/api/movies/{m}").json()["match_pct"] == it["match_pct"], m
        assert client.get(f"/api/recs/explain/{m}").json()["match_pct"] == it["match_pct"], m
