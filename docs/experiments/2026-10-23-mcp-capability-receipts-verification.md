# MCP Capability Receipt Verification

Date: 2026-10-23

## Question

Does binding an approval to a reviewed MCP-shaped capability detect review-to-execution drift that a name-and-arguments approval misses?

## Environment

- Windows, America/Denver work run
- Python 3.14.8 for the local source suite (`.venv_verify`)
- Python 3.12 for the independent clean-wheel install
- Project virtual environment: pytest 9.1.1, Ruff 0.16.10, FastAPI 0.143.0, Pydantic 2.14.0
- Seed `20261023`
- No model, provider, network service, or paid API used for evaluation

## Method

The evaluator loads the 14-case `mcp-capability-drift-v1` corpus. Each case applies one deterministic mutation to a reviewed capability. The capability receipt compares application server identity, transport, protocol version, tool name, title, description, input and output schemas, annotations, execution metadata, `_meta`, and unknown contract fields. The declared baseline compares only tool name; call arguments are fixed across all cases.

## Results

| Evaluator | Correct | Accuracy |
|---|---:|---:|
| Name-and-arguments baseline | 3 / 14 | 21.43% |
| Capability receipt | 14 / 14 | 100% |

The baseline correctly handled two safe controls and the tool-name mutation. It missed eleven drift cases where the name and arguments remained stable. The receipt produced the expected section finding for every blocked case.

Raw results: `docs/experiments/mcp-capability-drift-v1-results.json`

Visual: `docs/graphics/mcp-capability-drift-v1.svg`

## Integration checks

The policy integration test showed:

- missing fresh evidence denied with `CAPABILITY_EVIDENCE_REQUIRED`;
- input-schema drift denied with `INPUT_SCHEMA_CHANGED`;
- neither denial consumed the approval;
- a later semantically identical observation with reordered object keys consumed the approval exactly once;
- raw tool descriptions did not enter the approval preview or audit log.

The final source suite passed 42 tests with one pre-existing Starlette deprecation warning about its `httpx` test client. A separately created Python 3.12 environment installed the initial built 0.4.0 wheel with resolved dependencies, passed `pip check`, imported the installed capability module from outside the source checkout, and matched an identical capability. Final wheel verification after closure fixes is recorded below.

Closure on 2026-10-24 retained the original run seed. Four additional regression tests cover invalid observation denial without consumption, a local approval reused for external execution, caller mutation of returned approval previews, and distinct approval IDs and HMACs after capability drift. Returned previews are now detached copies of server-held authority.

The receipt does not verify freshness itself. A trusted adapter must fetch the observation, bind its connection and identity to execution, and dispatch only the stored arguments. There is an unavoidable gap between observation and a remote effect unless the remote service enforces a version precondition; that server-side enforcement is outside this slice.

The generated SVG parsed as XML and an offline headless Chrome render at 1000 by 500 showed both bars, both score labels, title, explanatory line, and limitation note without clipping or overlap. Windows UI automation was not used after its browser URL safety check stopped the session.

## Final wheel verification

On 2026-10-24, rebuilt both distributions and reinstalled the final wheel into the independent Python 3.12 environment. Copied tests, scripts, and fixtures into a separate directory without application sources, verified `app.__file__` resolved inside `site-packages`, and passed all 42 tests plus `pip check`. Wheel SHA-256: `b93dbb6f4e5e71e8a6987c8a70b8c15c95dbe0b3f35c9c1afb80f42002e94097`.

The wheel does not bundle the demonstration corpus, so the application API tests used an explicitly configured absolute fixture data directory. This validates installation of the library; standalone packaged demonstration assets are an existing packaging limitation.

## Dependency audit note

The first local `pip-audit --local` run found five known issues in the pre-existing verification environment: one in `certifi 2026.7.22`, three in `filelock 4.0.12`, and one in `setuptools 84.0.0`. Those are verification or transitive environment packages, not imports added by this change. The environment was upgraded to `certifi 2026.10.23`, `filelock 4.2.4`, and `setuptools 84.2.1`, the project was reinstalled as 0.4.0, and the repeated audit reported no known vulnerabilities. The local project itself was skipped because it is not a published PyPI distribution.

## Interpretation

The result demonstrates deterministic behavior on an implementation-aligned synthetic corpus. It does not estimate production attack detection, false positives, interoperability across real frameworks, or server trust. The comparison is intentionally conservative: a changed public capability requires a new review.

## Artifact provenance

The JSON and SVG were generated locally by `scripts/evaluate_capability_receipts.py` from the authored MIT corpus. The SVG contains no third-party image, font file, or generated media asset.

## Verification commands

```powershell
.\.venv_verify\Scripts\python.exe -m pytest -q
.\.venv_verify\Scripts\python.exe -m ruff check app/agent/capability_receipts.py app/agent/tool_policy.py app/models/schemas.py scripts/evaluate_capability_receipts.py tests/test_capability_receipts.py tests/test_api.py
.\.venv_verify\Scripts\python.exe -m ruff format --check app/agent/capability_receipts.py app/agent/tool_policy.py app/models/schemas.py scripts/evaluate_capability_receipts.py tests/test_capability_receipts.py tests/test_api.py
.\.venv_verify\Scripts\python.exe -m scripts.evaluate_capability_receipts --json docs/experiments/mcp-capability-drift-v1-results.json --svg docs/graphics/mcp-capability-drift-v1.svg
.\.venv_verify\Scripts\python.exe -m compileall -q app scripts tests
.\.venv_verify\Scripts\python.exe -m build
.\.venv_verify\Scripts\python.exe -m pip check
.\.venv_verify\Scripts\python.exe -m pip_audit --local
git diff --check
```

Ruff checks target changed Python files. The initial repository-wide run exposed existing lint and formatting findings in unrelated files, which were not silently reported as passing or included in this patch.
