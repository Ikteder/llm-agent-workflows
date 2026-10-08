# Grounding Receipts Verification

Date: 2026-10-08

## Environment

- Windows 11
- Python 3.14.7 local environment
- Project version 0.3.0
- Published starting commit: `85426c93b20c3506ef2b7a486af862d05b691921`
- Isolated worktree branch: `codex/grounding-receipts-20261008`

## Deterministic result

The versioned twelve-case corpus classified all cases correctly with grounding receipts. The filename-only baseline classified two cases correctly.

| Evaluator | Correct | Accuracy |
|---|---:|---:|
| Filename-only baseline | 2/12 | 16.67% |
| Grounding receipt verifier | 12/12 | 100% |

This is implementation-aligned mutation evidence. It is not a semantic citation benchmark or independent security assessment.

## Verified behaviors

- stable chunk identity across different absolute checkout roots;
- canonical repository-relative URIs;
- content mutation detection;
- missing, extra, duplicate, substituted, and reordered evidence detection;
- query, score, evidence-digest, receipt-ID, and citation-rank mismatch detection;
- answer citation resolution in the agent response;
- API-compatible optional response fields;
- no model or paid provider requirement.

## Commands and final outputs

- `python -m ruff check app tests scripts/evaluate_grounding_integrity.py`: passed with Ruff 0.16.10.
- `python -m compileall -q app tests scripts`: passed.
- `python -m pytest -q`: 22 passed in 0.45 seconds. Starlette emitted one deprecation warning about its current `httpx` TestClient adapter.
- Clean-environment `python -m pip check`: no broken requirements.
- Clean-environment `python -m pip_audit`: no known vulnerabilities; the unpublished local package itself was skipped because it is not on PyPI.
- `python -m scripts.evaluate_grounding_integrity ...`: receipt verifier 12/12; filename-only baseline 2/12.
- Existing 25-question evaluator logic: 25/25 remained correct and all 25 responses returned verified or not-applicable citation-integrity audits.
- FastAPI TestClient end-to-end request: HTTP 200, receipt `gr1-e2229ddca7634e030088bbd3`, verified integrity, seven returned sources.
- `python -m build`: built a 32,651-byte source archive and 29,738-byte wheel.
- Isolated wheel import: version 0.3.0 imported successfully. Wheel SHA-256: `0cbda86cd84f9280c8a64b18b1f27bf3f42b2f75b308d170951801b3c21faf67`.
- SVG XML parsing, secret-pattern scan, Git whitespace check, and README em-dash count all passed. README em-dash count: 0.
- Browser QA: the live Streamlit query displayed a resolvable receipt and cited-source tokens. At a 390 by 844 viewport, document `scrollWidth` equaled `clientWidth` at 390 pixels and the receipt remained visible. The sidebar collapsed correctly. Captured browser warnings and errors: 0.
- Visual QA: the generated SVG rendered its accessible title, 2/12 baseline, 12/12 receipt result, and semantic boundary without clipping after one label-contrast correction.

The machine-readable benchmark output is stored in `grounding-integrity-v1-results.json` in this directory.

## Known verification boundary

The local run uses Python 3.14.7. The existing public workflow uses Python 3.12. A broader workflow edit is not part of this change because the saved GitHub credential previously lacked workflow-file write scope. No live model, distributed store, signature, or independently labeled citation corpus is tested.
