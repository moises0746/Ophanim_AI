# ADR-007: Event-Driven Assistant Animation

Status: Accepted

## Decision

The animated Ophanim Assistant is driven by deterministic AssistantState and AgentActivity events emitted by Ophanim Core. The LLM never directly controls visual animation state.

## Consequences

- UI behavior is testable and reproducible;
- animation reflects real backend state;
- reduced-motion and accessibility modes are possible;
- the Agent Mesh can visualize orchestration without exposing hidden chain-of-thought.
