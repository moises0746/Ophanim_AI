# Ophanim Abuse Cases

Each scenario assumes the attacker or failure is possible at the named boundary. Expected behavior is safe denial, bounded degradation, truthful state, and auditable evidence without secret disclosure.

| ID | Threat scenario | Control | Expected safe behavior | Audit/evidence expectation |
|---|---|---|---|---|
| AB-01 | Malicious website instructs an agent to reveal credentials. | Treat page as untrusted; dedicated profile; secret isolation; tool policy. | Ignore instruction; no secret enters page, model, event, or log; stop/deny if attempted. | Page/source, denied tool/policy decision, sanitized prompt-injection classification. |
| AB-02 | Poisoned knowledge document tells model to bypass policy. | Source scope/citations; content-data separation; Core policy boundary. | Treat as untrusted document; policy remains authoritative; finding carries limitation/provenance. | Source/evidence reference and blocked recommendation/tool request. |
| AB-03 | MCP server advertises dangerous tool as read-only. | Registered server identity; schema/risk review; allowlist; discovery ≠ authorization. | Deny or quarantine tool; no execution based on metadata alone. | Server/tool version, policy denial, malformed/risk evidence. |
| AB-04 | Compromised model produces unauthorized parameters. | Typed schema validation; normalized digest; policy/tool boundary; deterministic verification. | Reject request; no credential resolution or execution. | Model/provider version, validation failure, policy decision, no raw secret payload. |
| AB-05 | User asks for arbitrary SQL. | Purpose-built approved database tools; arbitrary SQL forbidden by SEC-005. | Refuse arbitrary query; offer bounded supported lookup if authorized. | User/task correlation and denial reason; no arbitrary query retained unnecessarily. |
| AB-06 | Browser redirects to an unapproved domain. | Domain/app allowlist; safe redirect/new-tab handling; dedicated profile. | Stop navigation and deny action; preserve current safe state. | Original/redirect classification, URL metadata as authorized, denial/evidence. |
| AB-07 | Stale approval is replayed after parameters or destination change. | Exact digest, destination, environment, precondition, expiry, anti-replay binding. | Invalidate and deny; require new policy/approval. | Approval ID, mismatch reason, attempted replay, no execution claim. |
| AB-08 | Agent delegates a higher-risk capability. | Delegated capability/data/environment subset and bounded budgets; no self-grant. | Reject delegation; parent task remains within envelope. | Parent/child/profile refs, denied capability, policy decision. |
| AB-09 | Sensitive evidence is placed in an Assistant event. | Classification, field redaction, authorized filtering, sanitized summaries. | Strip/redact and fail closed if visibility cannot be determined; do not deliver. | Redaction/denial metadata and evidence reference without raw content. |
| AB-10 | Redis is lost or restarted. | PostgreSQL authority; transient-only Redis; reconnect/resync cursor. | Rebuild delivery/leases; recover canonical state from PostgreSQL; never claim loss of material history. | Degraded health, resync/gap marker, reconciliation audit. |
| AB-11 | AnythingLLM becomes unavailable. | Replaceable adapter; Core authority; bounded timeout/degraded mode. | Mark knowledge unavailable; continue only with authorized alternatives and explicit limitation. | Provider health, failed retrieval, limitation/evidence state. |
| AB-12 | LM Studio is unavailable. | Provider abstraction; timeout/failure classification; privacy routing policy. | Degrade or use an approved policy-permitted provider; never expand cloud scope silently. | Provider/version, routing decision, failure and limitation. |
| AB-13 | Attacker tampers with evidence metadata. | Immutable IDs, hashes, provenance, PostgreSQL integrity, append-oriented history. | Detect mismatch; quarantine/invalidate evidence; do not use as verified fact. | Integrity failure, prior hash/version, tamper event, affected result. |
| AB-14 | Cancellation occurs during browser/tool work. | Checks before calls and between steps; bounded cancellation; reconciliation. | Stop future work; reconcile whether side effect occurred; report cancelled/indeterminate truthfully. | Cancellation request, tool state, reconciliation/verification, no false prevention claim. |

## General Abuse Response

No model-generated explanation, UI animation, or client event can override a denial. Untrusted content remains data. Any ambiguous identity, scope, visibility, destination, approval, or integrity condition fails closed. Retention and incident-response handling use policy references; no duration is invented here.

## Traceability

SEC-001..012; NFR-SEC-001..003, NFR-PRIV-001..003, NFR-AUDIT-001..003, NFR-CANCEL-001..002, NFR-RECOVER-001..002; ADR-002, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, ADR-011, ADR-013, ADR-014.
