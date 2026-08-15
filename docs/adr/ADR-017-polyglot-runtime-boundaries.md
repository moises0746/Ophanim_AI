# ADR-017: Polyglot Runtime Boundaries: Python Control Plane and Evidence-Gated Rust

Status: Accepted

## Context

Ophanim Core is the authoritative control plane and currently uses Python 3.12+, FastAPI, and Pydantic. Python provides the primary AI, orchestration, provider, retrieval, policy-coordination, and application ecosystem for the product. ADR-001 establishes Core as a modular monolith and permits service extraction only when an accepted ADR demonstrates a material scaling, isolation, security, ownership, or deployment-cadence need.

Ophanim may later require a separately deployed Endpoint Runtime on Windows. That runtime would have different constraints from Core: continuous service operation, native operating-system integration, local observation and enforcement, small resource usage, predictable event processing, secure transport, and independent installation and updates. Selecting an implementation language for that boundary must not become a pretext for rewriting Core or prematurely decomposing the modular monolith.

Synthetic language benchmarks do not establish that a production Ophanim component is limited by its implementation language. Model inference, external providers, databases, queues, networks, architecture, and workload design may dominate observed performance. Technology changes therefore require representative evidence tied to defined requirements.

## Decision

Python 3.12+ remains the primary implementation language for Ophanim Core and the AI/control plane. This includes API delivery, agent orchestration, AI provider integration, retrieval-augmented generation, workflow coordination, policy and approval coordination, tool orchestration, investigation logic, evidence, audit, and durable workflow-state authority.

The existing Ophanim Core must not be rewritten in Rust merely because Rust has superior synthetic performance characteristics.

Rust is the preferred candidate for the future Ophanim Endpoint Runtime because it offers:

- low runtime footprint;
- memory safety;
- predictable latency;
- native executable deployment;
- suitability for long-running services; and
- strong event-processing performance.

Final Rust selection for the Endpoint Runtime is subject to a bounded Rust-versus-C#/.NET compatibility prototype against actual Windows endpoint requirements. C#/.NET remains the primary alternative when Windows-native APIs, UI Automation, enterprise management integration, team capability, or development complexity materially outweigh Rust's footprint advantages. Go may remain an evaluated alternative for network-oriented endpoint or gateway workloads, but it is not currently preferred for deep Windows integration.

Ophanim adopts this principle:

> Rust by evidence, not Rust everywhere.

Introducing Rust into a server-side component requires all of the following:

- a measurable service-level objective or economic requirement;
- representative workload profiling;
- evidence identifying the Python application runtime as the material bottleneck;
- evaluation of reasonable Python optimization, batching, caching, concurrency, scaling, and dependency changes first;
- a stable typed contract boundary;
- security and operational analysis;
- a rollback strategy; and
- a separate accepted ADR for the specific extraction.

Generic Rust-versus-Python benchmarks, developer preference, speculative future scale, or codebase growth are not sufficient justification for service extraction or rewriting.

## Endpoint Runtime Boundary

The future Ophanim Endpoint Runtime is a separately deployed trust and operational boundary. Its expected responsibilities may include:

- Windows service lifecycle;
- device identity;
- endpoint health;
- approved operating-system and application observation;
- local allowlist enforcement;
- sensitive-context filtering;
- data minimization;
- event normalization;
- secure outbound transport; and
- bounded deterministic endpoint capabilities approved by Core policy.

The Endpoint Runtime is not an unrestricted autonomous agent. It must explicitly prohibit:

- arbitrary shell execution;
- arbitrary PowerShell execution;
- unrestricted filesystem access;
- credential harvesting;
- keylogging;
- unrestricted screen surveillance;
- hidden or security-evasive operation;
- unrestricted browser control; and
- autonomous production changes.

Endpoint capabilities must use least privilege, closed typed inputs, explicit application, environment, path, command, and action allowlists as applicable, bounded timeouts, cancellation, deterministic verification, and auditable execution receipts. Local observation and telemetry must be minimized before transmission and limited to the authorized purpose and data scope.

## Control-Plane Authority

Ophanim Core remains authoritative for:

- authentication;
- authorization and RBAC;
- policy decisions;
- human approvals;
- orchestration;
- tool and capability authorization;
- evidence and audit; and
- durable workflow state.

The LLM must not directly control the Endpoint Runtime. The conceptual execution path is:

```text
LLM
  -> proposal
Ophanim Core
  -> authentication
  -> authorization
  -> policy
  -> approval where required
  -> normalized deterministic capability
Endpoint Runtime
  -> local validation
  -> bounded execution
  -> verification
  -> execution receipt
Ophanim Core
  -> authoritative audit/evidence
```

