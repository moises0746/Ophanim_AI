# Ophanim AI Product Requirements

## Status and Scope

This document is the authoritative product-requirements baseline established by S00-T04. It distinguishes long-term product direction from the first production vertical slice. It defines outcomes and constraints, not implementation contracts or authorization to build future capabilities.

The first production vertical slice is the read-only Transaction Investigation Skill described in [Transaction Investigation Skill Scope](skills/transaction-investigation.md). Personas, journeys, and quality requirements are defined in [Personas](personas.md), [User Journeys](user-journeys.md), and [Non-Functional Requirements](non-functional-requirements.md).

## Product Vision

Ophanim AI is an AI Coworker platform centered on the animated Ophanim Assistant. Users communicate through text and, in later product increments, voice. Ophanim understands goals, creates governed plans, coordinates bounded specialized agents, retrieves approved knowledge, investigates approved systems, uses deterministic tools, navigates approved web applications when structured interfaces are insufficient, correlates evidence, and reports findings and recommended actions.

The Assistant is the default human-facing surface. It shows real Core state through semantic animation, Agent Mesh activity, active-agent connections, tool activity, task progress, an Activity Feed, approval-required presentation, and completion, blocked, or error states. These presentations derive from authoritative sanitized Core events, never fabricate work, and never expose hidden chain-of-thought.

Long-term capabilities may include voice, knowledge/RAG, AnythingLLM, LM Studio, optional Ollama, Obsidian, MCP, official APIs/SDKs, native browser investigation, approved database/log/cloud/infrastructure investigation, research, documentation, operational assistance, content workflows, and future approval-gated actions. Inclusion in the vision does not make a capability part of the MVP.

## Product Principles

- Ophanim Core is the control plane.
- Models plan, analyze, classify, summarize, and recommend; governed deterministic tools execute.
- The MVP is read-only and ends with findings and recommendations.
- The Assistant reports real auditable activity without exposing hidden chain-of-thought.
- Agent Mesh participants are bounded capability profiles subordinate to Core policy.
- Evidence, provenance, policy decisions, and audit are product records, not incidental logs.
- Safe failure, cancellation, least privilege, and explicit scope take priority over maximum autonomy.
- Integration preference follows API/SDK, governed MCP, constrained SDK/CLI, deterministic browser, AI browser, vision, then controlled raw input.

## Product Boundaries

| Component | Product role | Not its role |
| --- | --- | --- |
| Ophanim Core | Authoritative control plane for tasks, orchestration, policy, tools, evidence, audit, and Assistant activity | A thin proxy around a model or vendor product |
| Ophanim Assistant | Default human-facing product surface and truthful presentation of Core activity | An autonomous policy bypass or static logo |
| Agent Mesh | Bounded specialist delegation model and activity visualization | Independent processes with unrestricted credentials or tools |
| AnythingLLM | Initial replaceable knowledge subsystem | Workflow, approval, evidence, or audit database |
| LM Studio | Initial local model runtime behind an Ophanim adapter | Control plane or hard-coded domain dependency |
| Ollama | Optional/alternative local runtime with separately governed final disposition | Mandatory MVP runtime |
| Obsidian | Human-readable, explicitly scoped knowledge source | Application persistence or default test-fixture source |
| PostgreSQL | Authoritative application system of record | Optional cache |
| Redis | Transient coordination/cache | Authoritative application persistence |
| MCP | Governed integration protocol | Authorization bypass |
| Native Browser | Approved application investigation fallback when preferred structured interfaces are unavailable or insufficient | Unrestricted browser automation or personal-profile control |

## Functional Requirements

### Task and Lifecycle

- **FR-TASK-001:** An authorized MVP user can create an investigation task from a transaction/reference number and required environment/scope context.
- **FR-TASK-002:** Core assigns a stable task identity and exposes authoritative lifecycle state, including created, planning, working, blocked, cancelling/cancelled, failed, and completed concepts; exact contract enums are deferred.
- **FR-TASK-003:** Material task transitions are persisted with correlation and audit metadata when persistence is implemented.
- **FR-TASK-004:** A completed task exposes findings, recommendations, supporting evidence references, limitations, and source/tool status.

