# Ophanim Core Domain Contracts

## Status and Authority

This is the authoritative S00-T05 conceptual contract baseline. It defines meaning and ownership, not Python types, schemas, endpoints, registries, or runtime. Ophanim Core owns these contracts. Models plan/recommend; governed deterministic tools execute.

IDs are opaque, stable, globally unique within Ophanim, and contain no secret or sensitive business data. Times are UTC instants. Stored records carry a schema version; incompatible changes require explicit versioning.

## Task

| Concern | Contract |
|---|---|
| Responsibility | Durable owner intent, bounded policy envelope, orchestration state, and outcome. |
| Ownership | Core task/application module; only its task service changes canonical state. |
| Stable ID | Immutable `task_id`, independent of title/correlation IDs. |
| Lifecycle/status | `created`, `planning`, `working`, `blocked`, `cancelling`, `cancelled`, `failed`, `completed`; see [Lifecycle Contracts](lifecycle-contracts.md). |
| Required fields | ID, owner/workspace, title, objective, status, priority, privacy/autonomy/risk, environment, policy-envelope version, created/updated times, correlation ID. |
| Optional fields | Parent, assignee, deadline, budgets, retry policy, result summary, sanitized error, cancellation reason, completed time. |
| Invariants | Objective is not authority; children cannot widen authority; terminal states cannot silently resume; completion records verification. |
| Validation | Bounded text, recognized scopes/environment, valid transition, coherent deadlines/budgets, authorized owner. |
| Security/privacy | Least privilege/default deny; no credentials, hidden reasoning, or unrestricted private content. |
| Persistence | Future canonical state is PostgreSQL; state plus material event is transactional where practical. Redis is transient. |
| Audit | Creation, material transitions, policy changes, cancellation, outcome, and verification. |
| Versioning | Pins schema/policy envelope; authority changes are auditable revisions. |

## TaskStep

| Concern | Contract |
|---|---|
| Responsibility | Bounded schedulable work with dependencies, limits, and verification. |
| Ownership | Core orchestration under one Task. |
| Stable ID | Immutable `task_step_id` referencing one `task_id`. |
| Lifecycle/status | Conceptually pending, ready, leased/working, blocked, cancelling, cancelled, failed, completed; exact vocabulary deferred. |
| Required fields | IDs, dependency position, bounded objective, status, capability requirements, attempt count, verification requirement, timestamps. |
| Optional fields | Dependency IDs, agent profile/version, worker lease, deadline/budget, sanitized input/output, retry/failure class, Evidence IDs. |
| Invariants | Same authorized task graph; cannot widen task authority; completion satisfies or explicitly lacks verification; leases bounded. |
| Validation | Acyclic dependencies, bounded attempts/lease, capability subset, valid transition, cancellation check. |
| Security/privacy | Minimized/sanitized content; inherited scope only narrows. |
| Persistence | Durable state in PostgreSQL; transient coordination is non-authoritative. |
| Audit | Assignment, attempt, lease recovery, status, verification, cancellation. |
| Versioning | Pins agent, capability, tool, and policy versions per attempt. |

## AgentProfile

| Concern | Contract |
|---|---|
| Responsibility | Versioned bounded role/capability/limit/output profile, not an autonomous principal. |
| Ownership | Core agent/profile module; Core policy/tools retain authority. |
| Stable ID | `agent_profile_id` plus immutable `profile_version`. |
| Lifecycle/status | Conceptually draft, active, deprecated, disabled. |
| Required fields | ID/version, name, role, status, required model capabilities, allowed capabilities/data/environments, risk tier, budgets/timeouts, delegation bounds, output/verification requirements. |
| Optional fields | Description, instruction reference/version, model characteristics, labels. |
| Invariants | No credentials; permissions only narrow task authority; delegation cannot expand scope/budget/autonomy. |
| Validation | Known capabilities/scopes, bounded limits, valid output contract, unique version. |
| Security/privacy | Portable and secret-free; classified instructions get controlled access. |
| Persistence | Versioned metadata in PostgreSQL when implemented; secrets outside the aggregate. |
| Audit | Creation, activation/deprecation, assignment, effective version. |
| Versioning | Material changes create immutable new versions; history pins the used version. |

## Capability

| Concern | Contract |
|---|---|
| Responsibility | Provider-independent permission-level operation. |
| Ownership | Core capability/policy boundary. |
| Stable ID | Namespaced `capability_id`, e.g. `browser.read`, `knowledge.search`, `logs.search`, `transaction.read`, `database.lookup`, `evidence.capture`. |
| Lifecycle/status | Conceptually proposed, active, deprecated, disabled. |
| Required fields | ID/version, description, read/write class, risk, scope dimensions, status. |
| Optional fields | Preconditions, approval class, evidence/verification expectations, replacement. |
| Invariants | Grants no execution alone; unknown/disabled/out-of-scope denies; ID contains no destination/secret. |
| Validation | Registered namespace, explicit classification, compatible scopes, unambiguous meaning. |
| Security/privacy | Default deny across identity/task/environment/data/application/domain/tool. |
| Persistence | Versioned authorization metadata in PostgreSQL when implemented. |
| Audit | PolicyDecision references evaluated capability/version. |
| Versioning | Semantic widening requires reviewed new version or ID. |

## ToolDefinition

