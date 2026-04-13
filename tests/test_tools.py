from __future__ import annotations

from app.agent.tools import compare_runs


def test_compare_runs_finds_top_cifar_model(container) -> None:
    result = compare_runs(
        container.tool_context,
        project="efficient_robust_cv",
        metric="accuracy",
        dataset="CIFAR-10",
        limit=3,
    )
    assert result.rows
    assert result.rows[0]["model_name"] == "ConvNeXt-Tiny"


def test_compare_runs_handles_model_export_latency(container) -> None:
    result = compare_runs(
        container.tool_context,
        project="model_export",
        metric="latency_ms",
        models=["mobilenet"],
        prefer_lowest=True,
        limit=3,
    )
    assert result.rows
    assert result.rows[0]["variant"] == "onnx"
