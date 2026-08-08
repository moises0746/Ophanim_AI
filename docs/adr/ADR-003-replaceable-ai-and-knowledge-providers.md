# ADR-003: Replaceable AI and Knowledge Providers

Status: Accepted

## Decision

LM Studio, Ollama, AnythingLLM and cloud model providers are adapters behind Ophanim-owned contracts. Ophanim domain/application code requests capabilities and knowledge operations rather than importing provider internals.

## Consequences

- provider upgrades/replacement do not redefine product architecture;
- local/private and cloud routing can coexist;
- vendored AnythingLLM/Ollama code remains isolated from first-party product logic.
