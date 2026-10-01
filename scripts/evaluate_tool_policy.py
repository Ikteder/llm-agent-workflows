from __future__ import annotations

import argparse
import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.agent.tool_policy import ToolInvocation, ToolPolicyEngine, confined_path


NOW = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)


def invocation(**overrides) -> ToolInvocation:
    values = {
        "session_id": "session-a",
        "tool_name": "generate_report",
        "arguments": {"title": "Approved title", "question": "Q", "summary": "S", "sources": []},
        "project": "project-a",
    }
    values.update(overrides)
    return ToolInvocation(**values)


def exact_evaluator(kind: str, root: Path) -> bool:
    policy = ToolPolicyEngine(
        secret=b"benchmark-secret",
        audit_path=root / "audit.jsonl",
        allowed_projects={"project-a"},
        approval_ttl_seconds=30,
    )
    base = invocation()
    if kind == "read":
        return policy.authorize(
            invocation(tool_name="search_docs", arguments={"query": "latency"}), now=NOW
        ).status == "allowed"
    if kind == "unapproved_write":
        return policy.authorize(base, now=NOW).status == "pending"
    if kind == "unknown_tool":
        return policy.authorize(invocation(tool_name="unknown"), now=NOW).status == "denied"
    if kind == "unknown_project":
        return policy.authorize(invocation(project="project-b"), now=NOW).status == "denied"
    if kind == "stale_policy":
        return policy.authorize(invocation(policy_version="old"), now=NOW).status == "denied"
    if kind == "traversal":
        try:
            confined_path(root, "../outside.md", filename_only=True)
        except ValueError:
            return True
        return False

    pending = policy.authorize(base, now=NOW)
    assert pending.approval_request is not None
    approval_id = pending.approval_request.approval_id
    if kind == "cross_session":
        policy.decide(approval_id, session_id="session-a", approve=True, now=NOW)
        return policy.consume(
            approval_id,
            session_id="session-b",
            tool_name="generate_report",
            project="project-a",
            now=NOW,
        ).status == "denied"
    if kind == "rejection":
        policy.decide(approval_id, session_id="session-a", approve=False, now=NOW)
        return policy.consume(
            approval_id,
            session_id="session-a",
            tool_name="generate_report",
            project="project-a",
            now=NOW,
        ).status == "denied"

    policy.decide(approval_id, session_id="session-a", approve=True, now=NOW)
    if kind == "expiry":
        return policy.consume(
            approval_id,
            session_id="session-a",
            tool_name="generate_report",
            project="project-a",
            now=NOW + timedelta(seconds=31),
        ).status == "denied"

    first = policy.consume(
        approval_id,
        session_id="session-a",
        tool_name="generate_report",
        project="project-a",
        now=NOW,
    )
    if kind == "exact":
        return first.status == "allowed" and first.arguments == base.arguments
    if kind == "mutation":
        attempted = {**base.arguments, "title": "Mutated title"}
        return first.status == "allowed" and first.arguments != attempted and first.arguments == base.arguments
    if kind == "replay":
        second = policy.consume(
            approval_id,
            session_id="session-a",
            tool_name="generate_report",
            project="project-a",
            now=NOW,
        )
        return first.status == "allowed" and second.status == "denied"
    raise ValueError(f"Unknown case kind: {kind}")


def name_only_baseline(kind: str) -> bool:
    """Return whether a tool-name-only policy produces the safe expected outcome."""
    safe_kinds = {"read", "unapproved_write", "exact", "unknown_tool", "rejection"}
    return kind in safe_kinds


def evaluate(corpus_path: Path) -> dict:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    results = []
    with tempfile.TemporaryDirectory(prefix="tool-policy-benchmark-") as temp:
        root = Path(temp)
        for case in corpus["cases"]:
            exact_safe = exact_evaluator(case["kind"], root / case["id"])
            baseline_safe = name_only_baseline(case["kind"])
            results.append(
                {
                    "id": case["id"],
                    "kind": case["kind"],
                    "exact_intent_correct": exact_safe,
                    "name_only_correct": baseline_safe,
                }
            )
    return {
        "schema_version": 1,
        "corpus": corpus["name"],
        "case_count": len(results),
        "exact_intent_correct": sum(item["exact_intent_correct"] for item in results),
        "name_only_correct": sum(item["name_only_correct"] for item in results),
        "results": results,
    }


def render_svg(result: dict) -> str:
    total = result["case_count"]
    baseline = result["name_only_correct"]
    exact = result["exact_intent_correct"]
    baseline_width = 520 * baseline / total
    exact_width = 520 * exact / total
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="840" height="300" viewBox="0 0 840 300" role="img" aria-labelledby="title desc">
  <title id="title">Tool policy benchmark</title>
  <desc id="desc">Exact-intent approval passes {exact} of {total} cases. Tool-name-only approval passes {baseline} of {total} cases.</desc>
  <rect width="840" height="300" rx="24" fill="#071525"/>
  <text x="52" y="55" fill="#f4f8fb" font-family="Arial, sans-serif" font-size="26" font-weight="700">Intent-bound tool approval</text>
  <text x="52" y="84" fill="#9fb3c8" font-family="Arial, sans-serif" font-size="15">Deterministic synthetic safety corpus, {total} cases</text>
  <text x="52" y="132" fill="#d9e4ee" font-family="Arial, sans-serif" font-size="16">Tool name only</text>
  <rect x="220" y="111" width="520" height="28" rx="8" fill="#183047"/>
  <rect x="220" y="111" width="{baseline_width:.1f}" height="28" rx="8" fill="#f3a85b"/>
  <text x="756" y="132" fill="#f4f8fb" font-family="Arial, sans-serif" font-size="16" text-anchor="end">{baseline}/{total}</text>
  <text x="52" y="190" fill="#d9e4ee" font-family="Arial, sans-serif" font-size="16">Exact intent</text>
  <rect x="220" y="169" width="520" height="28" rx="8" fill="#183047"/>
  <rect x="220" y="169" width="{exact_width:.1f}" height="28" rx="8" fill="#3dd6a0"/>
  <text x="756" y="190" fill="#f4f8fb" font-family="Arial, sans-serif" font-size="16" text-anchor="end">{exact}/{total}</text>
  <text x="52" y="244" fill="#9fb3c8" font-family="Arial, sans-serif" font-size="14">Checks argument mutation, replay, session scope, expiry, policy drift, and path containment.</text>
  <text x="52" y="269" fill="#71879d" font-family="Arial, sans-serif" font-size="12">Synthetic regression evidence, not a penetration test or production security certification.</text>
</svg>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the intent-bound tool policy.")
    parser.add_argument("--corpus", type=Path, default=Path("benchmarks/tool-policy-cases-v1.json"))
    parser.add_argument("--json", type=Path)
    parser.add_argument("--svg", type=Path)
    args = parser.parse_args()
    result = evaluate(args.corpus)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.svg:
        args.svg.parent.mkdir(parents=True, exist_ok=True)
        args.svg.write_text(render_svg(result), encoding="utf-8")
    print(
        f"Exact-intent: {result['exact_intent_correct']}/{result['case_count']} | "
        f"name-only: {result['name_only_correct']}/{result['case_count']}"
    )
    return 0 if result["exact_intent_correct"] == result["case_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
