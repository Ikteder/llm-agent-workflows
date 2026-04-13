from __future__ import annotations


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_returns_grounded_answer(client) -> None:
    response = client.post(
        "/api/chat",
        json={
            "session_id": "api-test",
            "project": "efficient_robust_cv",
            "question": "Which model performed best on CIFAR-10 in the vision benchmark?",
            "generate_report": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "compare_runs"
    assert "ConvNeXt-Tiny" in payload["answer"]


def test_generate_report_endpoint(client) -> None:
    response = client.post(
        "/api/reports/generate",
        json={
            "session_id": "report-test",
            "project": "predictive_maintenance",
            "question": "Generate a short report on the predictive maintenance hybrid fusion model.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["markdown_path"].endswith(".md")
