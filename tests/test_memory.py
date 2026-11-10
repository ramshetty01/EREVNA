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
