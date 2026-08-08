# Ophanim AI Non-Functional Requirements

## Status and Measurement Policy

These requirements define measurable quality categories for the transaction-investigation MVP. Where representative workload, deployment topology, data classification, or business risk is not yet known, the target is **TBD** and the required validation method is stated. S00-T04 does not invent SLA/SLO numbers or implement measurement tooling.

## Security

- **NFR-SEC-001:** Authorization and tool boundaries fail closed when identity, RBAC, environment/data scope, policy, application/domain, or credentials are missing or ambiguous. **Measure:** zero unauthorized successes in the defined security test matrix. **Validation:** denial and scope-escape tests in S00-T09/S00-T10 and implementation tasks.
- **NFR-SEC-002:** Secrets and hidden chain-of-thought are absent from Assistant events, normal logs, evidence summaries, API responses, and test fixtures. **Measure:** zero known exposures in automated redaction/secret scans and targeted tests. **Validation:** synthetic canary secrets plus review.
- **NFR-SEC-003:** MVP mutation paths are unavailable. **Measure:** all enumerated direct and indirect write attempts are deterministically denied. **Validation:** negative API/tool/MCP/browser/database/log tests.

## Privacy

- **NFR-PRIV-001:** Collection and retention are limited to authorized task purpose and configured policy. **Measure:** each retained artifact/evidence type has classification, purpose, scope, and retention metadata or an explicit documented exception. **Validation:** data inventory and retention review.
- **NFR-PRIV-002:** Private knowledge and screenshots are not retained or exported by default outside explicit scope. **Measure:** zero unauthorized artifacts in storage/export tests. **Validation:** synthetic private fixtures and access-control tests.
- **NFR-PRIV-003:** Cloud model routing for sensitive data is policy-controlled. **Target:** exact permitted classifications are **TBD**. **Validation:** business/privacy classification decision followed by routing-denial tests.

## Reliability

- **NFR-RELIABILITY-001:** A source failure does not become fabricated evidence or false completion. **Measure:** every injected dependency failure produces an accurate completed/partial/blocked/failed source status. **Validation:** fault-injection and contract tests.
- **NFR-RELIABILITY-002:** Material task state and correlated events are durable and internally consistent once persistence exists. **Measure:** no accepted test scenario leaves canonical state without its required material event. **Validation:** PostgreSQL transactional/recovery tests.
- **NFR-RELIABILITY-003:** Retried internal operations do not duplicate durable tasks, tool effects, or evidence where idempotency is required. **Target:** exact retry/idempotency matrix is **TBD**. **Validation:** contract definition plus duplicate-delivery tests.

## Availability

- **NFR-AVAIL-001:** Core distinguishes liveness from readiness and reports optional dependency degradation without exposing secrets. **Measure:** deterministic health state for each dependency scenario. **Validation:** health/API tests.
- **NFR-AVAIL-002:** Production availability target is **TBD** pending deployment topology, business hours, source-system dependencies, and support model. **Validation:** business SLO decision informed by pilot telemetry and dependency availability.

## Observability

- **NFR-OBS-001:** Logs, metrics, traces, task events, tool calls, and evidence share correlation identifiers appropriate to their scope. **Measure:** every sampled end-to-end test can be reconstructed without raw secrets. **Validation:** trace-correlation review.
- **NFR-OBS-002:** Operators can identify dependency health, task state, failure class, cancellation status, and selected integration mechanism. **Measure:** coverage of the agreed operational diagnostic matrix. **Validation:** controlled incident exercises; matrix **TBD** in S00-T10.

## Auditability

- **NFR-AUDIT-001:** Material task, policy, delegation, tool, evidence, cancellation, failure, and completion activity is attributable and time-correlated. **Measure:** 100% coverage of the material-event matrix once defined. **Validation:** event/audit contract tests and record reconciliation.
- **NFR-AUDIT-002:** Evidence exposes provenance and integrity metadata sufficient to distinguish observed facts from inference. **Measure:** every finding used in release qualification links to authorized supporting evidence or an explicit limitation. **Validation:** end-to-end traceability review.
- **NFR-AUDIT-003:** Consequential approval/audit history is append-only when future writes are introduced. It is not an MVP execution feature. **Validation:** future Phase 8 tampering and replay tests.

## Accessibility

- **NFR-ACCESS-001:** Every semantic Assistant state and meaningful animation has a text alternative and assistive-technology label; state is not communicated by color alone. **Measure:** complete semantic-state mapping. **Validation:** component review and automated/manual accessibility tests.
- **NFR-ACCESS-002:** Reduced-motion mode preserves state, activity, approval, blocked/failure, progress, and completion meaning. **Measure:** functional equivalence across the state matrix. **Validation:** reduced-motion component tests.
- **NFR-ACCESS-003:** Keyboard navigation, visible focus, scalable layout/text, contrast, and voice captions/transcripts meet the selected accessibility standard. **Target standard/version:** **TBD** by product/legal decision. **Validation:** automated scans plus keyboard and screen-reader review.

