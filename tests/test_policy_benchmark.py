from __future__ import annotations

from pathlib import Path

from scripts.evaluate_tool_policy import evaluate, render_svg


def test_exact_intent_policy_beats_name_only_baseline(repo_root: Path) -> None:
    result = evaluate(repo_root / "benchmarks" / "tool-policy-cases-v1.json")
    assert result["case_count"] == 12
    assert result["exact_intent_correct"] == 12
    assert result["name_only_correct"] == 5
    assert "12 of 12" in render_svg(result)
