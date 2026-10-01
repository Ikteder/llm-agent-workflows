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
    first = client.post(
        "/api/reports/generate",
        json={
            "session_id": "report-test",
            "project": "predictive_maintenance",
            "question": "Generate a short report on the predictive maintenance hybrid fusion model.",
        },
    )
    assert first.status_code == 409
    approval = first.json()["detail"]["approval_required"]
    decision = client.post(
        f"/api/tool-policy/approvals/{approval['approval_id']}",
        json={"session_id": "report-test", "decision": "approve"},
    )
    assert decision.status_code == 200

    response = client.post(
        "/api/reports/generate",
        json={
            "session_id": "report-test",
            "project": "predictive_maintenance",
            "question": "Generate a short report on the predictive maintenance hybrid fusion model.",
            "approval_id": approval["approval_id"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["markdown_path"].endswith(".md")

    replay = client.post(
        "/api/reports/generate",
        json={
            "session_id": "report-test",
            "project": "predictive_maintenance",
            "question": "Generate a short report on the predictive maintenance hybrid fusion model.",
            "approval_id": approval["approval_id"],
        },
    )
    assert replay.status_code == 403


def test_unknown_project_is_denied_before_tools(client) -> None:
    response = client.post(
        "/api/chat",
        json={
            "session_id": "unknown-project-test",
            "project": "../../private",
            "question": "Generate a report.",
            "generate_report": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "policy_denied"
    assert payload["report"] is None
    assert payload["approval_required"] is None


def test_tool_policy_manifest_is_explicit(client) -> None:
    response = client.get("/api/tool-policy/manifest")
    assert response.status_code == 200
    payload = response.json()
    report_policy = next(item for item in payload["tools"] if item["name"] == "generate_report")
    assert report_policy == {"name": "generate_report", "risk": "write", "requires_approval": True}
