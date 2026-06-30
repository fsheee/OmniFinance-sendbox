import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import shutil
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

import database.vector_store as vs


SAMPLE_KB = {
    "compound interest": {
        "definition": "Earning interest on your interest over time.",
        "analogy": "like a snowball rolling downhill",
        "explanation": "Earning interest on top of previously earned interest."
    },
    "liquidity": {
        "definition": "How quickly an asset can be turned into cash.",
        "analogy": "like cash in your wallet vs selling a house",
        "explanation": "Cash is highly liquid while real estate is not."
    },
    "inflation": {
        "definition": "The general increase in prices over time.",
        "analogy": "like a dollar buying less each year",
        "explanation": "Prices rise over time reducing purchasing power."
    }
}


def setup_function():
    vs._client = None
    vs._collection = None
    vs._seeded = False
    vs.CHROMA_DIR = tempfile.mkdtemp(prefix="chroma_test_")


def teardown_function():
    if vs._client:
        vs._client.clear_system_cache()
    if os.path.exists(vs.CHROMA_DIR):
        shutil.rmtree(vs.CHROMA_DIR, ignore_errors=True)
    vs.CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".chroma")


def test_seed_knowledge_base():
    vs.seed_knowledge_base(SAMPLE_KB)
    results = vs.search_knowledge("compound interest", n_results=5)
    terms = [r["term"] for r in results]
    assert "compound interest" in terms


def test_seed_is_idempotent():
    vs.seed_knowledge_base(SAMPLE_KB)
    vs.seed_knowledge_base(SAMPLE_KB)
    results = vs.search_knowledge("compound interest", n_results=5)
    assert len(results) == 3


def test_search_returns_correct_fields():
    vs.seed_knowledge_base(SAMPLE_KB)
    results = vs.search_knowledge("liquidity", n_results=3)
    assert len(results) == 3
    item = results[0]
    assert "term" in item
    assert "definition" in item
    assert "analogy" in item
    assert "explanation" in item
    assert 0 <= item["score"] <= 1


def test_search_respects_n_results():
    vs.seed_knowledge_base(SAMPLE_KB)
    r1 = vs.search_knowledge("money", n_results=1)
    assert len(r1) == 1
    r3 = vs.search_knowledge("money", n_results=3)
    assert len(r3) == 3


def test_search_scores_descending():
    vs.seed_knowledge_base(SAMPLE_KB)
    results = vs.search_knowledge("financial concepts", n_results=3)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_search_before_seed_returns_empty():
    assert vs.search_knowledge("anything") == []
