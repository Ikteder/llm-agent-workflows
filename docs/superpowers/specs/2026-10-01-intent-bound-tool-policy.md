# Intent-bound tool policy implementation spec

Date: 2026-10-01
Status: approved for implementation

## Problem and intended user

Researchers use this local agent to inspect experiment evidence and generate report files. The current write tool executes as soon as the request reaches the matching branch. The user cannot inspect the exact side effect before it happens, and the application does not bind any approval to the precise invocation that later executes.

The intended user is a researcher or ML engineer running the FastAPI and Streamlit application locally or behind an authenticated internal service.

## Evidence-based gap

Current agent frameworks support approvals and interruptions, while their documentation still assigns authorization and resource isolation to the application. Current issue evidence also shows that approval, transformed arguments, checkpoint resume, and execution can diverge. This project needs a small application-owned boundary, not a new orchestration framework.

## Scope

1. Add an explicit tool manifest with read versus write risk, approval requirement, and policy version.
2. Add a server-held approval registry that binds a pending request to canonical arguments, session, project, policy version, expiry, and a keyed digest.
3. Require approval for `generate_report`; never create a report on the first request.
4. Add an API for approving or rejecting one pending request and expose the exact safe argument preview.
5. Re-evaluate the invocation immediately before the write and consume approval once.
6. Reject unknown project scopes before tool planning.
7. Contain generated report files and metrics-table reads within their configured roots.
8. Record JSONL audit events without prompts, source contents, report contents, or secrets.
9. Add Streamlit approval and rejection controls that repeat the original request only after a recorded decision.
10. Add a versioned policy corpus, a name-only baseline, JSON results, and an SVG comparison visual.

## Non-goals

- This is not authentication, role-based access control, OAuth, or a multi-tenant security claim.
- This does not make client-submitted approval trustworthy on an unauthenticated public deployment.
- This does not sandbox arbitrary code, shell commands, networks, containers, or third-party MCP servers.
- This does not integrate a paid model or change answer quality.
- This does not claim equivalence with OpenAI Agents SDK, Pydantic AI, LangChain, LangGraph, or MCP implementations.

## Acceptance tests

1. Existing grounded read questions still pass without approval.
2. A report request returns a pending approval and creates no Markdown or HTML report.
3. Approving the pending request and repeating the identical call creates exactly one report pair.
4. Replaying the consumed approval does not create another report and returns a new pending request.
5. Changing the title, question, source paths, project, session, or policy version cannot reuse the prior approval.
6. Rejected and expired approvals fail closed without a write.
7. Unknown tools and unknown projects are denied.
8. CSV and report path traversal inputs are rejected before filesystem access.
9. Audit events contain decision metadata and digests but no question, answer, source extract, API key, or report body.
10. The exact-intent evaluator scores every policy case correctly and exceeds the name-only baseline on the same versioned corpus.
11. All previous tests plus new unit, API, packaging, style, and dependency checks pass.
12. The README contains no em dash character and includes a meaningful generated policy-evidence visual near the top.

## Comparison baseline

The baseline represents a common weak policy: an approved tool name is allowed for the remainder of a session. It does not bind arguments, project, expiry, policy version, or single-use state. Both evaluators run against the same synthetic cases.

## Risks and controls

| Risk | Control |
|---|---|
| Approval endpoint is mistaken for authentication | Document that deployment still requires authentication and transport security; call the feature local application approval, not an authorization system. |
| Sensitive content leaks into audit logs | Log only event type, tool, session hash, project label, invocation digest, approval ID, policy version, timestamps, and reason codes. |
| A stale approval executes changed arguments | Canonicalize and digest the complete safe invocation, then compare again immediately before the write. |
| Retry repeats a side effect | Mark approval consumed before invoking the write and require a new approval for every later attempt. |
| Process restart loses decisions | Fail closed. Version 0.2 uses in-memory pending state and documents restart behavior; the append-only audit log is evidence, not resumable authority. |
| Path check differs across operating systems | Resolve both root and candidate, require containment with `Path.relative_to`, and test Windows-relevant separator inputs. |
| Approval expires during review | Use a short explicit TTL and expose expiry. Expired requests require a new review. |

## Publication plan

Update the existing MIT repository at `https://github.com/Ikteder/llm-agent-workflows`. Add implementation, tests, evaluation artifacts, documentation, and a generated SVG. Verify locally, commit intentionally, push only after all checks pass, then verify the public commit and CI result. No upstream pull request is planned because this is application-specific enforcement built without copied upstream code.