## Performance

- **NFR-PERF-001:** The product reports task-source progress without waiting for the full investigation to finish once event delivery exists. **Target latency:** **TBD**. **Validation:** representative end-to-end latency measurement after event contracts and UI exist.
- **NFR-PERF-002:** Task creation, evidence browsing, and findings retrieval targets are **TBD** pending representative data sizes, model/runtime choice, network dependencies, and user research. **Validation:** define percentiles and concurrency after a benchmark workload is approved; run controlled load tests.
- **NFR-PERF-003:** Tool/model/browser operations have explicit timeouts and bounded retries appropriate to the source. **Target values:** **TBD per contract**. **Validation:** contract review and timeout/retry tests.

## Cancellation

- **NFR-CANCEL-001:** Cancellation is checked between task/agent/tool steps and before new tool calls. **Measure:** all cancellation injection points end in a truthful authoritative state without starting prohibited subsequent work. **Validation:** lifecycle and integration tests.
- **NFR-CANCEL-002:** Cancellation response target is **TBD** per tool interruptibility and safe-stop semantics. **Validation:** measure cooperative cancellation under representative tool/browser workloads and document non-interruptible boundaries.

## Recoverability

- **NFR-RECOVER-001:** Canonical task/audit state can be restored from PostgreSQL backups without depending on Redis. **RPO/RTO:** **TBD** after deployment and business-impact analysis. **Validation:** documented restore drills and state/evidence reconciliation.
- **NFR-RECOVER-002:** Restart recovery does not silently repeat completed governed work. **Measure:** all restart scenarios in the lifecycle matrix resolve through idempotency, reconciliation, or explicit human review. **Validation:** crash/restart tests.

## Maintainability

- **NFR-MAINT-001:** Domain code remains independent of FastAPI, database infrastructure, provider SDKs, Playwright, MCP SDKs, UI frameworks, and vendor internals. **Measure:** zero prohibited dependency violations. **Validation:** architecture tests.
- **NFR-MAINT-002:** Public contracts, policies, tools, events, and evidence schemas are versioned and documented before incompatible changes. **Measure:** all released contract changes include compatibility assessment. **Validation:** PR/checkpoint review.
- **NFR-MAINT-003:** Operational errors are structured, sanitized, classified, and actionable without secret-bearing dumps. **Validation:** error-contract and log-review tests.

## Extensibility

- **NFR-EXT-001:** AnythingLLM, LM Studio, Ollama, cloud models, MCP servers, browser engines, and enterprise systems remain behind Ophanim-owned contracts. **Measure:** provider replacement does not require domain-model changes. **Validation:** adapter contract and architecture tests.
- **NFR-EXT-002:** New agents, capabilities, tools, sources, and integrations require explicit registration, scope, policy, risk, timeout, audit, and tests. **Validation:** future registry/contract conformance tests.

## Testability

- **NFR-TEST-001:** Critical requirements trace through ADR, contract, implementation task, test, and evidence. **Measure:** 100% of release-blocking MVP requirement IDs have trace links before release qualification. **Validation:** traceability matrix review.
- **NFR-TEST-002:** Relevant behaviors have success, failure, denial, timeout, cancellation, and recovery coverage. **Measure:** coverage against an approved behavior matrix rather than a raw line-coverage number. **Validation:** S00-T10 and release test review.
- **NFR-TEST-003:** Browser, knowledge, database, log, voice, and private-data tests use controlled synthetic/non-sensitive fixtures. **Measure:** zero known private production fixtures. **Validation:** fixture inventory and secret/privacy scans.

## TBD Decision Register

| Decision | Owner/input needed | Validation method |
| --- | --- | --- |
| Production availability SLO | Business owner, deployment/support model | Pilot telemetry and dependency analysis |
| Performance percentiles and concurrency | Product owner, representative workload | Controlled load/latency testing |
| Tool timeout/retry budgets | Contract owners, source behavior | Fault-injection tests |
| Accessibility standard/version | Product/legal/accessibility review | Automated plus manual audit |
| RPO/RTO | Business impact and deployment design | Restore drills |
| Data classification and cloud routing | Security/privacy/business owners | Policy tests with synthetic classified data |
| Evidence/screenshot retention | Privacy/legal/operations | Storage lifecycle and access review |
| Operational diagnostic matrix | Operations/support owners | Incident simulation |

TBD values are not permission to omit safe defaults or validation. Before release, each applicable TBD must be decided, explicitly deferred with accepted risk, or shown not applicable.
