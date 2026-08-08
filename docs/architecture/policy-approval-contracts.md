# Policy Decision and Approval Contracts

## Scope and Decision Order

```text
identity -> task/environment/data scope -> capability/tool allowlist
         -> policy -> approval when required -> credential resolution
         -> deterministic execution -> verification -> evidence/audit
```

Missing, unknown, ambiguous, stale, malformed, unavailable, or mismatched authorization data denies by default. These are record contracts only: no engine, workflow, credentials, or writes are implemented.

## PolicyDecision

| Concern | Contract |
|---|---|
| Responsibility | Immutable evaluation result for one proposed capability/tool action. |
| Ownership | Ophanim Core policy boundary. |
| Stable ID | Immutable `policy_decision_id`; reevaluation creates a new record. |
| Lifecycle/status | Conceptually allow, deny, approval-required; error/indeterminate fails closed as deny. |
| Required fields | ID, subject identity, task/optional step, environment, data/workspace scope, capability/version, optional tool/version, normalized parameter digest, destination/resource, decision/reason code, policy/version, time, correlation ID. |
| Optional fields | Agent version, application/domain/path/command constraints, risk, approval class, validity, parent decision, safe explanation. |
| Invariants | Default deny; allow is exact/non-transferable; no widening by fallback/delegation/retry/adapter/MCP/browser/model; no credentials. |
| Validation | Authorized subject, known versions, scope subset, exact normalized request, known environment/destination, current policy, bounded validity. |
| Security/privacy | Sanitized explanation cannot leak secrets, other scopes, or sensitive policy internals. External resources are untrusted. |
| Persistence | Durable decisions in PostgreSQL when implemented; cache is not authority. |
| Audit | Referenced/digested inputs, result/reason, versions, actor, time, correlation. |
| Versioning | Pins policy/contracts; changed request/policy requires new evaluation. |

Evaluation dimensions include identity/workspace, parent/task envelope, environment, data scope/classification, capability/tool allowlists, application/domain/destination/resource, relevant paths/commands/arguments, read/write/risk, time/budget/retry/cancel limits, agent/delegation, evidence/verification, and approval. A required missing dimension denies.

## Approval

| Concern | Contract |
|---|---|
| Responsibility | Exact future human authorization for one consequential proposal; never execution itself. |
| Ownership | Core approval boundary; only an authenticated authorized human decides. Models/agents cannot approve. |
| Stable ID | Immutable `approval_id`; changed proposal creates a new request. |
| Lifecycle/status | Conceptually requested, granted, denied, expired, cancelled, consumed, invalidated. |
| Required fields | ID, task/step/ToolCall proposal, PolicyDecision ID, normalized action/parameter digest, destination/resource, environment, risk/impact summary, requester, eligible approver scope, status, issue/expiry, schema version. |
| Optional fields | Approver, decision time/rationale, precondition digest, consumption time/ToolCall, verification/rollback refs. |
| Invariants | Explicit human action, fail closed, exact context; any parameter/destination/environment/risk/precondition/tool-version change invalidates; no replay; never bypasses policy, verification, evidence, audit, or cancel. |
| Validation | Approver authentication/authority, integrity binding, current task/policy/preconditions, exact digest, expiry, anti-replay, exact environment/destination. |
| Security/privacy | Sanitized informed-consent context; no credentials/hidden reasoning; UI/transport failure never approves. |
| Persistence | Future authoritative append-only history in PostgreSQL; Redis cannot be sole record. |
| Audit | Request/presentation/decision/expiry/invalidation/cancel/consumption/execution/verification. |
| Versioning | Pins schema/policy/tool versions and preserves historical interpretation. |

## Read-Only MVP and Credential Boundaries

Future compatibility does not expose a production mutation path. Write tools are absent/disabled; Approval cannot override that. Draft/recommend is distinct from send, publish, upload, delete, overwrite, remediate, deploy, restart, purchase, or credential/permission change. Reads remain scoped and audited.

No AgentProfile, Capability, ToolDefinition, ToolCall, PolicyDecision, Approval, event, Evidence, or Artifact contains raw credentials. Only after authorization and any future valid approval may a deterministic tool resolve an opaque secret reference for a bounded operation. Missing/expired/revoked/wrong-scope credentials safely deny or fail; values never return to prompts, ordinary logs, evidence, or events.

## Traceability

- FR-POLICY-001, FR-TOOL-001..003, FR-AUTH-001, FR-READ-001..002.
- FR-ASSISTANT-003 (future presentation only), FR-AUDIT-001, FR-CANCEL-001, FR-FAIL-001..002.
- SEC-001..012.

## Deferred

Policy engine/language, reason codes, schemas/enums, identity/roles, secret provider, approval authentication/UX/transport/persistence, signatures, anti-replay runtime, separation of duties, idempotency, rollback, and all writes remain deferred.
