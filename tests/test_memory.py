import sqlite3

from agents.memory_agent import MemoryAgent


def test_cache_is_scoped_and_preserves_evidence(tmp_path):
    path = str(tmp_path / "memory.db")
    a = MemoryAgent(path, namespace="alice")
    b = MemoryAgent(path, namespace="bob")
    a.save("Retries", "Report", context="nvidia:bm25", payload={"passages": ["S1-P1"]})
    assert b.get_similar("Retries", context="nvidia:bm25") is None
    assert a.get_similar("Retries", context="demo:bm25") is None
    assert a.get_similar("retries", context="nvidia:bm25")["payload"]["passages"] == ["S1-P1"]


def test_expired_reports_are_not_reused(tmp_path):
    path = str(tmp_path / "memory.db")
    cache = MemoryAgent(path, ttl_hours=1)
    cache.save("Retries", "Old result")
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE memory SET created_at=datetime('now', '-2 hours')")
    assert cache.get_similar("Retries") is None


def test_legacy_cache_migrates_without_exposing_old_reports(tmp_path):
    path = str(tmp_path / "memory.db")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE memory (id INTEGER PRIMARY KEY, task TEXT, report TEXT, embedding TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute("INSERT INTO memory (task, report, embedding) VALUES ('query','old','[]')")
    cache = MemoryAgent(path)
    assert cache.get_similar("query") is None
    cache.save("query", "new")
    assert cache.get_similar("query")["report"] == "new"


def test_clear_is_namespace_and_context_scoped(tmp_path):
    path = str(tmp_path / "memory.db")
    alice = MemoryAgent(path, namespace="alice")
    bob = MemoryAgent(path, namespace="bob")
    for cache in (alice, bob):
        cache.save("query", "one", context="first")
        cache.save("query", "two", context="second")
    assert alice.clear(context="first") == 1
    assert alice.get_similar("query", context="first") is None
    assert alice.get_similar("query", context="second")
    assert alice.clear() == 1
    assert alice.clear() == 0
    assert bob.get_similar("query", context="first")
    assert bob.get_similar("query", context="second")


def test_invalid_cache_configuration_and_future_schema(tmp_path):
    import pytest

    path = str(tmp_path / "memory.db")
    for kwargs in (
        {"ttl_hours": float("nan")},
        {"ttl_hours": 0},
        {"threshold": 0},
        {"threshold": 1.01},
    ):
        with pytest.raises(ValueError):
            MemoryAgent(path, **kwargs)
    cache = MemoryAgent(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(ValueError, match="newer"):
        MemoryAgent(path)
    with pytest.raises(ValueError):
        cache.get_similar("query", threshold=float("nan"))


def test_exact_cache_regression_false_matches_and_misses(tmp_path):
    cache = MemoryAgent(str(tmp_path / "memory.db"))
    cache.save("Cache expires after 24 hours?", "report")
    positives = [
        "Cache expires after 24 hours?",
        "  Cache expires after 24 hours?  ",
        "cache expires after 24 hours?",
    ]
    negatives = [
        "Cache expires after 48 hours?",
        "Cache does not expire after 24 hours?",
        "Different question",
        "",
    ]
    assert all(cache.get_similar(query) is not None for query in positives)
    assert all(cache.get_similar(query) is None for query in negatives)
    with sqlite3.connect(cache.db_path) as conn:
        conn.execute("UPDATE memory SET payload='[]'")
    assert cache.get_similar(positives[0]) is None


def test_concurrent_legacy_migration_is_serialized(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    path = str(tmp_path / "memory.db")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE memory (id INTEGER PRIMARY KEY, task TEXT, report TEXT, embedding TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
    with ThreadPoolExecutor(max_workers=4) as pool:
        caches = list(pool.map(lambda i: MemoryAgent(path, namespace=str(i)), range(4)))
    for cache in caches:
        cache.save("query", cache.namespace)
        assert cache.get_similar("query")["report"] == cache.namespace
