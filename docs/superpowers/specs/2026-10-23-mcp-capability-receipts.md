# MCP Capability-Bound Approval Specification

Status: Approved for implementation on 2026-10-23

## Problem

The existing exact-intent policy binds a human approval to the application session, local tool name, arguments, project, policy version, expiry, and one-time consumption. That is sufficient for the current application-owned report tool, but it is incomplete for an external MCP tool. The MCP specification permits a server's tool catalog to change over time. A resumed approval can therefore retain the same visible tool name and arguments while the server identity, schema, description, annotations, or extension metadata have changed.

The intended user is an agent-platform engineer who pauses a side-effecting external tool call for review and later resumes it. The costly failure is executing a capability that is not the one the reviewer saw.

## Scope

Implement a provider-neutral, offline capability receipt and bind it into the existing approval lifecycle.

In scope:

- an application-assigned server identity, transport, and MCP protocol version;
- deterministic SHA-256 digests for the complete advertised tool definition and review-relevant sections;
- canonical JSON normalization that ignores object-key order but preserves array order and values;
- stable drift findings for server, transport, protocol, tool name, description, input schema, output schema, annotations, execution metadata, and extension metadata;
- optional capability evidence on `ToolInvocation` so current local tools remain backward compatible;
- a consume-time fail-closed comparison against a fresh observed capability;
- content-minimized audit records and approval previews;
- an authored mutation corpus, weak name-and-arguments baseline, JSON evidence, and SVG comparison;
- tests and the standard README, note, decision, dataset, experiment, and model/provider records.

Out of scope:

- implementing an MCP transport or trusting a server's self-declared identity;
- authenticating users, servers, DNS, TLS, OAuth, or credentials;
- proving that a tool implementation follows its schema or annotations;
- deciding whether a tool is safe, or replacing authorization inside the tool;
- invoking a live server, model, connector, or paid provider;
- modifying OpenAI Agents, Pydantic AI, LangChain, or the MCP specification.

## Design

`ToolCapability` holds an application-assigned `server_id`, a transport label, a protocol version, and one MCP-shaped tool object. `capability_receipt()` validates the bounded JSON value, computes section digests, and returns only safe identifiers, booleans, counts, and hashes. `compare_capabilities()` compares a reviewed snapshot with a fresh observed snapshot and emits a deterministic verdict and stable finding codes.

`ToolInvocation` gains an optional capability snapshot. The invocation HMAC includes the receipt digest. The approval request exposes a content-minimized receipt. The server retains the reviewed snapshot. `consume()` requires a fresh observed snapshot whenever the reviewed invocation carried one. Missing or changed evidence denies execution without consuming the approval; an exact semantic match consumes it once. Existing local invocations with no capability retain their current behavior.

The application, not the MCP server, assigns `server_id`. Tool annotations and `_meta` remain untrusted inputs. Binding them proves sameness, not truth.

## Baseline

The declared baseline binds only the tool name and arguments. It represents approval systems that resume a pending call by name without revalidating the server's advertised capability. It should accept unsafe mutations that preserve those two fields.

## Acceptance tests

1. Identical capability snapshots match and object-key reordering does not change any digest.
2. Changes to server identity, transport, protocol version, tool name, description, input schema, output schema, annotations, execution metadata, or `_meta` block execution with stable finding codes.
3. A capability-bound approval cannot be consumed without a fresh observed snapshot.
4. A mismatched observation does not consume the approval; a later exact observation may still consume it once.
5. Current local approval behavior and all existing tests remain green.
6. Approval previews and audit JSON never include raw descriptions, schemas, extension metadata, or arguments that are already minimized by policy.
7. At least 13 authored cases score exact expected verdicts; the receipt verifier materially outperforms the name-and-arguments baseline.
8. The benchmark JSON and SVG regenerate byte-identically.
9. Ruff, formatting, compilation, the full test suite, package build, isolated wheel install, dependency audit, SVG XML parse, README no-em-dash check, credential-pattern scan, and Git whitespace checks pass.
10. The public branch and `main` are updated only after local verification and remain aligned with the verified commit.

## Risks and controls

| Risk | Control |
|---|---|
| A receipt is mistaken for authorization or server authentication | Name it capability equality evidence and document that the application must establish server identity and tool-side authorization separately |
| Dynamic metadata creates unnecessary reapproval | Emit section-specific findings, retain hashes only, and document that callers should exclude truly per-call material before constructing the reviewed public capability |
| Canonicalization hides meaningful changes | Ignore only JSON object-key order; preserve all values and array order |
| Tool descriptions or `_meta` leak into logs | Store and emit digests and bounded summaries, never raw capability fields |
| A changed capability permanently destroys an approval | Fail before consumption so the application can reconnect to the reviewed capability or request a new approval |
| Existing local clients break | Make capability evidence optional and preserve the current API path when it is absent |
| The dirty primary checkout is overwritten | Implement in the clean existing worktree rooted at public commit `802178cfc5092d9902792dbed7342a4abe9a63e6`; do not modify the primary checkout |

## Publication plan

Commit the verified change on branch `codex/mcp-capability-receipts-20261023`. Push it to the existing public repository, then fast-forward public `main` only if remote `main` still matches the recorded starting commit. Preserve the separate dirty primary checkout. No upstream pull request is appropriate because this is an application-level integration pattern rather than a framework defect fix.
