# ADR-002: AI Plans, Deterministic Tools Execute

Status: Accepted

## Context

Models are useful for analysis, planning, classification, summarization, and recommendations, but their outputs are probabilistic and may be influenced by untrusted content. Giving a model unrestricted shell, SQL, browser, filesystem, or external-system authority would make validation, authorization, and verification unreliable.

## Decision

Models may analyze, plan, classify, summarize, and recommend. Only governed deterministic tools execute external operations or side effects. Tools are allowlisted, typed, scoped, policy checked, bounded by timeouts and retries, auditable, and approval-gated when required. Ophanim Core mediates execution.

## Rationale

Separating reasoning from execution makes authority explicit and permits deterministic validation, denial, cancellation, and verification at the tool boundary.

## Consequences

- Model output is a proposal, never proof that an action succeeded.
- Tool inputs and destinations require validation.
- Arbitrary execution interfaces are not valid product tools.
- Consequential results require deterministic verification and evidence.

## Rejected Alternatives

- Direct model access to shell, SQL, browser, or credentials: rejected as unsafe and unauditable.
- Prompt-only safety controls: rejected because prompts are not an execution boundary.
- Treating model self-reporting as verification: rejected because it is not deterministic evidence.

## Security Impact

This decision limits prompt-injection impact, credential exposure, scope escape, and unauthorized side effects. Untrusted tool output must remain data rather than instructions.

## Operational Impact

Tools need schemas, timeouts, bounded retries, cancellation, error classification, and health reporting. Provider or model failure can degrade planning without granting broader authority.

## Testing Impact

Tests must cover success, validation failure, denial, timeout, cancellation, retry, verification failure, prompt injection, and secret redaction. Negative tests must prove arbitrary execution is unavailable.

## Follow-up and Deferred Work

Define AgentProfile, Capability, ToolDefinition, policy, approval, and verification contracts in later authorized tasks. This ADR adds no tool runtime.
