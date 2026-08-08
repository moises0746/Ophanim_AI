# Conceptual Security Test Matrix

This matrix defines future tests only. S00-T07 adds no test code, auth, secret store, migration, or runtime control.

| Matrix ID | Test category/scenario | Requirement IDs | ADRs | Threat IDs | Future test type |
|---|---|---|---|---|---|
| ST-01 | Default-deny identity/capability/tool authorization | SEC-001, SEC-002; NFR-SEC-001 | ADR-002, ADR-005, ADR-008 | T-STRIDE-06, T-AI-08 | Unit/policy/integration negative |
| ST-02 | Workspace, tenant, environment, application/domain scope escape | SEC-001, SEC-002, SEC-006, SEC-010; NFR-PRIV-001 | ADR-006, ADR-007, ADR-011 | T-AI-06, T-AI-12 | Integration/security |
| ST-03 | Secret redaction in prompts, events, evidence, logs, screenshots | SEC-003, SEC-004, SEC-011; NFR-SEC-002 | ADR-008, ADR-010, ADR-013 | T-STRIDE-04, T-AI-07 | Redaction scan/fixture |
| ST-04 | Direct/indirect prompt injection from docs, pages, logs, tool output | SEC-007; NFR-SEC-001 | ADR-002, ADR-003, ADR-005, ADR-007 | T-AI-01, T-AI-04, T-AI-05 | Adversarial integration |
| ST-05 | MCP unregistered server, poisoned metadata/resource, schema mismatch | SEC-001, SEC-005, SEC-007, SEC-011 | ADR-005, ADR-008 | T-AI-02, T-STRIDE-06 | MCP contract/security |
| ST-06 | Browser redirect, popup, upload/download, JS, personal-profile, cross-domain escape | SEC-005, SEC-006, SEC-007; NFR-SEC-003 | ADR-006, ADR-007, ADR-014 | T-AI-05, T-AI-06 | Browser security/e2e |
| ST-07 | Arbitrary SQL, shell, filesystem, network, or raw-coordinate denial | SEC-005, SEC-009 | ADR-002, ADR-006, ADR-014 | T-STRIDE-06, T-AI-08 | Negative API/tool/integration |
| ST-08 | Model malformed output, hallucinated success, unauthorized parameters | SEC-001, SEC-007, SEC-008; NFR-AUDIT-002 | ADR-002, ADR-004, ADR-013 | T-AI-03, T-AI-04 | Contract/property/integration |
| ST-09 | Agent delegation subset, budget, timeout, no credential sharing | SEC-001..003; NFR-SEC-001 | ADR-001, ADR-002, ADR-008 | T-STRIDE-06, T-AI-08 | Domain/security |
| ST-10 | Approval spoof, replay, stale digest/precondition, expiry, transport failure | SEC-001, SEC-009; NFR-SEC-001, NFR-AUDIT-003 | ADR-009, ADR-014 | T-AI-09, T-STRIDE-01/02 | Approval/security integration |
| ST-11 | Event authorization, field redaction, visibility failure, no fabricated feed | SEC-004, SEC-011; NFR-OBS-001, NFR-ACCESS-001 | ADR-010, ADR-013 | T-STRIDE-01/04, T-AI-10/11/12 | Event/reducer/accessibility |
| ST-12 | Evidence provenance, hash mismatch, append history, tamper detection | SEC-008, SEC-011; NFR-AUDIT-001..003 | ADR-011, ADR-013 | T-STRIDE-02/03, T-AI-10 | Persistence/integrity |
| ST-13 | Cancellation before/between/during tool/browser work | SEC-012; NFR-CANCEL-001..002 | ADR-002, ADR-007, ADR-014 | T-STRIDE-05, T-AI-05 | Lifecycle/integration |
| ST-14 | PG recovery, Redis loss, duplicate/replay/gap/resync | NFR-OBS-001, NFR-RECOVER-001..002 | ADR-010, ADR-011 | T-STRIDE-02/05, T-AI-11 | Recovery/chaos/integration |
| ST-15 | AnythingLLM/LM Studio/provider unavailable or cloud-routing mismatch | NFR-PRIV-003, NFR-OBS-002 | ADR-003, ADR-004 | T-STRIDE-05, T-AI-12 | Adapter/degraded-mode |
| ST-16 | Development/test to production credential/data/environment separation | SEC-010; NFR-SEC-001, NFR-PRIV-001 | ADR-001, ADR-008, ADR-011 | T-STRIDE-01/04/06, T-AI-12 | Environment/security |

## Test Principles

Tests use synthetic canary secrets and private fixtures. They assert denial, redaction, provenance, truthful degraded state, and absence of side effects—not merely successful HTTP responses. Future tests must cover positive authorized reads and negative indirect/state-changing attempts.

## Traceability

The matrix covers SEC-001..012, FR-TASK, FR-AGENT, FR-TOOL, FR-EVIDENCE, FR-ASSISTANT, FR-CANCEL, FR-FAIL, FR-AUDIT, and NFR-SEC, PRIV, OBS, AUDIT, ACCESS, CANCEL, and RECOVER families.
