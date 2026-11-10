import csv

from research.evaluate_support import export_review_template, load_dataset, score


def test_fixture_validity_balance_and_label_provenance():
    data = load_dataset()
    assert "Not independently human reviewed" in data["label_provenance"]
    assert len(data["cases"]) == 32
    for split in ("development", "evaluation"):
        cases = [c for c in data["cases"] if c["split"] == split]
        assert len(cases) == 16
        assert {
            label: sum(c["expected_verdict"] == label for c in cases)
            for label in ("supported", "partially_supported", "contradicted", "insufficient")
        } == {"supported": 4, "partially_supported": 4,
              "contradicted": 4 if split == "development" else 5,
              "insufficient": 4 if split == "development" else 3}
    dev = {c["category"] for c in data["cases"] if c["split"] == "development"}
    evaluation = {c["category"] for c in data["cases"] if c["split"] == "evaluation"}
    assert not dev & evaluation
    assert all(c["human_review_status"] == "pending" for c in data["cases"])


def test_unavailable_and_narrowed_claims_are_not_scored_as_correct_originals():
    rows = [
        {"expected": "supported", "predicted": "supported", "disposition": "retained"},
        {"expected": "supported", "predicted": "unavailable", "disposition": "excluded"},
        {
            "expected": "partially_supported",
            "predicted": "partially_supported",
            "disposition": "narrowed",
        },
        {"expected": "contradicted", "predicted": "supported", "disposition": "retained"},
    ]
    result = score(rows)
    assert result["classification_accuracy"] == 0.5
    assert result["supported_original_retention"] == 0.5
    assert result["unsupported_original_acceptance"] == 0.5
    assert result["retained_original_precision"] == 0.5
    assert result["narrowed_claims_emitted"] == 1
    assert result["unavailable_decisions"] == 1


def test_human_review_template_does_not_reveal_reference_labels(tmp_path):
    path = tmp_path / "review.csv"
    data = load_dataset()
    export_review_template(data["cases"], path)
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 32
    assert all(r["reviewer_verdict"] == "" for r in rows)
    assert "expected_verdict" not in rows[0]
    assert "reference_rationale" not in rows[0]
