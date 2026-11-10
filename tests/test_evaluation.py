from research.evaluate import evaluate


def test_evaluation_counts_and_metric_integrity():
    result = evaluate()
    for metrics in result["methods"].values():
        assert metrics["answerable_cases"] == 40
        assert metrics["unanswerable_cases"] == 10
        assert len(metrics["cases"]) == 50
        assert 0 <= metrics["source_recall_at_k"] <= 1
        assert all(row["recall_at_k"] is None for row in metrics["cases"] if not row["answerable"])


def test_all_method_comparison_records_provenance_and_separates_unanswerable():
    import numpy as np

    class Encoder:
        def encode(self, texts, normalize_embeddings=True):
            return np.array([[1.0, 0.0] for _ in texts])

    result = evaluate(method="all", encoder=Encoder())
    assert set(result["methods"]) == {"first_500_chars_bm25", "bm25", "dense", "hybrid"}
    assert result["embedding"]["model"] == "injected-test-encoder"
    assert result["embedding"]["revision"] is None
    assert len(result["implementation_sha256"]) == 64
    for metrics in result["methods"].values():
        assert 0 <= metrics["query_p50_ms"] <= metrics["query_p95_ms"]
        assert metrics["index_build_seconds"] >= 0
        assert 0 <= metrics["unanswerable_with_results"] <= 10
        assert all(len(row["retrieved_passage_ids"]) <= result["k"] for row in metrics["cases"])


def test_evaluation_invalid_method_or_k():
    import pytest

    for kwargs in ({"method": "typo"}, {"k": 0}, {"k": 13}):
        with pytest.raises(ValueError):
            evaluate(**kwargs)
