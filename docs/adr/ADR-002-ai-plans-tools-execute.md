# ADR-002: AI Plans, Deterministic Tools Execute

Status: Accepted

## Decision

Models may analyze, plan, classify, summarize and recommend. External side effects are executed only by deterministic, allowlisted tools behind typed contracts and policy checks.

## Consequences

- no model receives arbitrary shell/SQL/browser/filesystem authority;
- tool inputs are validated and auditable;
- sensitive actions can be paused for approval;
- deterministic verification is preferred over model self-reporting.
