# Bind the Reviewed MCP Capability

Date: 2026-10-23

Status: Accepted

## Decision

An approval for an external tool may be consumed only when a fresh capability observation matches the reviewed application-assigned server identity, transport, protocol version, and complete advertised tool definition.

The comparison uses canonical JSON and section-specific SHA-256 digests. It ignores object-key order only. Description, title, schemas, annotations, execution metadata, `_meta`, and unknown top-level fields remain binding because each can change how the model, adapter, reviewer, or host interprets the capability.

Missing or changed evidence denies execution before marking the approval consumed. Existing application-owned tools can omit capability evidence and keep the prior exact-intent path.

## Why

Binding only the tool name and arguments assumes the name continues to identify the same server-side contract. MCP explicitly allows catalogs to change. Framework adapters also cache, rename, filter, namespace, and convert tool definitions. A reviewer should not unknowingly authorize a changed schema, prompt-facing description, destructive hint, or host extension.

An application-assigned server ID is used instead of a server-provided display name because a self-declared label is not a trust anchor.

## Alternatives rejected

- Bind only name and input schema: misses server swaps, description changes, output-contract changes, and host metadata changes.
- Trust `destructiveHint` as authorization: MCP annotations are advisory and come from the server.
- Automatically accept list-change notifications: notification is freshness evidence, not reviewer consent to a new capability.
- Embed raw definitions in audit logs: improves readability but unnecessarily copies potentially sensitive descriptions, schemas, and extension metadata.
- Add an MCP client dependency: unnecessary for the policy boundary; adapters can supply the observed MCP-shaped definition.

## Consequences

Some benign capability updates require a new approval. The section findings make that reason inspectable. Callers should keep per-call secrets and volatile transport data outside the public tool definition they submit for review. A matching receipt proves equality of two observations, not server authentication, tool implementation honesty, or authorization of the effect.
