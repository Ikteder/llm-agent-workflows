# Content-Addressed Grounding Receipts Specification

Status: Approved for implementation on 2026-10-08

## Problem

The application returns source objects but does not provide a stable, content-addressed contract linking an answer to the exact retrieved chunks. The current evaluator accepts filenames plus answer keywords, so content mutation, source substitution, and rank changes can remain invisible.

## Scope

Implement schema version 1 grounding receipts for the existing deterministic and optional-model answer paths.

In scope:

- canonical repository-relative source URIs;
- stable content and chunk SHA-256 digests;
- response-local citation tokens and retrieval ranks;
- a deterministic receipt identifier over query and ordered evidence;
- citation resolution checks for each response;
- offline verification against current chunks;
- a versioned synthetic integrity corpus, filename-only baseline, JSON results, and SVG comparison;
- API and Streamlit presentation;
- README, dataset, model, decision, experiment, and asset-provenance documentation.

Out of scope:

- proving semantic entailment for arbitrary generated prose;
- signing receipts with an external identity;
- remote document storage, vector-database versioning, or cross-service attestations;
- live paid-model evaluation;
- replacing Ragas, DeepEval, TruLens, or an observability platform.

## Design

Each ingested chunk receives a canonical `source_uri`, `content_sha256`, and stable `chunk_id`. Search results receive a one-based `retrieval_rank` and response-local token such as `S1`. The agent builds a versioned receipt from the normalized query digest and ordered citation entries. A verifier compares the receipt with supplied current chunks and reports missing chunks, digest mismatches, URI substitutions, and rank mismatches.

The response also includes a citation audit that checks whether every answer token resolves and whether sourced deterministic answers contain at least one citation. The audit name must use "integrity" rather than "faithfulness" because it does not prove entailment.

## Baseline

The previous implementation-aligned baseline treats a source as unchanged when its filename still appears. It cannot detect content mutation, same-name substitution, or retrieval-order changes.

## Acceptance tests

1. Rebuilding the same corpus produces identical chunk IDs and digests regardless of absolute checkout path.
2. Search results expose ordered ranks and citation tokens.
3. Deterministic retrieval, comparison, verification, metrics, log, and artifact answers include resolvable citation tokens when sources exist.
4. The API returns a schema-versioned receipt with a stable ID and a separate citation-integrity audit.
5. Offline verification accepts an unchanged source set and rejects missing, mutated, substituted, or reordered evidence with stable finding codes.
6. A minimum 12-case corpus reports exact expected outcomes for both the filename-only baseline and the receipt verifier.
7. Existing tests remain green; new provenance, API, and benchmark tests pass.
8. Ruff, compilation, package build, isolated wheel import, dependency consistency, vulnerability audit, SVG parsing, README no-em-dash check, and Git whitespace checks pass.
9. The README shows a verified comparison visual near the top and states that integrity is not semantic entailment or truth.

## Risks and controls

| Risk | Control |
|---|---|
| Users interpret a valid receipt as proof that the answer is true | Name the output citation integrity, document the boundary in API fields and README, and keep `grounded` semantics conservative |
| Absolute paths make hashes machine-specific | Hash canonical repository-relative URIs plus normalized content, never checkout roots |
| Float serialization changes receipt IDs | Round retrieval scores to a documented precision before canonical JSON hashing |
| Existing clients break on additional fields | Add optional or defaulted schema fields and preserve existing response fields |
| Optional model emits unknown citations | Audit rather than silently rewriting model output; expose unresolved tokens |
| Uncommitted memory work in the primary checkout is overwritten | Implement in an isolated worktree from published commit `85426c93b20c3506ef2b7a486af862d05b691921` |

## Publication plan

Commit the verified change on branch `codex/grounding-receipts-20261008`. Push it to the existing public repository only after local verification. Fast-forward public `main` only if it still matches the recorded starting commit. Preserve the separate dirty primary checkout untouched and document that boundary.
