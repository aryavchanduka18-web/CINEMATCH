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