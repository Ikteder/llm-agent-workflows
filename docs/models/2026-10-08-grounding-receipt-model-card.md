# Grounding Receipt Model and Provider Card

Date: 2026-10-08

## Model use

No model was used to create, verify, or benchmark grounding receipts. The feature uses deterministic Python, SHA-256, canonical JSON, regular-expression citation parsing, and the existing retrieval scores.

## Optional application model path

The existing application can call an OpenAI model only when both `LLM_BACKEND=openai` and `OPENAI_API_KEY` are configured. That path was not invoked during this run. No provider, model output, token count, or cost applies to the reported benchmark.

For optional model answers, the same source tokens are supplied in context and the returned answer is audited for token resolution. A resolved token does not prove that a model claim is supported by the associated text.

## Intended use

- reproducible local evidence identity;
- regression tests for content, URI, query, score, and order changes;
- a stable substrate for later semantic citation evaluation;
- user-visible debugging of which exact chunks were returned.

## Non-goals

- natural-language entailment;
- factual truth assessment;
- digital signatures or author identity;
- malicious-process or cryptographic collision defense;
- retrieval completeness or ranking quality;
- production security certification.

## Risks

The primary risk is over-interpretation. The product therefore names the result citation integrity and displays an explicit boundary in the README and evaluation visual. Optional model behavior remains nondeterministic and unevaluated in this run.

## Cost

Actual paid-provider cost: USD 0.00.