The endpoint independently fails closed when identity, contract version, authorization binding, policy version, environment, destination, scope, expiry, or integrity is unknown or invalid. Local validation narrows authority and cannot widen or replace Core authorization. An endpoint execution receipt is evidence input, not by itself authoritative proof of overall workflow success.

## Contract and Transport Boundary

Communication between Core and the Endpoint Runtime must use Ophanim-owned, technology-neutral, explicitly versioned contracts. Provider, framework, Windows API, Rust, and Python implementation types must not leak into the shared domain meaning.

Contracts must define stable identifiers, device and environment scope, correlation and causation, timestamps, schema versions, normalized capability inputs, policy and approval references where applicable, sequence or idempotency semantics, sanitized results, verification status, error classification, and integrity metadata. Compatibility rules must cover version negotiation, additive evolution, duplicate delivery, replay, bounded buffering, backpressure, reconnection, revocation, unsupported versions, and safe handling of unknown authority-bearing fields.

The initial transport direction is:

- HTTP for enrollment, configuration, and administrative request/response operations;
- WebSocket for persistent real-time endpoint communication; and
- gRPC deferred until measured connection density, throughput, latency, bandwidth, interoperability, or operational evidence justifies it.

This transport direction does not authorize creation of endpoints, schemas, services, or runtime code. The exact transport, authentication, delivery, replay, and compatibility contracts require separately authorized work.

## Relationship to Existing Decisions

This decision complements and does not supersede ADR-001. The Endpoint Runtime is justified by a distinct endpoint deployment, operating-system, lifecycle, resource, and trust boundary, not by decomposition of Ophanim Core. Any later server-side extraction remains subject to ADR-001 and requires a separate accepted ADR.

ADR-016 also preserves:

- ADR-002: models propose while governed deterministic tools execute;
- ADR-005: a protocol or discovered capability never bypasses Core governance;
- ADR-006: integrations use the safest reliable mechanism and fallbacks never expand authority;
- ADR-008: agents and endpoint contracts do not own or expose credentials;
- ADR-009: consequential actions require exact human approval before execution;
- ADR-011: PostgreSQL remains authoritative for durable application and workflow state;
- ADR-013: Core-owned evidence and audit remain first-class records;
- ADR-014: the MVP remains read-only and this ADR enables no endpoint mutation path; and
- ADR-015: first-party Core and endpoint logic remain isolated from vendor source.

## Rationale

The language boundary follows product responsibilities rather than benchmark rankings. Python retains the mature AI and orchestration ecosystem where external I/O and model latency commonly dominate. Rust is a strong candidate where endpoint footprint, native deployment, predictable resource use, secure systems programming, and continuous event processing are direct requirements.

The prototype gate preserves C#/.NET as a credible Windows-native alternative and prevents the preferred candidate from becoming an untested mandate. Evidence gates for server extraction preserve Core's modular-monolith benefits while keeping technology replacement possible behind stable contracts.

## Positive Consequences

- The endpoint may use a language suited to footprint, safety, latency, deployment, and long-running service constraints.
- Ophanim preserves Python's AI, orchestration, and provider ecosystem in Core.
- Ophanim-owned contracts keep endpoint and future extracted implementations replaceable.
- Evidence-gated server extraction remains available when a real requirement emerges.
- Rust offers the potential for a smaller endpoint footprint and predictable event processing.
- The separate endpoint boundary can have independent lifecycle, health, isolation, and release controls.

## Negative Consequences

- The project gains a second language and toolchain.
- CI/CD, dependency governance, testing, observability, and release management become more complex.
- Cross-language contract generation, versioning, and compatibility require ongoing discipline.
- Development and review require additional skills.
- Windows FFI can add implementation and safety complexity.
- Endpoint packaging, signing, enrollment, updates, revocation, and rollback create an additional release lifecycle.
- Distributed-boundary failure modes such as disconnection, replay, backpressure, and version skew must be handled.

## Risks and Mitigations

### Duplicated policy semantics

Risk: endpoint-local enforcement may diverge from Core policy or be mistaken for an independent source of authority.

Mitigation: Core remains authoritative. The endpoint receives a bounded, versioned enforcement projection and may only narrow or deny it. Compatibility and denial tests must cover semantic drift.

### Protocol drift

Risk: Python and Rust implementations may interpret messages or compatibility rules differently.

Mitigation: use Ophanim-owned generated or versioned contracts, golden fixtures, cross-language compatibility tests, explicit negotiation, and fail-closed unknown-field rules for authority-bearing data.

### Endpoint compromise

Risk: a compromised endpoint could forge observations, replay commands, expose data, or abuse local capabilities.

