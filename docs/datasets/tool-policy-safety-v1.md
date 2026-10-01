# Dataset card: tool-policy-safety-v1

Date: 2026-10-01

## Summary

`benchmarks/tool-policy-cases-v1.json` is a twelve-case synthetic regression corpus for the local tool policy. It covers a permitted read, an unapproved write, exact approval, argument mutation, replay, cross-session use, expiry, unknown tool, unknown project, path traversal, explicit rejection, and stale policy version.

## Source, version, and license

- Source: independently authored synthetic cases
- Version: schema 1, dated 2026-10-01
- License: CC0-1.0 as declared in the corpus
- External data: none

No upstream issue text, prompts, production logs, credentials, private paths, or model outputs are included.

## Labels and baseline

Every case expects a safe policy outcome. The exact-intent evaluator checks the production policy engine or the shared path-containment function. The comparison baseline represents a weak session policy that remembers only an approved tool name.

## Leakage and evaluation limits

The corpus was designed with knowledge of the implementation requirements and is used as regression evidence. It is not an independent security evaluation, a prevalence estimate, a fuzzing campaign, or a penetration test. Passing all cases does not establish authentication, multi-tenant isolation, operating-system sandboxing, or production safety.

## Quality concerns

- Cases are small and deterministic.
- There is one write tool and one filesystem boundary.
- Concurrency, distributed approval stores, clock skew, database isolation, and malicious authenticated users are not represented.
- The name-only baseline is intentionally simple and is not presented as any named framework's behavior.

## Next dataset improvement

Add property-based canonicalization cases, concurrent decision and consumption races, restart behavior, and externally authored cases. Keep the expected outcome reviewable without a model judge.

