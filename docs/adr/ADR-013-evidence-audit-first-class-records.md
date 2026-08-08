# ADR-013: Evidence and Audit as First-Class Records

Status: Accepted

## Context

Ophanim coordinates models, agents, tools, browser activity, policy decisions, approvals, and external data. Without durable provenance and audit records, users cannot verify conclusions, reconstruct consequential activity, or distinguish model claims from observed facts.

## Decision

Evidence and audit are first-class Ophanim records owned by Core. Evidence records preserve task/tool/source provenance, classification, integrity metadata, capture time, verification, and authorized artifact references. Audit records capture material task transitions, policy decisions, approvals, consequential tool actions, verification outcomes, and cancellation. Consequential approval and audit history uses append-only semantics. Records are sanitized and never include hidden chain-of-thought, credential values, or unrestricted raw private content.

## Rationale

First-class records make findings reviewable, actions attributable, failures diagnosable, and approval enforcement demonstrable.

## Consequences

- Results must distinguish evidence, inference, recommendation, and action status.
- Tool success is not claimed until deterministic verification succeeds.
- Large artifacts may be stored outside PostgreSQL with immutable references and hashes.
- Retention, redaction, export, and access policy require explicit design.

## Rejected Alternatives

- Logs alone as audit: rejected because operational logs lack durable domain semantics and access guarantees.
- Model summaries as evidence: rejected because summaries are interpretations, not provenance.
- Storing everything indefinitely: rejected due to privacy, cost, and minimization requirements.
- Exposing chain-of-thought for auditability: rejected; structured events and evidence provide accountable transparency.

## Security Impact

Evidence may contain sensitive data and prompt injection. Identity/data scope, classification, integrity, encryption, redaction, retention, and tamper-evident or append-only controls are required.

## Operational Impact

Storage growth, artifact lifecycle, retention, export, archival, integrity verification, and recovery require monitoring and policy.

## Testing Impact

Tests must cover provenance, hashes, authorization, redaction, append semantics, verification links, cancellation, partial failures, tampering, retention, and recovery.

## Follow-up and Deferred Work

Define exact Evidence, Artifact, AuditEvent, PolicyDecision, and ToolCall contracts plus retention/storage implementation in later tasks. No persistence is implemented here.
