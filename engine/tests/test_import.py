import cinematch_engine
from cinematch_engine.config import event_weights


def test_package_imports():
    assert cinematch_engine.__version__


def test_event_weights_load():
    w = event_weights()
    assert w["like"] == 4
    assert w["dislike"] == -5
    assert set(w) == {
        "detail_view", "quick_view", "search_click", "list_add",
        "list_remove", "watched", "like", "dislike", "rate",
    }
