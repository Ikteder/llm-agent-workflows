from __future__ import annotations

from app.agent.tools import search_docs, search_logs


def test_search_docs_returns_predictive_maintenance_summary(container) -> None:
    results = search_docs(
        container.tool_context,
        "What does the hybrid fusion approach do in predictive maintenance?",
        project="predictive_maintenance",
        limit=3,
    )
    assert results
    assert any("predictive_maintenance_operator_summary.md" in result.path for result in results)


def test_search_logs_returns_activity_log(container) -> None:
    results = search_logs(
        container.tool_context,
        "Which log says the CIFAR-10 confusion matrix was exported?",
        project="efficient_robust_cv",
        limit=3,
    )
    assert results
    assert any("efficient_robust_cv_activity.log" in result.path for result in results)
