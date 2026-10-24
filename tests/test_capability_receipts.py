from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET

import pytest

from app.agent.capability_receipts import (
    ToolCapability,
    capability_receipt,
    compare_capabilities,
)
from app.agent.tool_policy import ToolInvocation, ToolPolicyEngine
from scripts.evaluate_capability_receipts import (
    base_capability,
    evaluate,
    mutate,
    render_svg,
)


def build_policy(tmp_path) -> ToolPolicyEngine:
    return ToolPolicyEngine(
        secret=b"capability-test-secret",
        audit_path=tmp_path / "audit.jsonl",
        allowed_projects={"project-a"},
    )


def external_invocation(capability: ToolCapability) -> ToolInvocation:
    return ToolInvocation(
        session_id="session-a",
        tool_name="generate_report",
        arguments={
            "title": "Approved",
            "question": "Q",
            "summary": "private",
            "sources": [],
        },
        project="project-a",
        capability=capability,
    )


def test_receipt_is_stable_across_object_key_order() -> None:
    reviewed = base_capability()
    reordered = mutate(reviewed, "object_key_order")
    assert capability_receipt(reviewed) == capability_receipt(reordered)
    assert compare_capabilities(reviewed, reordered).verdict == "matched"


@pytest.mark.parametrize(
    ("mutation", "finding"),
    [
        ("server_id", "SERVER_ID_CHANGED"),
        ("transport", "TRANSPORT_CHANGED"),
        ("protocol_version", "PROTOCOL_VERSION_CHANGED"),
        ("tool_name", "TOOL_NAME_CHANGED"),
        ("description", "TOOL_DESCRIPTION_CHANGED"),
        ("input_schema", "INPUT_SCHEMA_CHANGED"),
        ("output_schema", "OUTPUT_SCHEMA_CHANGED"),
        ("annotations", "TOOL_ANNOTATIONS_CHANGED"),
        ("execution", "TOOL_EXECUTION_CHANGED"),
        ("meta", "TOOL_META_CHANGED"),
        ("extra_field", "TOOL_DEFINITION_CHANGED"),
    ],
)
def test_each_contract_surface_has_a_stable_finding(
    mutation: str, finding: str
) -> None:
    reviewed = base_capability()
    comparison = compare_capabilities(reviewed, mutate(reviewed, mutation))
    assert comparison.verdict == "blocked"
    assert finding in comparison.findings


def test_capability_validation_is_bounded_and_rejects_non_json() -> None:
    base = base_capability()
    with pytest.raises(ValueError, match="finite JSON"):
        capability_receipt(
            ToolCapability(
                base.server_id,
                base.transport,
                base.protocol_version,
                {"name": "x", "n": math.nan},
            )
        )
    nested: dict = {"name": "x"}
    cursor = nested
    for _ in range(34):
        cursor["next"] = {}
        cursor = cursor["next"]
    with pytest.raises(ValueError, match="nesting depth"):
        capability_receipt(
            ToolCapability(
                base.server_id, base.transport, base.protocol_version, nested
            )
        )


def test_policy_requires_fresh_match_without_consuming_on_drift(tmp_path) -> None:
    policy = build_policy(tmp_path)
    reviewed = base_capability()
    invocation = external_invocation(reviewed)
    pending = policy.authorize(invocation)
    assert pending.approval_request is not None
    approval_id = pending.approval_request.approval_id
    preview = pending.approval_request.capability
    assert preview is not None
    assert preview["tool_name"] == "generate_report"
    assert reviewed.tool["description"] not in json.dumps(preview)
    policy.decide(approval_id, session_id="session-a", approve=True)

    missing = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
    )
    assert missing.reason == "capability_evidence_required"
    assert missing.findings == ("CAPABILITY_EVIDENCE_REQUIRED",)

    drifted = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=mutate(reviewed, "input_schema"),
    )
    assert drifted.reason == "capability_drift"
    assert "INPUT_SCHEMA_CHANGED" in drifted.findings

    allowed = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=mutate(reviewed, "object_key_order"),
    )
    assert allowed.status == "allowed"
    assert allowed.arguments == invocation.arguments

    replay = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=reviewed,
    )
    assert replay.reason == "approval_consumed"
    audit = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    assert "Write a report" not in audit
    assert '"INPUT_SCHEMA_CHANGED"' in audit


def test_policy_stores_an_immutable_capability_snapshot(tmp_path) -> None:
    policy = build_policy(tmp_path)
    capability = base_capability()
    pending = policy.authorize(external_invocation(capability))
    assert pending.approval_request is not None
    capability.tool["description"] = "mutated after review"
    policy.decide(
        pending.approval_request.approval_id, session_id="session-a", approve=True
    )
    decision = policy.consume(
        pending.approval_request.approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=base_capability(),
    )
    assert decision.status == "allowed"


def test_benchmark_beats_name_and_arguments_baseline(repo_root) -> None:
    result = evaluate(repo_root / "benchmarks" / "mcp-capability-drift-v1.json")
    assert result["case_count"] == 14
    assert result["receipt_correct"] == 14
    assert result["name_and_arguments_correct"] == 3
    ET.fromstring(render_svg(result))


def test_unbound_local_approval_cannot_authorize_external_execution(tmp_path) -> None:
    policy = build_policy(tmp_path)
    pending = policy.authorize(
        ToolInvocation("session-a", "generate_report", {}, project="project-a")
    )
    approval_id = pending.approval_request.approval_id
    policy.decide(approval_id, session_id="session-a", approve=True)
    decision = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=base_capability(),
    )
    assert decision.reason == "capability_binding_required"
    assert decision.arguments is None


def test_malformed_observation_denies_without_consuming(tmp_path) -> None:
    policy = build_policy(tmp_path)
    capability = base_capability()
    pending = policy.authorize(external_invocation(capability))
    approval_id = pending.approval_request.approval_id
    policy.decide(approval_id, session_id="session-a", approve=True)
    capability.tool["_meta"]["invalid"] = math.inf
    denied = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=capability,
    )
    assert denied.findings == ("CAPABILITY_EVIDENCE_INVALID",)
    assert denied.arguments is None
    allowed = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=base_capability(),
    )
    assert allowed.status == "allowed"


def test_returned_approval_cannot_modify_server_held_scope(tmp_path) -> None:
    policy = build_policy(tmp_path)
    pending = policy.authorize(external_invocation(base_capability()))
    approval_id = pending.approval_request.approval_id
    pending.approval_request.project = "project-b"
    pending.approval_request.capability.clear()
    decided = policy.decide(approval_id, session_id="session-a", approve=True)
    assert decided.project == "project-a"
    assert decided.capability["tool_name"] == "generate_report"
    decided.tool_name = "delete_everything"
    allowed = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        observed_capability=base_capability(),
    )
    assert allowed.status == "allowed"


def test_changed_capability_needs_its_own_approval(tmp_path) -> None:
    policy = build_policy(tmp_path)
    base = base_capability()
    first = policy.authorize(external_invocation(base)).approval_request
    second = policy.authorize(
        external_invocation(mutate(base, "server_id"))
    ).approval_request
    assert first.approval_id != second.approval_id
    assert first.invocation_digest != second.invocation_digest
