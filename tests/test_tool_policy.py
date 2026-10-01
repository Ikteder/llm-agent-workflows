from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.agent.tool_policy import ToolInvocation, ToolPolicyEngine, confined_path
from app.services.metrics_reader import MetricsReader


def build_policy(tmp_path, *, ttl: int = 900) -> ToolPolicyEngine:
    return ToolPolicyEngine(
        secret=b"deterministic-test-secret",
        audit_path=tmp_path / "audit.jsonl",
        allowed_projects={"project-a"},
        approval_ttl_seconds=ttl,
    )


def report_invocation(**overrides) -> ToolInvocation:
    values = {
        "session_id": "session-a",
        "tool_name": "generate_report",
        "arguments": {
            "title": "Project A report",
            "question": "Summarize the run",
            "summary": "Evidence summary",
            "sources": [],
        },
        "project": "project-a",
    }
    values.update(overrides)
    return ToolInvocation(**values)


def test_read_tool_is_allowed_without_approval(tmp_path) -> None:
    policy = build_policy(tmp_path)
    decision = policy.authorize(
        ToolInvocation(
            session_id="session-a",
            tool_name="search_docs",
            arguments={"query": "latency"},
            project="project-a",
        )
    )
    assert decision.status == "allowed"
    assert decision.receipt is None


def test_exact_approval_is_single_use_and_returns_stored_arguments(tmp_path) -> None:
    policy = build_policy(tmp_path)
    invocation = report_invocation()
    pending = policy.authorize(invocation)
    assert pending.status == "pending"
    assert pending.approval_request is not None
    assert "content" not in json.dumps(pending.approval_request.arguments)
    assert "summary" not in pending.approval_request.arguments
    assert len(pending.approval_request.arguments["summary_sha256"]) == 64

    policy.decide(
        pending.approval_request.approval_id,
        session_id=invocation.session_id,
        approve=True,
    )
    allowed = policy.consume(
        pending.approval_request.approval_id,
        session_id=invocation.session_id,
        tool_name=invocation.tool_name,
        project=invocation.project,
    )
    assert allowed.status == "allowed"
    assert allowed.arguments == invocation.arguments
    assert len(allowed.receipt or "") == 64

    replay = policy.consume(
        pending.approval_request.approval_id,
        session_id=invocation.session_id,
        tool_name=invocation.tool_name,
        project=invocation.project,
    )
    assert replay.status == "denied"
    assert replay.reason == "approval_consumed"


def test_approved_call_cannot_be_rebound_to_changed_arguments(tmp_path) -> None:
    policy = build_policy(tmp_path)
    original = report_invocation()
    pending = policy.authorize(original)
    assert pending.approval_request is not None
    policy.decide(pending.approval_request.approval_id, session_id="session-a", approve=True)

    changed = report_invocation(arguments={**original.arguments, "title": "Changed report"})
    changed_pending = policy.authorize(changed)
    assert changed_pending.status == "pending"
    assert changed_pending.approval_request is not None
    assert changed_pending.approval_request.approval_id != pending.approval_request.approval_id

    consumed = policy.consume(
        pending.approval_request.approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
    )
    assert consumed.arguments["title"] == "Project A report"


def test_pending_record_keeps_an_immutable_snapshot_of_arguments(tmp_path) -> None:
    policy = build_policy(tmp_path)
    original = report_invocation()
    pending = policy.authorize(original)
    assert pending.approval_request is not None

    original.arguments["title"] = "Mutated after approval request"
    policy.decide(pending.approval_request.approval_id, session_id="session-a", approve=True)
    consumed = policy.consume(
        pending.approval_request.approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
    )

    assert consumed.arguments["title"] == "Project A report"


def test_session_scope_rejection_and_expiry_fail_closed(tmp_path) -> None:
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    policy = build_policy(tmp_path, ttl=30)
    pending = policy.authorize(report_invocation(), now=now)
    assert pending.approval_request is not None
    with pytest.raises(PermissionError):
        policy.decide(
            pending.approval_request.approval_id,
            session_id="different-session",
            approve=True,
            now=now,
        )
    policy.decide(pending.approval_request.approval_id, session_id="session-a", approve=True, now=now)
    expired = policy.consume(
        pending.approval_request.approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        now=now + timedelta(seconds=31),
    )
    assert expired.status == "denied"
    assert expired.reason == "approval_expired"


def test_unknown_tool_project_and_stale_policy_are_denied(tmp_path) -> None:
    policy = build_policy(tmp_path)
    assert policy.authorize(report_invocation(tool_name="delete_everything")).reason == "unknown_tool"
    assert policy.authorize(report_invocation(project="project-b")).reason == "unknown_project"
    assert policy.authorize(report_invocation(policy_version="old")).reason == "stale_policy_version"


def test_audit_log_excludes_tool_arguments(tmp_path) -> None:
    policy = build_policy(tmp_path)
    sensitive = "question text must not enter audit"
    policy.authorize(report_invocation(arguments={"question": sensitive}))
    audit_text = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert sensitive not in audit_text
    event = json.loads(audit_text.splitlines()[0])
    assert event["event"] == "approval_requested"
    assert len(event["invocation_digest"]) == 64


def test_confined_path_and_metrics_reader_reject_traversal(tmp_path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    assert confined_path(root, "safe.csv", filename_only=True) == (root / "safe.csv").resolve()
    with pytest.raises(ValueError):
        confined_path(root, "../secret.txt", filename_only=True)
    with pytest.raises(ValueError):
        MetricsReader(tmp_path).load_table("../secret.csv")