### Planning and Agent Mesh

- **FR-PLAN-001:** Ophanim produces a bounded investigation plan identifying required approved capabilities and source categories before governed execution.
- **FR-PLAN-002:** The plan remains subordinate to authorization, environment/data scope, tool allowlists, policy, budgets, and cancellation.
- **FR-AGENT-001:** Core may delegate bounded steps to specialist Agent Mesh profiles whose declared capabilities match the step.
- **FR-AGENT-002:** Delegation never transfers credentials, policy authority, or unrestricted execution rights to an agent.

### Governed Tools and Read-Only Enforcement

- **FR-TOOL-001:** Every tool invocation uses a registered deterministic tool with typed bounded inputs/outputs, explicit timeout, risk classification, and auditable identity.
- **FR-TOOL-002:** Core evaluates identity, RBAC, environment, data scope, capability/tool allowlist, and policy before invocation; credentials are resolved only at execution time.
- **FR-TOOL-003:** Tool results are sanitized and treated as potentially untrusted input.
- **FR-READ-001:** MVP tool boundaries deterministically deny external state-changing actions, including indirect browser submissions, uploads, database writes, shell execution, and unsafe fallbacks.
- **FR-READ-002:** A request that cannot be completed read-only stops as denied, blocked, failed, or incomplete rather than expanding authority.

### Investigation Sources

- **FR-BROWSER-001:** Ophanim may inspect an approved test/read-only web portal using registered applications/domains, dedicated browser profiles, bounded read/navigation actions, and evidence capture.
- **FR-BROWSER-002:** Browser use follows the integration preference order and is selected only when preferred structured interfaces are unavailable or insufficient.
- **FR-DATA-001:** Approved database retrieval uses predefined or parameterized read-only operations; users and models cannot submit arbitrary SQL.
- **FR-LOG-001:** Approved log retrieval supports bounded searches over authorized environments, time ranges, and data scopes without exposing unrestricted query or command execution.
- **FR-KNOW-001:** Knowledge retrieval may supply policies, mappings, runbooks, and context from explicitly approved sources with provenance and citations.
- **FR-KNOW-002:** Knowledge-system failure degrades or blocks the relevant step without changing canonical task/audit authority.

### Evidence, Correlation, and Results

- **FR-EVIDENCE-001:** Every material fact or artifact used in findings retains task, source, tool, capture-time, classification, integrity, and verification metadata appropriate to policy.
- **FR-EVIDENCE-002:** Screenshots are captured only when needed, from approved applications, and retained/accessed according to classification and policy.
- **FR-EVIDENCE-003:** Ophanim distinguishes observed evidence, derived inference, issue classification, recommendation, and unverified limitation.
- **FR-ANALYSIS-001:** Ophanim correlates authorized transaction, browser, database, log, and knowledge evidence by relevant identifiers and chronology.
- **FR-ANALYSIS-002:** Ophanim produces a likely issue classification with supporting evidence and uncertainty/limitations.
- **FR-RESULT-001:** Findings summarize what was observed and why the classification is supported.
- **FR-RESULT-002:** Recommendations describe human-reviewable next steps and never claim that remediation occurred.

### Assistant, Activity, Cancellation, and Failure

- **FR-ASSISTANT-001:** The Assistant presents authoritative semantic state, task progress, active agents, tool activity, evidence count, blocked/failure information, and completion status from sanitized Core events.
- **FR-ASSISTANT-002:** Every Activity Feed item corresponds to a real auditable Core event; the UI does not fabricate activity with timers or model narration.
- **FR-ASSISTANT-003:** The UI exposes no hidden chain-of-thought, credentials, raw secret-bearing payloads, or private provider internals.
- **FR-CANCEL-001:** An authorized user can request cancellation; Core checks cancellation between steps and before tool calls and reports the final cancellation outcome.
- **FR-FAIL-001:** Timeouts, unavailable dependencies, policy denials, insufficient evidence, and unsafe requests produce explicit sanitized blocked/failure states without authority expansion.
- **FR-FAIL-002:** Partial investigations identify completed and incomplete sources so findings are not presented as comprehensive.

