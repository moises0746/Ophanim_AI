# ADR-009: Read-Only MVP and Approval-Gated Writes

Status: Accepted

## Decision

The MVP is read-only. Ophanim may investigate, retrieve, correlate, classify, summarize, recommend and draft. State-changing actions are excluded until a later phase with explicit policy, approval, verification and rollback contracts.

## Consequences

- first business slice is investigation rather than remediation;
- write-capable tools default disabled;
- approval UX can be designed before production mutation is enabled;
- risky automation cannot be introduced as incidental scope.
