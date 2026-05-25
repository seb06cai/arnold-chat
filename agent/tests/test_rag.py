import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag import load_retriever, retrieve


def test_load_retriever_is_not_none():
    r = load_retriever()
    assert r is not None


def test_retrieve_returns_list_of_strings():
    r = load_retriever()
    results = retrieve(r, "how to do a bench press")
    assert isinstance(results, list) and len(results) > 0
    assert all(isinstance(s, str) for s in results)


def test_retrieve_is_relevant():
    r = load_retriever()
    results = retrieve(r, "standing barbell curl execution")
    combined = " ".join(results).lower()
    assert any(w in combined for w in ["curl", "bicep", "bar", "elbow", "arm"])


def test_retrieve_short_query():
    r = load_retriever()
    results = retrieve(r, "squat")
    assert len(results) > 0


def test_retriever_is_cached():
    r1 = load_retriever()
    r2 = load_retriever()
    assert r1 is r2
