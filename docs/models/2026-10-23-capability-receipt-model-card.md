# Capability Receipt Model and Provider Card

Date: 2026-10-23

## Model use

No language model, embedding model, classifier, model judge, or hosted inference provider is used by the capability receipt, comparison, corpus, tests, or visual.

## Deterministic method

The implementation validates bounded JSON-compatible input, canonicalizes JSON object keys, computes SHA-256 section and aggregate digests, and applies exact equality rules with stable finding codes. The existing approval engine adds its keyed HMAC over the invocation and capability digest.

## Intended use

- Bind an application review record to one observed MCP-shaped tool capability.
- Detect capability drift immediately before consuming an approval.
- Produce content-minimized evidence for tests and audit logs.

## Non-goals

- server or user authentication;
- authorization inside the tool;
- semantic risk classification;
- prompt-injection detection;
- malware or vulnerability detection;
- proof that a server implementation follows its advertised contract.

## Risks

Exact equality can require reapproval for benign edits. Stable digests do not identify who made an observation. SHA-256 collision resistance is relied on for compact evidence, while the existing HMAC secret remains an application deployment concern. Raw capability definitions can contain sensitive material before hashing, so adapters should keep credentials and per-call secrets outside tool metadata.

## Providers, tokens, and cost

- Providers: none.
- Models and versions: none.
- Input tokens: 0.
- Output tokens: 0.
- Actual paid-provider cost: USD 0.00.

## Export and reproducibility

The evidence exports are plain JSON and SVG. They can be regenerated offline with Python 3.11+ and the repository's existing environment. No model weights, API keys, network access, or paid account is required.
