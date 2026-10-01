# Model and provider card: tool policy improvement

Date: 2026-10-01

## Models and providers used

No model or paid provider was called to implement or evaluate the tool policy. The application test environment used its existing deterministic TF-IDF retrieval and extractive summarizer path.

Actual paid-provider cost: USD 0.00.

## Intended use

The policy protects application-owned tool execution independently of which model proposes a tool call. It binds reviewed intent after deterministic application validation and before the side effect.

## Non-goals

- It does not evaluate tool-selection quality for any LLM.
- It does not detect prompt injection with a model judge.
- It does not claim that a provider, agent SDK, or MCP server is secure.
- It does not make approval an authentication boundary.

## Reproducibility

All unit, API, and policy-corpus tests run without an API key. The optional existing OpenAI answer backend remains outside this improvement's evaluation and cost claims.

