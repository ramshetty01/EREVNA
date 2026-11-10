from research.evaluate import evaluate


def test_evaluation_counts_and_metric_integrity():
    result = evaluate()
    for metrics in result["methods"].values():
        assert metrics["answerable_cases"] == 40
        assert metrics["unanswerable_cases"] == 10
        assert len(metrics["cases"]) == 50
        assert 0 <= metrics["source_recall_at_k"] <= 1
        assert all(row["recall_at_k"] is None for row in metrics["cases"] if not row["answerable"])
