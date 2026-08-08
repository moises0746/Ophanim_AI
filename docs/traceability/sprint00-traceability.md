# Sprint 00 Traceability Baseline

This view links product requirement families to accepted decisions, conceptual contracts, implementation ownership, and future test types. It is a planning baseline, not evidence that implementation exists.

| Product requirement family | ADRs | Contract artifacts | Planned implementation owner | Planned test type |
|---|---|---|---|---|
| FR-TASK-001..004 | ADR-001, 002, 009, 011, 014 | Core domain, lifecycle, policy/approval | Core domain + application task service | Domain, application, PostgreSQL, API |
| FR-PLAN-001..002 | ADR-001, 002 | Core domain, lifecycle, policy | Planning/application service | Domain/application/security |
| FR-AGENT-001..002 | ADR-001, 002, 008 | Core domain, lifecycle, security threat model | Agent profile/delegation application module | Domain/security/architecture |
| FR-TOOL-001..003 | ADR-002, 005, 006, 009, 014 | Core domain, policy/approval, browser/tool rules | Tool registry/execution application + adapters | Contract/integration/security |
| FR-READ-001..002 | ADR-002, 006, 014 | Policy/approval, browser/action, security | Read-only tool ports/adapters | Negative integration/security |
| FR-BROWSER-001..002 | ADR-006, 007, 014 | Browser execution, registry, actions, evidence, security | Browser port + later isolated runtime | Browser/security/e2e |
| FR-DATA-001, FR-LOG-001 | ADR-002, 003, 011, 012, 013 | Evidence, asset classification, trust boundaries | Data/log ports and adapters | Adapter/security/evidence |
| FR-KNOW-001..002 | ADR-003, 012, 013 | Evidence contracts, trust boundaries | Knowledge port + AnythingLLM adapter | Adapter/contract/security |
| FR-EVIDENCE-001..003 | ADR-002, 009, 011, 013 | Evidence/artifact contracts | Evidence application + PostgreSQL/artifact adapter | Domain/integration/integrity |
| FR-ANALYSIS-001..002 | ADR-002, 003, 013 | Evidence and result semantics | Analysis/application service | Domain/application/adversarial |
| FR-RESULT-001..002 | ADR-002, 013, 014 | Lifecycle/evidence contracts | Result/verification application service | Application/e2e |
| FR-ASSISTANT-001..003 | ADR-010, 013 | Assistant event/state/feed/delivery contracts | Core event projection + later desktop client | Event/accessibility/security |
| FR-CANCEL-001 | ADR-002, 007, 010, 014 | Lifecycle, event delivery, browser execution | Application cancellation coordinator | Unit/integration/browser |
| FR-FAIL-001..002 | ADR-001, 002, 011, 013 | Lifecycle, evidence, delivery | Application failure/recovery paths | Failure/recovery/e2e |
| FR-AUDIT-001 | ADR-009, 011, 013 | Event, evidence, policy, security contracts | Audit/event application + PostgreSQL | Integrity/recovery/security |
| FR-AUTH-001, FR-POLICY-001 | ADR-002, 005, 008, 009, 014 | Policy/approval, trust boundaries | Policy/authorization ports and service | Security/negative/API |

## Security and Non-Functional Traceability

| Requirement families | Authoritative artifacts | Planned verification |
|---|---|---|
| SEC-001..012 | ADR-002, 005..015; threat model; trust boundaries; browser security; engineering guardrails | Security negative, redaction, scope, architecture, browser/MCP tests |
| NFR-SEC-001..003 | Policy/approval, threat model, CI gates | Authorization denial, secret scan, mutation-denial tests |
| NFR-PRIV-001..003 | Asset classification, evidence, provider ADRs | Retention/classification/routing tests |
| NFR-OBS-001..002 | Event delivery, engineering/backend standards | Correlation and dependency-health tests |
| NFR-AUDIT-001..003 | Evidence, event, PostgreSQL ADR | Append/integrity/provenance/recovery tests |
| NFR-ACCESS-001..003 | Assistant state/frontend standards | Accessibility/reduced-motion/component tests |
| NFR-CANCEL-001..002 | Lifecycle, browser, engineering standards | Cancellation/interruptibility/reconciliation tests |
| NFR-RECOVER-001..002 | PostgreSQL ADR, lifecycle, CI gates | Restore/restart/idempotency tests |

## Sprint 01 Traceability Gap Review

No missing link blocks the proposed Core foundation slice. The first implementation tasks should close the Python domain-type, application-service, default-deny policy, event-model, API, and architecture-test links. Browser, MCP, provider replacement, desktop, voice, and writes remain later owners.
