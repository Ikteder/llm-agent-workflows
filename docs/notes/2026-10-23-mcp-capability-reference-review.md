# MCP Capability Approval Reference Review

Date: 2026-10-23

## Seeded selection

- Seed: `20261023` using Python `random.Random`.
- Mode roll: `0.2529479731947105`, selecting the 40% improve-existing branch.
- Previous completed scheduled focus areas: 6, 2, and 5.
- Eligible focus areas: 1, 3, 4, and 7.
- Seeded eligible index: 1, selecting focus area 3, tool use, MCP, connectors, permissions, sandboxing, and interoperability.
- Project: `llm-agent-workflows`. Its last scheduled improvement was 2026-10-08, outside the subsequent SchemaRoute, AgentTrace Canary, and intervening completion work. The separate dirty primary checkout is not used.

## User and problem

Agent-platform engineers need to pause an external side-effecting tool call, show a reviewer what will run, and safely resume later. This project already binds local tool approvals to exact server-held arguments. It does not bind the identity and advertised definition of an external capability. MCP allows a tool list to change and modern framework adapters cache, prefix, filter, and translate those definitions. A name-stable capability can therefore drift between review and execution.

## Current reference comparison

| Reference | User and capability | Primary evidence inspected on 2026-10-23 | License and contribution rules | Integration surface | Relevant limitation |
|---|---|---|---|---|---|
| [MCP specification and tools contract](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/draft/server/tools.mdx) plus [Python SDK](https://github.com/modelcontextprotocol/python-sdk) | Protocol and SDK authors building interoperable tool clients and servers | Draft tool specification at commit `dae694f61a31`; tool catalogs may change, advertise `listChanged`, vary by authorization, and support caching. Python SDK v2 source/docs at `2af9e3089ac6`, current stdio and Streamable HTTP surfaces, migration guide, issues, releases, tests, and contribution guide | Specification repository is transitioning MIT to Apache-2.0, with non-spec documentation CC-BY-4.0; Python SDK is MIT and accepts guided contributions | `tools/list`, list-change notifications, pagination/caching, `tools/call`, SDK clients and servers | The protocol tells clients that capabilities can change and recommends human control, but it does not define an application approval receipt that binds a reviewed call to a particular observed tool definition |
| [OpenAI Agents Python MCP integration](https://openai.github.io/openai-agents-python/mcp/) | Agent developers using local or hosted MCP servers with filtering, approvals, guardrails, metadata, and traces | Docs/source at repository commit `0dc4cf152bff`, current activity, MCP caching and invalidation, server-prefixed names, local and hosted approval paths, advisory annotation warning, issues, tests, and security-focused contribution rules | MIT; non-collaborators are directed to issues rather than pull requests | Hosted MCP, stdio, SSE, Streamable HTTP, `require_approval`, tool filters, guardrails, `_meta`, tracing | Local MCP approval policy can inspect a tool definition but not call arguments or call ID; caching is optional; the SDK does not expose a reusable content-minimized before/after capability receipt for application-owned durable review |
| [Pydantic AI deferred tools and MCP toolsets](https://github.com/pydantic/pydantic-ai/blob/main/docs/deferred-tools.md) | Application developers composing argument-aware toolsets and deferred human approval | Docs/source at commit `dd82a00ae3ef`, MCP client metadata and schema surfaces, current issues and security advisories, and open issue [#5536](https://github.com/pydantic/pydantic-ai/issues/5536) documenting an approval boolean with no nonce, signature, call binding, or TTL in one durable boundary | MIT; contribution guide and repository instructions require focused tests and documentation | `ApprovalRequiredToolset`, deferred request/result IDs, MCP toolsets, tool definitions, metadata, approval metadata | The docs explicitly say approval is not authorization against an untrusted client. Tool-call IDs bind responses inside the framework, but there is no portable receipt proving that the resumed external server/tool definition equals the reviewed one |
| [LangChain MCP tools](https://github.com/langchain-ai/docs/blob/main/src/oss/langchain/mcp/tools.mdx) and [core MCP issue #40072](https://github.com/langchain-ai/langchain/issues/40072) | LangChain and LangGraph developers adapting MCP catalogs into agent tools | Current core repository at `b15a385cb1aa`, beta MCP docs, recent releases, issues and pull requests. The former adapter repository was archived on 2026-09-17 after migration to core. Current metadata includes serving-server identity, annotations, `_meta`, schema conversion, prefixes, and cache controls | MIT; issue templates and focused contribution workflow; the archived adapter accepts no changes | `MCPAdapter.list_tools`, server-prefixed names, tool metadata, human-in-the-loop middleware, cache modes | Metadata can support a local comparison, but approval examples key on adapted names and current definitions; the docs warn that an unprefixed key can miss the gate. No deterministic approval-time capability receipt or drift benchmark is supplied |
| [Applied ML](https://github.com/eugeneyan/applied-ml) as discovery map, original [Amazon data-quality paper](https://www.amazon.science/publications/automating-large-scale-data-quality-verification), and [Deequ](https://github.com/awslabs/deequ) | Production ML teams turning implicit input assumptions into explicit pre-consumption checks | Applied ML data-quality index, the original 2018 publication page/paper, Deequ source, tests, activity, issues, license, and contribution guide | Applied ML is MIT; Deequ is Apache-2.0 | Declarative constraints verified before downstream consumption | The relevant pattern is explicit, testable invariants before a downstream action. It is problem-framing evidence, not an MCP solution, and no Amazon result is claimed as locally reproduced |

The GitHub API showed current activity for all four implementation references on 2026-10-23/24 UTC. None publishes a benchmark for approval-time versus execution-time tool-definition drift. Stars and issue counts were inspected only as navigation metadata and are not treated as evidence of correctness.

## Evidence-based gap

Existing systems have the pieces: tool definitions, server metadata, namespacing, caching, list-change notifications, call IDs, and approval hooks. The local system already has exact arguments, expiry, HMAC binding, and one-time consumption. The missing application-level contract is a content-minimized receipt that records the capability the reviewer actually saw and compares it with a fresh observation immediately before consuming approval.

The selected slice adds value in at least four dimensions:

- correctness: schema and tool-definition changes are not silently ignored;
- security: server swaps, description changes, and advisory metadata changes fail closed;
- interoperability: one normalized receipt works with MCP-shaped definitions independent of agent framework;
- privacy and auditability: evidence is hashed and sectioned instead of copying descriptions or schemas into logs.

## Impact gate

| Check | Evidence |
|---|---|
| Real problem | Durable human approval for side-effecting external tools can outlive a cached or changed capability definition |
| Current evidence | MCP explicitly permits catalog changes; OpenAI and LangChain expose caching and metadata; Pydantic documents approval trust boundaries and an open durable-binding hardening issue |
| Original value | Adds correctness, security, interoperability, and content-minimized audit evidence to the existing exact-intent policy |
| Measurability | Authored mutation corpus versus a declared name-and-arguments baseline, plus direct policy integration tests |
| Finishability | One small dependency-free module, optional policy integration, deterministic evidence, and documentation |
| Maintainability | Typed dataclasses, stable finding codes, canonical JSON, no new runtime dependency, backward-compatible local path |
| License fit | Independent MIT implementation; no reference source, fixtures, or prompts copied |

## Chosen vertical slice

Build capability snapshots and deterministic receipts, compare a fresh observation at approval consumption, deny missing or drifted evidence without consuming the approval, and demonstrate the difference on a versioned synthetic corpus. Do not implement a transport, live connector, or framework fork.

## License and inspiration boundary

All implementation and fixtures are independently authored under this project's MIT license. The MCP shape is an interoperability interface. Reference projects and Deequ informed requirements and comparison only; no source, test fixture, benchmark, or company result is copied.