| Concern | Contract |
|---|---|
| Responsibility | Versioned deterministic implementation contract; never arbitrary execution. |
| Ownership | Core registry contract; implementation at approved adapter/infrastructure boundary. |
| Stable ID | `tool_definition_id` plus immutable `tool_version`. |
| Lifecycle/status | Conceptually proposed, enabled, disabled, deprecated. |
| Required fields | ID/version, capability mapping, typed input/output schema refs, read/write/risk, timeout, bounded retry, cancel behavior, restrictions, credential-reference/evidence/verification requirements, status. |
| Optional fields | Adapter, environments, idempotency, health dependency, replacement. |
| Invariants | No arbitrary shell/SQL/JavaScript/unbounded destination; validate before credential resolution; retry cannot widen authority. |
| Validation | Known mapping, closed/bounded schemas, timeout/retry/cancel, allowlisted environment/application/domain/path/command as applicable. |
| Security/privacy | Resolve credential values only at execution; never store them in contracts/prompts/evidence; external output is untrusted. |
| Persistence | Versioned metadata in PostgreSQL; runtime health/cache is non-authoritative. |
| Audit | Registration/status/version and selected version. |
| Versioning | Schema/authority changes create a new version with compatibility declared. |

## ToolCall

| Concern | Contract |
|---|---|
| Responsibility | Auditable request/outcome for one governed deterministic invocation. |
| Ownership | Core execution application module; adapter receives only its authorized request. |
| Stable ID | Immutable `tool_call_id`, idempotency-aware where applicable. |
| Lifecycle/status | Conceptually requested, denied, awaiting approval, executing, cancelling, cancelled, failed, verification-failed, completed. |
| Required fields | ID, task/step, agent version if applicable, capability/version, tool/version, normalized sanitized input or digest, environment/scope, PolicyDecision ID, status, request time, correlation ID. |
| Optional fields | Approval ID, opaque credential-reference ID, attempts, times, sanitized result/error, verification, Evidence/Artifact IDs. |
| Invariants | No execution without allow; changed parameters require reevaluation/invalidate approval; no success before required verification. |
| Validation | Schema/scope/destination/restrictions, transition, timeout/retry budget, exact approval binding. |
| Security/privacy | No raw credentials/cookies/auth state/hidden reasoning/unrestricted payload; output sanitized/classified. |
| Persistence | Material lifecycle and integrity metadata in PostgreSQL; transient worker state only may be cached. |
| Audit | Request, denial/approval, execution, cancel/retry, verification, outcome. |
| Versioning | Pins all effective contract and policy versions. |

## Minimal Event Contracts

The authoritative detailed vocabulary, transport, ordering, replay, and UI mappings are now defined by [Assistant Event Contracts](../assistant/assistant-event-contracts.md), [Agent Activity Events](../assistant/agent-activity-events.md), [Assistant State Projection](../assistant/assistant-state-projection.md), [Activity Feed Projection](../assistant/activity-feed-projection.md), and [Event Delivery Contracts](event-delivery-contracts.md). S00-T06 adds no runtime.

### AssistantStateEvent

| Concern | Contract |
|---|---|
| Responsibility | Sanitized Core-authored fact from which the Assistant may represent authoritative orchestration state. |
| Ownership | Core event boundary; UI/models cannot author authority. |
| Stable ID | Immutable `event_id` with correlation and relevant entity references. |
| Lifecycle/status | Immutable occurrence; correction/supersession is another event. |
| Required fields | ID, type, schema version, occurred-at, correlation ID, sanitized semantic state, producer, visibility/data-scope metadata. |
| Optional fields | Task/step/tool/approval/evidence/causation refs, safe display summary. |
| Invariants | Real Core activity only; no timer-fabricated transition, secret, or chain-of-thought. |
| Validation | Known type/version, valid refs, authorized sanitized payload. |
| Security/privacy | Minimized/redacted/scoped; display confers no authority. |
| Persistence | Material events future-durable in PostgreSQL; delivery buffer is not authority. |
| Audit | Links the causing material state/audit record. |
| Versioning | Explicit schema; additive unknown fields safely ignored. |

### AgentActivityEvent

| Concern | Contract |
|---|---|
| Responsibility | Sanitized Core-authored fact about bounded agent/delegation/tool/progress/wait activity. |
| Ownership | Core event boundary. |
| Stable ID | Immutable `event_id` with correlation/causation. |
| Lifecycle/status | Immutable occurrence; activity vocabulary deferred to S00-T06. |
| Required fields | ID, type, schema version, occurred-at, correlation, producer, sanitized activity class, visibility/data scope. |
| Optional fields | Task/step/agent/tool/evidence/policy/approval/parent-event refs, safe summary. |
| Invariants | Auditable Core fact; no private reasoning or model claim presented as activity. |
| Validation | Known type/version, referential consistency, sanitization, visibility authorization. |
| Security/privacy | Minimized/redacted/scoped; external content remains untrusted. |
| Persistence | Material events future-durable in PostgreSQL; transport deferred. |
| Audit | Links authoritative activity/decision record. |
| Versioning | Explicit schema and backward-compatible evolution. |

## Traceability

| Area | Functional requirements | Security |
|---|---|---|
| Task/TaskStep | FR-TASK-001..004, FR-PLAN-001..002, FR-CANCEL-001, FR-FAIL-001..002, FR-RESULT-001..002 | SEC-001, SEC-006, SEC-010, SEC-011 |
| AgentProfile/Capability | FR-AGENT-001..002, FR-PLAN-002 | SEC-001..003, SEC-006 |
| ToolDefinition/ToolCall | FR-TOOL-001..003, FR-READ-001..002, FR-BROWSER-001..002, FR-DATA-001, FR-LOG-001, FR-KNOW-001..002 | SEC-001..008, SEC-010..012 |
| Events | FR-ASSISTANT-001..003, FR-AUDIT-001 | SEC-004, SEC-006, SEC-009, SEC-010 |

## Deferred

Pydantic, enums, cardinalities, transaction boundaries, schemas/migrations, registries, runtimes, exact event contracts/transport/replay/UI mapping, and endpoints require later authorization. MVP remains read-only.
