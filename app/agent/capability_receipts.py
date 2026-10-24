from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

MAX_CAPABILITY_BYTES = 262_144
MAX_NESTING_DEPTH = 32
RECEIPT_SCHEMA_VERSION = "1"

_SECTION_CODES = {
    "title": "TOOL_TITLE_CHANGED",
    "description": "TOOL_DESCRIPTION_CHANGED",
    "inputSchema": "INPUT_SCHEMA_CHANGED",
    "outputSchema": "OUTPUT_SCHEMA_CHANGED",
    "annotations": "TOOL_ANNOTATIONS_CHANGED",
    "execution": "TOOL_EXECUTION_CHANGED",
    "_meta": "TOOL_META_CHANGED",
}


@dataclass(frozen=True)
class ToolCapability:
    """Application-observed identity and one MCP-shaped advertised tool."""

    server_id: str
    transport: str
    protocol_version: str
    tool: dict[str, Any]


@dataclass(frozen=True)
class CapabilityReceipt:
    schema_version: Literal["1"]
    capability_digest: str
    identity_digest: str
    tool_digest: str
    server_id: str
    transport: str
    protocol_version: str
    tool_name: str
    section_digests: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_digest": self.capability_digest,
            "identity_digest": self.identity_digest,
            "tool_digest": self.tool_digest,
            "server_id": self.server_id,
            "transport": self.transport,
            "protocol_version": self.protocol_version,
            "tool_name": self.tool_name,
            "section_digests": dict(self.section_digests),
        }


@dataclass(frozen=True)
class CapabilityComparison:
    verdict: Literal["matched", "blocked"]
    findings: tuple[str, ...]
    reviewed: CapabilityReceipt
    observed: CapabilityReceipt


def clone_capability(capability: ToolCapability) -> ToolCapability:
    """Return a JSON round-tripped snapshot so caller mutation cannot rebind approval."""

    _validate_capability(capability)
    return ToolCapability(
        server_id=capability.server_id,
        transport=capability.transport,
        protocol_version=capability.protocol_version,
        tool=json.loads(_canonical_json(capability.tool)),
    )


def capability_receipt(capability: ToolCapability) -> CapabilityReceipt:
    _validate_capability(capability)
    identity = {
        "protocol_version": capability.protocol_version,
        "server_id": capability.server_id,
        "transport": capability.transport,
    }
    identity_digest = _digest(identity)
    tool_digest = _digest(capability.tool)
    sections = {
        key: _digest(
            {"present": key in capability.tool, "value": capability.tool.get(key)}
        )
        for key in _SECTION_CODES
    }
    combined = {
        "identity_digest": identity_digest,
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "tool_digest": tool_digest,
    }
    return CapabilityReceipt(
        schema_version="1",
        capability_digest=_digest(combined),
        identity_digest=identity_digest,
        tool_digest=tool_digest,
        server_id=capability.server_id,
        transport=capability.transport,
        protocol_version=capability.protocol_version,
        tool_name=str(capability.tool["name"]),
        section_digests=sections,
    )


def compare_capabilities(
    reviewed: ToolCapability,
    observed: ToolCapability,
) -> CapabilityComparison:
    reviewed_receipt = capability_receipt(reviewed)
    observed_receipt = capability_receipt(observed)
    findings: list[str] = []
    if reviewed.server_id != observed.server_id:
        findings.append("SERVER_ID_CHANGED")
    if reviewed.transport != observed.transport:
        findings.append("TRANSPORT_CHANGED")
    if reviewed.protocol_version != observed.protocol_version:
        findings.append("PROTOCOL_VERSION_CHANGED")
    if reviewed_receipt.tool_name != observed_receipt.tool_name:
        findings.append("TOOL_NAME_CHANGED")
    for section, code in _SECTION_CODES.items():
        if (
            reviewed_receipt.section_digests[section]
            != observed_receipt.section_digests[section]
        ):
            findings.append(code)
    known_fields = {"name", *_SECTION_CODES}
    reviewed_other = {
        key: value for key, value in reviewed.tool.items() if key not in known_fields
    }
    observed_other = {
        key: value for key, value in observed.tool.items() if key not in known_fields
    }
    if _digest(reviewed_other) != _digest(observed_other):
        findings.append("TOOL_DEFINITION_CHANGED")
    return CapabilityComparison(
        verdict="blocked" if findings else "matched",
        findings=tuple(findings),
        reviewed=reviewed_receipt,
        observed=observed_receipt,
    )


def _validate_capability(capability: ToolCapability) -> None:
    for label, value in (
        ("server_id", capability.server_id),
        ("transport", capability.transport),
        ("protocol_version", capability.protocol_version),
    ):
        if not isinstance(value, str) or not value.strip() or len(value) > 256:
            raise ValueError(
                f"{label} must be a non-empty string of at most 256 characters."
            )
    if not isinstance(capability.tool, dict):
        raise TypeError("tool must be a JSON object.")
    name = capability.tool.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 256:
        raise ValueError(
            "tool.name must be a non-empty string of at most 256 characters."
        )
    _check_depth(capability.tool, 0)
    encoded = _canonical_json(capability.tool).encode("utf-8")
    if len(encoded) > MAX_CAPABILITY_BYTES:
        raise ValueError(
            f"tool exceeds the {MAX_CAPABILITY_BYTES}-byte canonical limit."
        )


def _check_depth(value: Any, depth: int) -> None:
    if depth > MAX_NESTING_DEPTH:
        raise ValueError(
            f"tool exceeds the maximum nesting depth of {MAX_NESTING_DEPTH}."
        )
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("tool object keys must be strings.")
        for nested in value.values():
            _check_depth(nested, depth + 1)
    elif isinstance(value, list):
        for nested in value:
            _check_depth(nested, depth + 1)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError("tool must contain only JSON-compatible values.")


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("tool must contain finite JSON-compatible values.") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
