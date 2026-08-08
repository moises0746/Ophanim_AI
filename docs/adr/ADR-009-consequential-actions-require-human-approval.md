# ADR-009: Consequential Actions Require Human Approval

Status: Accepted

## Context

Ophanim may eventually send, publish, upload, delete, overwrite, install, deploy, restart, retry, purchase, change credentials or permissions, or mutate production systems. These operations can create financial, security, legal, operational, or reputational harm.

## Decision

Consequential, production, and state-changing actions require explicit human approval before execution. Approval is bound to approver identity, task, normalized action and parameters, destination/resource, environment, risk, expiry, and current preconditions. Changed parameters invalidate approval. Approval does not replace deterministic post-action verification, evidence, audit, or rollback planning.

## Rationale

Exact human authorization preserves accountable control at the point where impact becomes material and prevents broad consent from becoming unrestricted autonomy.

## Consequences

- Drafting and recommending do not imply permission to execute.
- Approval requests must clearly present action, destination, impact, and relevant evidence.
- Replayed, expired, ambiguous, or mismatched approvals are denied.
- MVP write-capable tools remain disabled under ADR-014.

## Rejected Alternatives

- Broad standing consent for consequential actions: rejected as insufficiently specific.
- Model-determined approval: rejected because models cannot authorize on the user's behalf.
- Approval after execution: rejected because it cannot prevent harm.
- Approval as the only control: rejected because policy, scope, verification, and rollback remain necessary.

## Security Impact

Approver authentication, integrity binding, anti-replay, expiry, authorization, audit, and fail-closed behavior are mandatory. UI or transport failure must not default to approval.

## Operational Impact

Tasks may pause while awaiting approval and must handle expiry, cancellation, denial, and stale preconditions. Emergency stop remains available.

## Testing Impact

Tests must cover grant, denial, expiry, replay, tampering, parameter/destination/environment changes, unauthorized approvers, cancellation, verification failure, and audit integrity.

## Follow-up and Deferred Work

Define approval schemas, UX, persistence, policy, verification, idempotency, and rollback contracts before Phase 8 mutations. This ADR enables no write action.
