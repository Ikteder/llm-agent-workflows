# Decision: Content-Addressed Grounding Receipts Before Semantic Judges

Date: 2026-10-08

## Decision

Add a deterministic runtime receipt that binds the normalized query to ordered source URIs, chunk identities, content SHA-256 digests, retrieval ranks, rounded scores, and answer citation tokens. Call the associated check citation integrity, not faithfulness.

## Context

The application already returned source objects and reported a 25/25 retrieval benchmark. That benchmark accepted an expected filename plus answer keywords. It could not show that the content behind the filename was unchanged or that the displayed citation order matched the evidence used for the answer.

Current RAG evaluation frameworks provide broad retrieval and semantic metrics. Adding another judge metric would not fix the local runtime identity gap. Semantic evaluation is also harder to make reproducible without model calls and human labels.

## Why this choice

- Content digests detect mutation that filenames miss.
- Canonical URIs make identity independent of absolute checkout paths.
- Ordered receipt entries preserve retrieval rank rather than allowing later reordering.
- A deterministic verifier runs offline and in CI with no provider credentials.
- The receipt can become the stable evidence layer beneath future semantic evaluation.

## Alternatives rejected

### Add only inline filename citations

Rejected because filenames are mutable labels and can collide across directories.

### Add an LLM faithfulness judge now

Rejected for this slice because a judge would not establish immutable evidence identity, introduces nondeterminism and cost, and needs independently labeled calibration data.

### Adopt a full evaluation framework

Rejected as the immediate implementation because Ragas, DeepEval, and TruLens solve broader evaluation and observability problems. The local gap is small and application-specific. Future adapters remain possible.

### Sign receipts

Deferred. A signature would require a key-management and identity model. Version 1 is explicit that receipts are unsigned integrity records, not authenticity or authorization evidence.

## Consequences

API responses are larger and expose digest metadata. Existing fields remain compatible. Retrieval score changes now invalidate receipts after rounding to twelve decimal places. The system can prove exact local evidence identity and order, but it still cannot prove that a generated claim is entailed, that a source is correct, or that the retrieval set is complete.
