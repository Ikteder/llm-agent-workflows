# Grounding Receipts Reference Review

Date: 2026-10-08

## User and problem

Research engineers use this project to answer questions over experiment reports, logs, and metrics. The current API returns source chunks, but its 25-question evaluator only checks for an expected filename and answer keywords. A filename can still resolve after content changes, a source list can be reordered without detection, and the answer does not consistently bind claims to source tokens. This makes a passing evaluation weaker than the README implies.

## Current reference comparison

| Reference | Intended user and core capability | Current evidence inspected | Integration surface | License and contribution rules | Limitation relevant here |
|---|---|---|---|---|---|
| [Ragas](https://github.com/vibrantlabsai/ragas) | LLM application teams evaluating RAG and agent systems with generated tests and judge or non-judge metrics | Repository, current docs for context precision, source tree, activity, issues and pull requests | Python metrics, datasets, LangChain/LangGraph/LlamaIndex and observability integrations | Apache-2.0; fork and pull-request workflow | It provides ID-based and non-LLM context precision, but it is an evaluation framework rather than an application runtime contract that binds each response to immutable local chunk digests |
| [DeepEval](https://github.com/confident-ai/deepeval) | Developers testing RAG, agents, and conversational systems | Repository, RAG metric docs, 2026 changelog, contextual-precision discussion, source, current activity | Python and TypeScript metrics, pytest workflow, framework integrations, hosted Confident AI option | Apache-2.0; fork and pull-request workflow with Poetry development setup | CitationFaithfulness and RAG metrics are valuable, but most semantic checks use a model judge; current discussion also documents why positional retrieval quality can be obscured when a judge effectively reorders evidence |
| [TruLens](https://github.com/truera/trulens) | Teams tracing and evaluating LLM applications and agents | Repository, RAG Triad docs, template source, current issues, activity, contribution guide | OpenTelemetry spans, provider packages, LangChain/LangGraph and LlamaIndex integrations | MIT; issue-first contribution guidance, CLA, standards certification | Rich trace and judge surfaces add observability, but they do not make this application's bundled source chunks content-addressed or detect later local corpus mutation by themselves |
| [Applied ML](https://github.com/eugeneyan/applied-ml) and the original [Google production-data paper](https://research.google/pubs/data-management-challenges-in-production-machine-learning/) | Discovery map for production ML lessons; original paper frames data validation, debugging, understanding, and enrichment as pipeline concerns | Index entry and original 2017 ACM publication page and abstract | Problem-framing evidence, not a runtime dependency | Applied ML is MIT; the linked publication is cited as research, not copied code | The production data-management pattern is relevant to retrieved evidence, but the paper does not specify an LLM citation receipt format |

Repository metadata was checked through the GitHub API on 2026-10-08. Ragas reported Apache-2.0 and a latest push date of 2026-02-24. DeepEval reported Apache-2.0 and a latest push date of 2026-10-07. TruLens reported MIT and a latest push date of 2026-10-06. Counts of open issues can include pull requests and were not used as quality evidence.

## Evidence-based gap

The local project needs a small runtime provenance contract before it needs another broad evaluation framework. The useful gap is to bind the exact retrieval order and exact chunk bytes used for an answer into a deterministic receipt, expose resolvable answer citations, and provide an offline verifier that detects missing, mutated, substituted, or reordered evidence.

This is not a semantic entailment judge. It answers the narrower and prerequisite question: "Can this response prove which exact local evidence it used, in which order, and whether that evidence still matches?"

## Chosen vertical slice

- content-address each ingested chunk with SHA-256 and a canonical repository-relative URI;
- attach stable response-local citation tokens and retrieval ranks;
- return a versioned grounding receipt and an explicit citation-integrity audit in the API;
- cite deterministic answer paths consistently;
- verify receipts against a supplied source set without a model or network call;
- compare the receipt verifier with the previous filename-only baseline on a versioned synthetic corpus;
- document that integrity and provenance do not prove semantic entailment or truth.

## License and inspiration boundary

The implementation is independent MIT code in the existing project. No Ragas, DeepEval, TruLens, or Google source code or prompts are copied. Their evaluation and production-data patterns informed the gap analysis only.
