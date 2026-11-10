"""Scoped, expiring SQLite report cache; exact matching needs no model download."""

import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta

import numpy as np

DB_PATH = "database/memory.db"
THRESHOLD = 0.80


class MemoryAgent:
    def __init__(
        self,
        db_path: str = DB_PATH,
        model_name: str = "all-MiniLM-L6-v2",
        *,
        namespace: str = "default",
        ttl_hours: float = 24,
        encoder=None,
    ):
        self.db_path = db_path
        self.model_name = model_name
        self.namespace = namespace
        self.ttl_hours = ttl_hours
        self._model = encoder
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()

    @property
    def model(self):
        if self._model is None and os.getenv("EREVNA_SEMANTIC_CACHE") == "1":
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL,
                report TEXT NOT NULL, embedding TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
            existing = {r[1] for r in conn.execute("PRAGMA table_info(memory)")}
            for name, declaration in {
                "namespace": "TEXT NOT NULL DEFAULT 'legacy'",
                "context": "TEXT NOT NULL DEFAULT ''",
                "payload": "TEXT NOT NULL DEFAULT '{}'",
                "embedding_model": "TEXT NOT NULL DEFAULT ''",
            }.items():
                if name not in existing:
                    conn.execute(f"ALTER TABLE memory ADD COLUMN {name} {declaration}")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS memory_scope ON memory(namespace, context, created_at)"
            )

    def save(self, task: str, report: str, *, context: str = "", payload: dict | None = None):
        model = self.model
        embedding = model.encode(task).tolist() if model is not None else []
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO memory
                (task, report, embedding, namespace, context, payload, embedding_model)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    task,
                    report,
                    json.dumps(embedding),
                    self.namespace,
                    context,
                    json.dumps(payload or {}),
                    self.model_name if model is not None else "",
                ),
            )
            conn.execute("DELETE FROM memory WHERE created_at < datetime('now', '-30 days')")

    def get_similar(self, query: str, threshold: float = THRESHOLD, *, context: str = ""):
        cutoff = (datetime.now(UTC) - timedelta(hours=self.ttl_hours)).strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT task, report, embedding, payload, created_at, embedding_model
                FROM memory WHERE namespace=? AND context=? AND created_at>=?
                ORDER BY id DESC LIMIT 50""",
                (self.namespace, context, cutoff),
            ).fetchall()
        model = self.model
        query_vector = np.asarray(model.encode(query)) if model is not None else None
        best, best_score = None, 0.0
        for task, report, emb_str, payload_str, created_at, emb_model in rows:
            score = 1.0 if task.strip().casefold() == query.strip().casefold() else 0.0
            try:
                if not score and query_vector is not None and emb_model == self.model_name:
                    emb = np.asarray(json.loads(emb_str))
                    if emb.shape == query_vector.shape:
                        score = float(
                            np.dot(query_vector, emb)
                            / (np.linalg.norm(query_vector) * np.linalg.norm(emb) + 1e-9)
                        )
                payload = json.loads(payload_str)
            except (ValueError, TypeError):
                continue
            if score > best_score:
                best_score = score
                best = {
                    "task": task,
                    "report": report,
                    "payload": payload,
                    "created_at": created_at,
                    "score": score,
                }
        return best if best_score >= threshold else None
