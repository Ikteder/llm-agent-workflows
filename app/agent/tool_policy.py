from __future__ import annotations

import hashlib
import hmac
import json
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from app.models.schemas import ToolApprovalRequest


POLICY_VERSION = "2026-10-01.v1"


@dataclass(frozen=True)
class ToolPolicy:
    name: str
    risk: Literal["read", "write"]
    requires_approval: bool


@dataclass(frozen=True)
class ToolInvocation:
    session_id: str
    tool_name: str
    arguments: dict[str, Any]
    project: str | None = None
    policy_version: str = POLICY_VERSION


@dataclass(frozen=True)
class ToolPolicyDecision:
    status: Literal["allowed", "pending", "denied"]
    reason: str
    approval_request: ToolApprovalRequest | None = None
    receipt: str | None = None
    arguments: dict[str, Any] | None = None


@dataclass
class _ApprovalRecord:
    request: ToolApprovalRequest
    session_id: str
    invocation_digest: str
    arguments: dict[str, Any]
    status: Literal["pending", "approved", "rejected", "consumed", "expired"] = "pending"
    approved_at: str | None = None


DEFAULT_POLICIES = {
    "search_docs": ToolPolicy("search_docs", "read", False),
    "search_logs": ToolPolicy("search_logs", "read", False),
    "read_metrics_csv": ToolPolicy("read_metrics_csv", "read", False),
    "compare_runs": ToolPolicy("compare_runs", "read", False),
    "show_confusion_matrix": ToolPolicy("show_confusion_matrix", "read", False),
    "summarize_failures": ToolPolicy("summarize_failures", "read", False),
    "generate_report": ToolPolicy("generate_report", "write", True),
}


def confined_path(root: Path, relative_name: str, *, filename_only: bool = False) -> Path:
    """Resolve a caller-controlled path and prove it remains under root."""
    if not relative_name or "\x00" in relative_name:
        raise ValueError("Path must be a non-empty string without null bytes.")
    candidate_fragment = Path(relative_name)
    if candidate_fragment.is_absolute():
        raise ValueError("Absolute paths are not allowed.")
    if filename_only and (candidate_fragment.name != relative_name or "/" in relative_name or "\\" in relative_name):
        raise ValueError("Only a file name without directory components is allowed.")
    resolved_root = root.resolve()
    resolved_candidate = (resolved_root / candidate_fragment).resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("Path escapes the configured root.") from exc
    return resolved_candidate