Mitigation: least-privilege service identity, device authentication, command expiry and anti-replay controls, local allowlists, signed artifacts, endpoint revocation, bounded offline behavior, verification, and authoritative Core audit/evidence correlation.

### Unsafe Windows FFI

Risk: native API integration may introduce memory, handle-lifecycle, or privilege errors despite Rust's general safety properties.

Mitigation: minimize and isolate unsafe code, prefer maintained safe wrappers, document invariants, add focused tests and static review, and compare complexity with the C#/.NET prototype.

### Excessive telemetry collection

Risk: endpoint observation could collect private or sensitive content beyond the authorized purpose.

Mitigation: explicit observation allowlists, local sensitive-context filtering, data minimization before transport, bounded retention, classification, user-visible controls, redaction, and security/privacy tests.

### Premature Rust service extraction

Risk: language enthusiasm could fragment Core without an operational need.

Mitigation: enforce the evidence-based extraction gates in this ADR and ADR-001, including representative profiling, Python optimization evaluation, rollback planning, and a separate accepted ADR.

### Insufficient Rust expertise

Risk: limited team experience could reduce delivery speed, code quality, or operational reliability.

Mitigation: use a bounded prototype, define ownership and review expectations, train reviewers, keep the Rust boundary small, and select C#/.NET if measured delivery or Windows-integration complexity outweighs Rust's benefits.

## Security Impact

This decision introduces no executable capability, but it defines a future high-value trust boundary. Authentication, authorization, least privilege, environment and data scope, capability allowlists, exact approvals, secret isolation, local minimization, secure transport, revocation, verification, evidence, audit, cancellation, emergency stop, and signed releases are mandatory before deployment.

The endpoint must treat commands, external application content, operating-system observations, and remote configuration as untrusted until authenticated, schema validated, authorized, and locally constrained. The existence of a Rust endpoint never grants an LLM unrestricted operating-system access.

## Operational Impact

A future Endpoint Runtime requires independent enrollment, identity and key rotation, inventory, health, compatibility, configuration rollout, staged update, signing, rollback, revocation, crash recovery, bounded offline buffering, diagnostics, and incident-response procedures. Core must degrade safely when an endpoint is unavailable, stale, compromised, duplicated, slow, or incompatible.

Server-side Rust extraction would add network, deployment, failure, observability, data-consistency, and ownership costs. Those costs must be included in the evidence and economic analysis rather than treating runtime speed as the sole criterion.

## Testing Impact

Future Endpoint Runtime work requires contract and compatibility tests across Python and Rust, Windows service lifecycle tests, least-privilege and denial tests, replay and expiry tests, malformed-message tests, data-minimization and redaction tests, cancellation and emergency-stop tests, disconnect/reconnect and backpressure tests, update and rollback tests, artifact-signature verification, and representative performance measurements.

Any future server-side extraction requires equivalence, failure-mode, security, observability, compatibility, load, rollback, and recovery tests before traffic migration. This proposed ADR adds no tests or runtime behavior itself.

## Rejected Alternatives

- Rewrite Ophanim Core in Rust: rejected because no representative evidence identifies Python as a material bottleneck, and a rewrite would discard the existing AI ecosystem while increasing delivery and migration risk.
- Use Rust for all new server components by default: rejected because language selection follows measured component requirements and ADR-001 extraction criteria.
- Keep all endpoint behavior in Python: rejected as the preferred direction because a continuously deployed Windows endpoint has footprint, native distribution, predictability, and systems-integration constraints that warrant a Rust candidate, subject to prototype evidence.
- Select C#/.NET without comparison: rejected as a default decision, but retained as the primary alternative for deep Windows integration and lower implementation complexity.
- Select Go as the endpoint default: rejected for now because its strengths are more compelling for network-oriented services than deep Windows integration; it remains available for evidence-based evaluation.
- Introduce gRPC immediately: rejected as unnecessary distributed-system and tooling complexity before transport requirements are measured.
- Treat endpoint-local policy as authoritative: rejected because it would fragment authorization and create bypass and consistency risks.

## Follow-up and Deferred Work

This ADR authorizes no implementation. It does not create the Endpoint Runtime, Rust source, API endpoints, contracts, transport, migrations, deployment assets, or server extraction.

Before selecting and implementing the Endpoint Runtime, separately authorized work must define actual Windows requirements, update the threat model and trust boundaries, establish performance and footprint targets, run the bounded Rust-versus-C#/.NET prototype, select packaging and signing mechanisms, and obtain human review.

Any server-side Rust extraction requires representative measurements and its own accepted ADR. Current Sprint completion status and roadmap authorization remain unchanged.