### Audit and Governance

- **FR-AUDIT-001:** Material task, planning, delegation, policy, tool, evidence, cancellation, failure, and completion activity produces correlated audit metadata.
- **FR-AUTH-001:** Access is restricted by authenticated identity, RBAC, workspace/data scope, environment, capability, and policy.
- **FR-POLICY-001:** Policy decisions are explicit, version-identifiable, reasoned, and tied to the relevant task/tool request when implemented.

## Security Requirements

- **SEC-001:** Apply least privilege and default-deny authorization to identities, capabilities, tools, data, environments, applications, domains, commands, and paths.
- **SEC-002:** Enforce RBAC and explicit environment/data scope at both API and tool boundaries.
- **SEC-003:** Agents never own credentials; tools resolve opaque secret references from an approved vault/provider at execution time.
- **SEC-004:** Do not expose secret values in prompts, Assistant events, evidence, fixtures, or normal logs.
- **SEC-005:** Prohibit arbitrary SQL, arbitrary shell, unrestricted filesystem access, unrestricted browser automation, and controlled-raw-input use without explicit later authorization.
- **SEC-006:** Browser investigation uses approved applications/domains, dedicated isolated profiles, bounded navigation/actions, and safe redirect/domain-escape handling.
- **SEC-007:** Treat browser pages, knowledge, MCP resources, logs, database content, model output, and tool output as potentially prompt-injected/untrusted.
- **SEC-008:** Preserve evidence provenance and integrity metadata; consequential audit/approval history uses append-only semantics when implemented.
- **SEC-009:** The MVP exposes no remediation or external write path. Future consequential/state-changing actions require exact human approval under ADR-009 and separate implementation authorization.
- **SEC-010:** Separate development, test, and production environments and prevent cross-environment credential or data-scope use.
- **SEC-011:** Assistant/Agent events are authorized and sanitized and expose neither hidden chain-of-thought nor secret/private provider internals.
- **SEC-012:** Cancellation, pause, and emergency-stop behavior must fail safely and must not be bypassed by agents or tools.

## Requirements Traceability Baseline

| Requirement group | Governing ADRs | Next specification/implementation owner |
| --- | --- | --- |
| FR-TASK, FR-PLAN, FR-AGENT | ADR-001, ADR-002, ADR-011 | S00-T05 and Phase 1 Core tasks |
| FR-TOOL, FR-READ | ADR-002, ADR-008, ADR-009, ADR-014 | S00-T05, S00-T07, S00-T08, later tool tasks |
| FR-BROWSER | ADR-006, ADR-007, ADR-014 | S00-T08 and Phase 4 |
| FR-DATA, FR-LOG | ADR-002, ADR-006, ADR-014 | Phase 5/6 governed read-tool tasks |
| FR-KNOW | ADR-003, ADR-004, ADR-012 | Phase 2 knowledge/model tasks |
| FR-EVIDENCE, FR-AUDIT | ADR-011, ADR-013 | Phase 1 evidence/audit/persistence tasks |
| FR-ASSISTANT | ADR-010, ADR-013 | S00-T06 and Phase 3 |
| SEC-001 through SEC-012 | ADR-002, ADR-005 through ADR-015 as applicable | S00-T05 through S00-T10 and implementation security tests |

Future contracts, implementation tasks, tests, and evidence must cite stable requirement IDs rather than relying only on prose.

## Voice Classification

Voice interaction, listening visualization, and real audio-reactive speaking are product direction and part of a later Assistant increment. Text input is sufficient for the first transaction-investigation backend slice. Voice recognition, VAD, STT, TTS, wake word, speaker verification, and always-on listening are not immediate MVP acceptance requirements unless a later explicitly authorized task changes the product scope.

## Deferred Product Decisions

Business owners must later determine production data sources, supported environments, identity provider and role matrix, retention periods, evidence export, classification policy, issue taxonomy, service availability targets, performance/load targets, deployment topology, and which future write actions are worth proposing. Validation methods are listed in the NFR document.
