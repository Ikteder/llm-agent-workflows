# Tool policy verification

Date: 2026-10-01

## Environment

- Operating system: Windows
- Python: 3.14.7 for the local full suite and package build
- Model or provider calls: none
- Paid-provider cost: USD 0.00

## Deterministic results

Initial implementation verification:

| Check | Result |
|---|---|
| Existing plus new Pytest suite | 18 passed in 0.70 seconds |
| Policy corpus | exact-intent 12/12; tool-name-only baseline 5/12 |
| Python compilation | passed for `app`, `scripts`, and `tests` |
| SVG parsing | passed |
| Ruff | passed for `app`, `scripts`, and `tests` |
| Package build | source distribution and wheel built for version 0.2.0 |
| Isolated wheel install | import reported version 0.2.0 and policy 2026-10-01.v1 |
| Isolated dependency check | no broken requirements |
| Isolated vulnerability audit | no known vulnerabilities; the unpublished local package was skipped |
| README style | zero em dash characters |
| Browser desktop flow | pending call, explicit approval, report write, and approval removal observed |
| Browser narrow layout | 390 by 844; document and body widths both equaled 390 pixels |

The API test proves the end-to-end sequence: a report request returns HTTP 409 with a pending exact invocation, an explicit decision approves that ID, the resumed request writes the report, and replay of the consumed ID returns HTTP 403. Live browser QA repeated the same successful pause and approval flow through Streamlit. The approval preview exposed the tool, project, title, question, content hashes, summary hash and size, expiry, and invocation digest without exposing full retrieved content in the approval payload.

## Interpretation

The seven-case improvement over the name-only baseline comes from argument binding, single-use state, session scope, expiry, project scope, path containment, and policy-version binding. The baseline is implementation-aligned and intentionally weak. These results are regression evidence only.

## Observed limitations

- The corpus is synthetic and authored alongside the implementation.
- The in-memory approval store does not survive a process restart or coordinate across replicas.
- The keyed digest provides application integrity, not user identity, authentication, authorization, or operating-system sandboxing.
- Browser console history retained expected disconnect messages from deliberate service restarts during QA; the final loaded flow completed successfully.

