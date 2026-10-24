# MCP Capability Drift v1 Dataset Card

Date: 2026-10-23

## Summary

`benchmarks/mcp-capability-drift-v1.json` is an authored deterministic regression corpus for changes between human review and execution of one external MCP-shaped tool.

## Source and license

- Source: independently authored synthetic cases in this repository.
- Version: schema 1, accessed and evaluated 2026-10-23.
- License: MIT with the project.
- Third-party data: none.
- Personal, customer, credential, prompt, or provider data: none.

## Schema

Each case contains:

- `id`: stable case identifier;
- `mutation`: deterministic transformation applied to the reviewed capability;
- `expected`: `matched` or `blocked`.

The evaluator owns one fixed base capability and applies the named transformation. Tool-call arguments remain unchanged in every case so the weak baseline isolates capability drift.

## Coverage

Fourteen cases cover two safe controls and changes to application server identity, transport, protocol version, tool name, title, description, input schema, output schema, annotations, execution metadata, extension metadata, and an unknown top-level contract field.

## Preprocessing and split

No preprocessing, training split, validation split, or test split is used. Cases are executed directly. Object keys are canonically sorted for hashing; arrays and values preserve their input semantics.

## Leakage and bias controls

The corpus is implementation-aligned and was written with the finding taxonomy in view, so it is not independent security evidence. The declared name-and-arguments baseline was fixed before measurement. No case is tuned from production failures or third-party private data.

## Quality concerns and mismatch

- One representative tool cannot cover all MCP revisions, adapters, auth contexts, transports, or extension conventions.
- Mutations are isolated and deterministic; real deployments can combine changes.
- Expected labels reflect a conservative reapproval policy, not a universal safety standard.
- The corpus measures exact contract equality, not whether a changed capability is malicious or whether an unchanged implementation behaves honestly.

## Intended use

Use for regression tests, CI, and explaining the difference between call binding and capability binding. Do not use it as a penetration-test result, framework ranking, production false-positive estimate, or compliance claim.
