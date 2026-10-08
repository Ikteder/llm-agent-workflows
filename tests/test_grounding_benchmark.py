from __future__ import annotations

from scripts.evaluate_grounding_integrity import DEFAULT_CASES, evaluate


def test_grounding_integrity_corpus() -> None:
    result = evaluate(DEFAULT_CASES)
    assert result["case_count"] == 12
    assert result["filename_only_correct"] == 2
    assert result["receipt_correct"] == 12
    assert all(item["receipt_correct"] for item in result["results"])