class ToolPolicyEngine:
    """Application-owned tool policy with exact, expiring, single-use approvals."""

    def __init__(
        self,
        *,
        secret: bytes,
        audit_path: Path,
        allowed_projects: set[str],
        approval_ttl_seconds: int = 900,
        policies: dict[str, ToolPolicy] | None = None,
    ) -> None:
        if not secret:
            raise ValueError("A non-empty policy secret is required.")
        if approval_ttl_seconds <= 0:
            raise ValueError("Approval TTL must be positive.")
        self._secret = secret
        self._audit_path = audit_path
        self._allowed_projects = set(allowed_projects)
        self._approval_ttl_seconds = approval_ttl_seconds
        self._policies = dict(policies or DEFAULT_POLICIES)
        self._records: dict[str, _ApprovalRecord] = {}
        self._lock = threading.RLock()

    @property
    def policy_version(self) -> str:
        return POLICY_VERSION

    def manifest(self) -> dict[str, Any]:
        return {
            "policy_version": POLICY_VERSION,
            "approval_ttl_seconds": self._approval_ttl_seconds,
            "tools": [
                {
                    "name": policy.name,
                    "risk": policy.risk,
                    "requires_approval": policy.requires_approval,
                }
                for policy in sorted(self._policies.values(), key=lambda item: item.name)
            ],
            "allowed_projects": sorted(self._allowed_projects),
        }

    def validate_project(self, project: str | None) -> bool:
        return project is None or project in self._allowed_projects

    def authorize(self, invocation: ToolInvocation, *, now: datetime | None = None) -> ToolPolicyDecision:
        current = self._utc(now)
        policy = self._policies.get(invocation.tool_name)
        if policy is None:
            self._audit("denied", invocation, current, reason="unknown_tool")
            return ToolPolicyDecision("denied", "unknown_tool")
        if invocation.policy_version != POLICY_VERSION:
            self._audit("denied", invocation, current, reason="stale_policy_version")
            return ToolPolicyDecision("denied", "stale_policy_version")
        if not self.validate_project(invocation.project):
            self._audit("denied", invocation, current, reason="unknown_project")
            return ToolPolicyDecision("denied", "unknown_project")
        if not policy.requires_approval:
            self._audit("allowed", invocation, current, reason="read_policy")
            return ToolPolicyDecision("allowed", "read_policy")

        invocation_digest = self._invocation_digest(invocation)
        stored_arguments = json.loads(
            json.dumps(invocation.arguments, ensure_ascii=False, allow_nan=False)
        )
        with self._lock:
            matching = self._matching_record(invocation, invocation_digest)
            if matching is not None:
                expires_at = datetime.fromisoformat(matching.request.expires_at)
                if current >= expires_at:
                    matching.status = "expired"
                    self._audit(
                        "expired",
                        invocation,
                        current,
                        approval_id=matching.request.approval_id,
                        reason="approval_expired",
                    )
                elif matching.status == "approved":
                    return ToolPolicyDecision("denied", "approval_id_required", matching.request)
                elif matching.status == "rejected":
                    matching.status = "consumed"
                    self._audit(
                        "denied",
                        invocation,
                        current,
                        approval_id=matching.request.approval_id,
                        reason="approval_rejected",
                    )
                    return ToolPolicyDecision("denied", "approval_rejected")
                elif matching.status == "pending":
                    return ToolPolicyDecision("pending", "approval_required", matching.request)

            created_at = current.isoformat()
            expires_at = (current + timedelta(seconds=self._approval_ttl_seconds)).isoformat()
            approval_id = str(uuid.uuid4())
            request = ToolApprovalRequest(
                approval_id=approval_id,
                tool_name=invocation.tool_name,
                risk=policy.risk,
                project=invocation.project,
                policy_version=POLICY_VERSION,
                invocation_digest=invocation_digest,
                arguments=self._preview_arguments(invocation.arguments),
                created_at=created_at,
                expires_at=expires_at,
            )
            self._records[approval_id] = _ApprovalRecord(
                request=request,
                session_id=invocation.session_id,
                invocation_digest=invocation_digest,
                arguments=stored_arguments,
            )
            self._audit(
                "approval_requested",
                invocation,
                current,
                approval_id=approval_id,
                reason="write_requires_approval",
            )
            return ToolPolicyDecision("pending", "approval_required", request)

    def consume(
        self,
        approval_id: str,
        *,
        session_id: str,
        tool_name: str,
        project: str | None,
        now: datetime | None = None,
    ) -> ToolPolicyDecision:
        current = self._utc(now)
        with self._lock:
            record = self._records.get(approval_id)
            if record is None:
                return ToolPolicyDecision("denied", "approval_not_found")
            if not hmac.compare_digest(record.session_id, session_id):
                self._audit_record("execution_denied", record, current, reason="session_mismatch")
                return ToolPolicyDecision("denied", "session_mismatch")
            if record.request.tool_name != tool_name or record.request.project != project:
                self._audit_record("execution_denied", record, current, reason="scope_mismatch")
                return ToolPolicyDecision("denied", "scope_mismatch")
            if record.request.policy_version != POLICY_VERSION:
                self._audit_record("execution_denied", record, current, reason="stale_policy_version")
                return ToolPolicyDecision("denied", "stale_policy_version")
            if current >= datetime.fromisoformat(record.request.expires_at):
                record.status = "expired"
                self._audit_record("expired", record, current, reason="approval_expired")
                return ToolPolicyDecision("denied", "approval_expired")
            if record.status != "approved":
                self._audit_record("execution_denied", record, current, reason=f"approval_{record.status}")
                return ToolPolicyDecision("denied", f"approval_{record.status}")
            record.status = "consumed"
            receipt = self._receipt(record)
            self._audit_record(
                "executed_authorized",
                record,
                current,
                reason="exact_intent_match",
                receipt=receipt,
            )
            return ToolPolicyDecision(
                "allowed",
                "exact_intent_match",
                receipt=receipt,
                arguments=record.arguments,
            )

    def decide(
        self,
        approval_id: str,
        *,
        session_id: str,
        approve: bool,
        now: datetime | None = None,
    ) -> ToolApprovalRequest:
        current = self._utc(now)
        with self._lock:
            record = self._records.get(approval_id)
            if record is None:
                raise KeyError("Approval request was not found.")
            if not hmac.compare_digest(record.session_id, session_id):
                self._audit_record("decision_denied", record, current, reason="session_mismatch")
                raise PermissionError("Approval request belongs to a different session.")
            if current >= datetime.fromisoformat(record.request.expires_at):
                record.status = "expired"
                self._audit_record("expired", record, current, reason="approval_expired")
                raise TimeoutError("Approval request has expired.")
            if record.status != "pending":
                raise ValueError(f"Approval request is already {record.status}.")
            record.status = "approved" if approve else "rejected"
            record.approved_at = current.isoformat()
            self._audit_record(
                "approved" if approve else "rejected",
                record,
                current,
                reason="explicit_user_decision",
            )
            return record.request

    def _matching_record(self, invocation: ToolInvocation, digest: str) -> _ApprovalRecord | None:
        for record in reversed(list(self._records.values())):
            if (
                record.session_id == invocation.session_id
                and record.invocation_digest == digest
                and record.status in {"pending", "approved", "rejected"}
            ):
                return record
        return None

    def _invocation_digest(self, invocation: ToolInvocation) -> str:
        payload = {
            "arguments": invocation.arguments,
            "policy_version": invocation.policy_version,
            "project": invocation.project,
            "session_id": invocation.session_id,
            "tool_name": invocation.tool_name,
        }
        canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)
        return hmac.new(self._secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _preview_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
        preview = dict(arguments)
        summary = preview.pop("summary", None)
        if summary is not None:
            summary_text = str(summary)
            preview["summary_chars"] = len(summary_text)
            preview["summary_sha256"] = hashlib.sha256(summary_text.encode("utf-8")).hexdigest()
        sources = arguments.get("sources")
        if isinstance(sources, list):
            safe_sources = []
            for source in sources:
                if not isinstance(source, dict):
                    continue
                content = str(source.get("content", ""))
                safe_sources.append(
                    {
                        "chunk_id": source.get("chunk_id"),
                        "path": source.get("path"),
                        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    }
                )
            preview["sources"] = safe_sources
        return preview

    def _receipt(self, record: _ApprovalRecord) -> str:
        payload = f"{record.request.approval_id}:{record.invocation_digest}:{record.approved_at}:consumed"
        return hmac.new(self._secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _utc(value: datetime | None) -> datetime:
        current = value or datetime.now(UTC)
        if current.tzinfo is None:
            return current.replace(tzinfo=UTC)
        return current.astimezone(UTC)

    @staticmethod
    def _session_hash(session_id: str) -> str:
        return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]

    def _audit(
        self,
        event: str,
        invocation: ToolInvocation,
        current: datetime,
        *,
        reason: str,
        approval_id: str | None = None,
        receipt: str | None = None,
    ) -> None:
        self._write_audit(
            {
                "event": event,
                "at": current.isoformat(),
                "approval_id": approval_id,
                "tool_name": invocation.tool_name,
                "project": invocation.project,
                "policy_version": invocation.policy_version,
                "session_hash": self._session_hash(invocation.session_id),
                "invocation_digest": self._invocation_digest(invocation),
                "reason": reason,
                "receipt": receipt,
            }
        )

    def _audit_record(
        self,
        event: str,
        record: _ApprovalRecord,
        current: datetime,
        *,
        reason: str,
        receipt: str | None = None,
    ) -> None:
        self._write_audit(
            {
                "event": event,
                "at": current.isoformat(),
                "approval_id": record.request.approval_id,
                "tool_name": record.request.tool_name,
                "project": record.request.project,
                "policy_version": record.request.policy_version,
                "session_hash": self._session_hash(record.session_id),
                "invocation_digest": record.invocation_digest,
                "reason": reason,
                "receipt": receipt,
            }
        )

    def _write_audit(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

