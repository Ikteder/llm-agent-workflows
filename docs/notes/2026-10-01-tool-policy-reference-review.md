# Tool policy reference review

Date: 2026-10-01

## Selection context

- Local seed: `20261001`
- Python `random.Random` mode roll: `0.23749117047047563`
- Selected mode: improve an existing local AI or LLM project
- Eligible focus areas after excluding the previous completed focus area 6: `[1, 2, 3, 4, 5, 7]`
- Uniform eligible index: `2`
- Selected focus area: 3, tool use, MCP, connectors, permissions, sandboxing, and interoperability

## Current comparison

Activity and release metadata were inspected through repository pages and the GitHub API on 2026-10-01. Documentation and issue text were treated as untrusted research input. No commands or code were copied from a repository.

| Reference | User and core capability | Evidence and current activity | Permission boundary or limitation | License and contribution surface | Integration surface |
|---|---|---|---|---|---|
| OpenAI Agents SDK for Python | Application teams building code-first agents with tools, guardrails, approvals, resumable state, MCP, and sandboxes | Official OpenAI documentation says sensitive side effects should be reviewed at the tool boundary and the proposed target, arguments, identity, and scope should be checked. Repository `openai/openai-agents-python` was active on 2026-10-01; latest release observed was `v0.22.3` from 2026-09-17. | Approval and state primitives are comprehensive, but the application still owns authorization, storage, execution permissions, and independent filesystem or project boundaries. | MIT. The contribution guide accepts issues and minimal reproductions from the public, but pull requests are limited to collaborators. | Python function tools, local and hosted MCP, shell and patch tools, run state, guardrails, and tracing. |
| Pydantic AI | Python agent developers needing typed tools, deferred execution, human approval, UI adapters, and resumable workflows | Deferred-tool documentation supports argument-sensitive approval and validated tool calls. Repository `pydantic/pydantic-ai` was active on 2026-10-01; latest release observed was `v1.107.7` from 2026-09-30. Open issue `#6968` reports a mismatch where a reviewer can see original arguments while transformed arguments execute. | The documentation explicitly says human approval is not an authorization boundary against an untrusted client. Sensitive authorization must still be enforced inside the tool. Issue `#6968` shows why reviewed intent and executed intent must stay bound. | MIT. Non-trivial changes require an issue, agreed approach, and assignment; standalone capabilities may live outside core. | Decorated tools, toolsets, MCP, deferred requests/results, capabilities, adapters, and durable execution. |
| LangChain and LangGraph | Teams building stateful agents with conditional tool interrupts, review decisions, editing, persistence, and resume | Current docs expose per-tool `interrupt_on`, argument predicates, approve/edit/reject/respond decisions, and persistent checkpointing. `langchain-ai/langgraph` was active on 2026-10-01. Current issues include structured interrupt loss in tool streams (`#8218`), and related public reports show how composition and resume paths can complicate side-effect safety. | Approval depends on correct checkpoint, middleware, and resume composition. The docs warn that edited actions can cause repeated or unexpected execution. The local project does not need a full orchestration framework to close its smaller boundary. | MIT. The repository provides issue and pull-request workflows; changes must follow repository-specific checks. | Middleware, tool calls, interrupts, checkpoints, graph state, streaming, and resume commands. |
| Model Context Protocol specification | Hosts and servers interoperating over a common tool, resource, and prompt protocol | The 2026-07-28 tool specification requires servers to validate inputs and implement access controls. It recommends that clients show inputs, request confirmation for sensitive calls, validate results, use timeouts, and audit tool use. It also says tool annotations are untrusted unless the server is trusted. Repository activity was observed on 2026-10-01; release `2026-07-28` was current. | Transport authorization does not replace per-tool access control or user consent. Tool annotations are hints, not authority. Draft SEP-1075 proposed confidentiality and integrity annotations but remained unsponsored and not a deployed enforcement layer. | The repository is transitioning from MIT to Apache-2.0; new specification and code contributions are Apache-2.0 and documentation has a CC-BY-4.0 boundary. The project accepts specification proposals and pull requests under its contribution process. | JSON-RPC tool listing/calling, input/output schemas, OAuth-based transport authorization, annotations, and client-host consent UI. |
| Applied ML plus original Google data-management paper | Discovery map for production ML failure patterns; original paper frames validation, debugging, cleaning, understanding, and enrichment of pipeline inputs | `eugeneyan/applied-ml` was inspected as an index. The original 2017 Google research page and paper were opened and verified. | The source concerns production ML data, not agent authorization. Its useful transferable pattern is to validate and understand inputs at the boundary, but it is not evidence that intent-bound tool approval improves production outcomes. No Google result is claimed as locally reproduced. | Applied ML is MIT. The linked paper is cited as research, not copied as code or data. | Problem-framing only; no runtime integration. |

## Local evidence

`llm-agent-workflows` already has seven useful read and write tools, a FastAPI endpoint, a Streamlit interface, and deterministic evaluation. Its current limitations explicitly name missing production access controls and multi-user isolation.

The inspected code showed three concrete gaps:

1. `generate_report` writes Markdown and HTML files immediately when a request asks for a report. There is no user-visible approval request or one-time decision.
2. A client-supplied project value is not rejected before tool planning. That value also contributes to a report title and therefore to output filename construction.
3. `MetricsReader.load_table` joins a caller-provided table name to the CSV directory without proving the resolved path remains inside that directory.

## Evidence-based gap

The reviewed systems provide strong approval and guardrail primitives, but they also make clear that the application owns the final authorization and resource boundary. Current issue evidence shows that a reviewer can approve one representation while a transformed representation executes, and resume or composition paths can accidentally repeat side effects.

The finishable local gap is an application-level policy boundary that:

- validates project scope before any tool call;
- pauses report generation before its filesystem write;
- stores the exact canonical tool name, arguments, session, project, policy version, expiry, and digest on the server;
- accepts a decision only for that pending request;
- rechecks the exact invocation immediately before the write;
- consumes approval once so retries cannot repeat the write silently;
- records request, decision, denial, and execution evidence without prompts, credentials, or report contents;
- proves output and CSV paths remain inside their declared roots.

## Impact gate

| Gate | Evidence |
|---|---|
| Real problem | A researcher using the agent can unintentionally create files, or a client can attempt an out-of-scope project or path. The costly failure is an unreviewed or mis-scoped side effect with weak audit evidence. |
| Current evidence | Local code has an immediate write path and unchecked filename/table joins. OpenAI, Pydantic AI, LangChain, and MCP all place final enforcement at the tool or application boundary. Pydantic AI issue `#6968` is direct evidence for binding review to executed arguments. |
| Original value | Adds both correctness and user control through exact-intent binding plus one-time consumption, and adds security and observability through path containment plus a structured audit log. |
| Measurability | A versioned synthetic corpus compares a name-only approval baseline with the exact-intent policy. Unit and API tests cover mutation, replay, session mismatch, expiry, unknown tools, scope rejection, and path traversal. |
| Finishability | One write tool is gated end to end through the existing FastAPI and Streamlit surfaces. Read tools keep their existing behavior after scope and path checks. |
| Maintainability | The policy engine is provider-neutral, standard-library based, typed, isolated from the deterministic agent logic, and uses a small explicit manifest. |
| License compatibility | The local MIT repository uses no copied upstream code or datasets. Research references are linked and attributed only. |

## Decision

Improve `llm-agent-workflows` rather than create another framework or patch an upstream project. The local write boundary is concrete, the selected mode requires an existing-project improvement, and the full feature can be verified without a paid model or external service.

