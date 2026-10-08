import numpy as np
import pandas as pd

from cinematch_engine.models.content import build_content_features


def _films():
    movies = pd.DataFrame({
        "tmdb_id": [1, 2, 3],
        "overview": ["a detective hunts a serial killer in a rainy city",
                     "a detective hunts a serial killer across the country",
                     "two friends sing and dance at a summer wedding"],
        "tagline": [None, None, "love"],
        "keywords": [["serial killer"], ["serial killer"], ["wedding"]],
        "genres": [["Crime"], ["Crime"], ["Romance"]],
        "original_language": ["en", "en", "hi"],
        "countries": [["US"], ["US"], ["IN"]],
        "studios": [["A"], ["B"], ["C"]],
    })
    credits = pd.DataFrame([
        {"tmdb_id": 1, "name": "Dir X", "role": "director", "credit_order": None},
        {"tmdb_id": 2, "name": "Dir X", "role": "director", "credit_order": None},
        {"tmdb_id": 3, "name": "Dir Y", "role": "director", "credit_order": None},
    ])
    return movies, credits


def test_rows_are_unit_length_and_similar_films_are_closer():
    feats = build_content_features(*_films())
    m = feats.matrix
    assert m.shape[0] == 3
    assert np.allclose(np.sqrt(m.multiply(m).sum(axis=1)).A1, 1.0)
    sim = (m @ m.T).toarray()
    assert sim[0, 1] > sim[0, 2]
    assert set(feats.block_columns) == {"text", "genres", "language", "country", "director", "cast", "studio"}

def test_adding_films_with_fit_mask_leaves_existing_rows_unchanged():
    movies, credits = _films()
    before = build_content_features(movies.iloc[:2], credits).matrix
    extra = pd.DataFrame({"tmdb_id": [4], "overview": ["a brand new film about a detective"], "tagline": [None],
                          "keywords": [[]], "genres": [["Crime"]], "original_language": ["en"],
                          "countries": [["US"]], "studios": [["Z"]]})
    both = pd.concat([movies.iloc[:2], extra], ignore_index=True)
    credits = pd.concat([credits, pd.DataFrame([{"tmdb_id": 4, "name": "Dir Z", "role": "director",
                                                 "credit_order": None}])], ignore_index=True)
    feats = build_content_features(both, credits, fit_mask=np.array([True, True, False]))
    cols = feats.fit_columns()
    after = feats.matrix
    assert abs(after[:2][:, cols] - before).max() == 0           # same values on the original columns
    assert after[:2][:, np.setdiff1d(np.arange(after.shape[1]), cols)].nnz == 0
    assert len(feats.block_vocab["director"]) == 2 and feats.block_vocab["director"][-1] == "Dir Z"
    assert (after[2] @ after[0].T).toarray()[0, 0] > 0           # the new film is similar to the crime films
