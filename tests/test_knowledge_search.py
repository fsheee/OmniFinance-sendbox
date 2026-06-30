import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_search_knowledge_no_query():
    res = client.get("/knowledge/search")
    assert res.status_code == 422


def test_search_knowledge_returns_always_top5():
    """Vector search always returns top-n nearest neighbors even for gibberish."""
    res = client.get("/knowledge/search?query=xyzzynotaword&n_results=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 5


def test_search_knowledge_returns_results():
    res = client.get("/knowledge/search?query=compound+interest&n_results=3")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    if len(data) > 0:
        item = data[0]
        assert "term" in item
        assert "definition" in item
        assert "analogy" in item
        assert "explanation" in item
        assert "score" in item
        assert 0 <= item["score"] <= 1


def test_search_knowledge_custom_n():
    res = client.get("/knowledge/search?query=interest&n_results=1")
    assert res.status_code == 200
    assert len(res.json()) <= 1


def test_search_knowledge_scores_ordered():
    res = client.get("/knowledge/search?query=debt+savings&n_results=5")
    assert res.status_code == 200
    data = res.json()
    scores = [item["score"] for item in data]
    assert scores == sorted(scores, reverse=True)
