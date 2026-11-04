"""New users see films in their onboarding languages first (language_lift)."""
from types import SimpleNamespace

import numpy as np

from cinematch_engine.online import OnlineEngine, UserState


def lift(langs, behavioral, film_langs=("en", "hi", "ta", "en")):
    fake = SimpleNamespace(cat=SimpleNamespace(language=list(film_langs)))
    st = UserState(languages=list(langs), behavioral_count=behavioral)
    scores = {"popularity": np.full(len(film_langs), 7.0, dtype=np.float32), "content": np.zeros(len(film_langs))}
    return OnlineEngine.language_lift(fake, st, scores)


def test_cold_user_who_picked_hindi_gets_hindi_lifted_only():
    out = lift(["hi"], 0)
    assert np.allclose(out["popularity"], [7.0, 8.2, 7.0, 7.0])
    assert out["content"].tolist() == [0, 0, 0, 0]          # other sources untouched


def test_lift_fades_with_feedback():
    assert np.isclose(lift(["hi"], 5)["popularity"][1], 7.6)   # warming: half
    assert lift(["hi"], 20)["popularity"][1] == np.float32(7.0)  # established: none


def test_english_gets_half_when_picked_with_another_language():
    out = lift(["en", "hi"], 0)["popularity"]
    assert out[1] > out[0] > 7.0


def test_no_languages_no_change():
    scores = {"popularity": np.ones(4, dtype=np.float32)}
    fake = SimpleNamespace(cat=SimpleNamespace(language=["en"] * 4))
    assert OnlineEngine.language_lift(fake, UserState(), scores) is scores
