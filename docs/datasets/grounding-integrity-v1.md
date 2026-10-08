# Grounding Integrity v1 Dataset Card

Date created: 2026-10-08

## Purpose

`benchmarks/grounding-integrity-v1.json` is a deterministic regression corpus for the application's grounding receipt verifier. It tests whether a verifier distinguishes an unchanged query and ordered evidence set from mutations that filenames alone cannot detect.

## Source and license

All twelve cases and both short source texts were created for this repository on 2026-10-08. They contain no user data, model output, third-party text, or externally licensed dataset material. They are released under the repository MIT license.

## Schema

Each case contains:

- `id`: stable case identifier;
- `mutation`: transformation applied to the valid two-source fixture;
- `expected_valid`: whether the resulting evidence package should verify.

The script constructs source objects, a receipt, and detailed findings at runtime. Generated results are stored in `docs/experiments/grounding-integrity-v1-results.json`.

## Cases

| Case | Change | Expected |
|---|---|---|
| valid | No mutation | valid |
| content-tamper | Changes retrieved text while retaining identity | invalid |
| missing-source | Removes one cited chunk | invalid |
| rank-reorder | Swaps the two retrieved chunks | invalid |
| uri-substitution | Changes the canonical source URI while keeping the filename | invalid |
| unexpected-source | Adds an uncited chunk | invalid |
| query-substitution | Verifies against a different query | invalid |
| receipt-id-tamper | Replaces the receipt identifier | invalid |
| evidence-digest-tamper | Replaces the ordered-evidence digest | invalid |
| duplicate-chunk | Repeats a current chunk identity | invalid |
| retrieval-score-tamper | Changes a recorded retrieval score | invalid |
| citation-token-tamper | Breaks the citation-to-rank binding | invalid |

## Leakage and baseline

The corpus was authored against the documented receipt invariants, so it is implementation-aligned and unsuitable as an independent benchmark. The filename-only baseline checks whether each expected basename is still present. It intentionally represents the prior project's effective provenance check, not a competitive external system.

## Quality concerns and non-goals

- The corpus is small and synthetic.
- Mutations are isolated rather than compositional.
- It does not contain paraphrased claims or human entailment labels.
- It does not test malicious SHA-256 collisions, compromised processes, digital signatures, remote stores, or distributed consistency.
- A perfect score does not measure source truth, retrieval recall, semantic faithfulness, or production reliability.
