# Ophanim Threat Model

## System and Security Objectives

Ophanim is a control plane coordinating an Assistant, bounded Agent Mesh profiles, untrusted model runtimes, knowledge and integration adapters, deterministic tools, browser automation, evidence, policy, approval, and auditable state. The security objective is to preserve user intent, scope, confidentiality, integrity, availability, and truthful outcomes while the MVP remains read-only.

Trust boundaries are detailed in [Trust Boundaries](trust-boundaries.md). Assets and practical handling classes are in [Asset Classification](asset-classification.md). This is a design baseline, not a claim that controls are implemented.

## STRIDE-Style Threat Register

| ID | Category | Threat | Primary assets/boundaries | Required control direction |
|---|---|---|---|---|
| T-STRIDE-01 | Spoofing | Forged desktop/user, agent, tool, provider, approval, or event identity | User/Desktop/Core, event delivery, approval | Authenticated scoped identities, signed/integrity-bound records, client cannot author approval/state. |
| T-STRIDE-02 | Tampering | Task, policy, tool parameters, evidence, event sequence, or configuration altered | Core/PG, tools, artifacts | Immutable IDs, version/digest binding, constraints, append-oriented audit, integrity checks. |
| T-STRIDE-03 | Repudiation | Actor denies task, approval, tool action, or source observation | Core, tools, evidence | Correlation, actor identity, timestamps, policy/tool versions, provenance, append-oriented history. |
| T-STRIDE-04 | Information disclosure | Secrets, private knowledge, screenshots, transcripts, prompts, or evidence leak | Models, events, logs, browser, storage | Classification, minimization, field redaction, scoped delivery, secret-provider isolation, fail closed. |
| T-STRIDE-05 | Denial of service | Provider, MCP, browser, PG, Redis, or event consumer unavailable or overloaded | All integration boundaries | Timeouts, bounded retries, cancellation, backpressure, degraded mode, PG recovery, Redis non-authority. |
| T-STRIDE-06 | Elevation of privilege | Agent/model/tool/fallback/delegation gains broader capability or environment | Core policy, Agent Mesh, tools | Default deny, subset delegation, exact allowlists, no self-grant, approval and verification gates. |

## AI-Specific Threat Register

| ID | Threat | Safe control direction |
|---|---|---|
| T-AI-01 | Direct or indirect prompt injection in documents, pages, logs, MCP resources, or tool output | Treat content as data; isolate instructions; independently validate every tool request; preserve provenance. |
| T-AI-02 | Tool poisoning or malicious MCP metadata advertises dangerous behavior as read-only | Registration, server identity, schema/risk review, capability/tool allowlists, policy evaluation; discovery never authorizes. |
| T-AI-03 | Hallucinated model output influences action or claims success | Models propose only; typed deterministic tools execute; deterministic verification and evidence required. |
| T-AI-04 | Context poisoning or poisoned knowledge document changes policy interpretation | Classification, source scope, citations, sanitization, no content-granted authority, independent policy boundary. |
| T-AI-05 | Malicious browser content or deceptive UI induces unsafe action | Approved domains/apps, DOM-first inspection, action classification, redirect/popup controls, no unrestricted writes. |
| T-AI-06 | Cross-domain browser escape or unsafe fallback escalation | Dedicated profiles, allowlists, redirect checks, ADR-006 preference order, fallback cannot widen scope. |
| T-AI-07 | Credential exfiltration through prompts, events, logs, screenshots, or tool outputs | Agents own no credentials; runtime-only secret refs; redaction and classification; no personal profile. |
| T-AI-08 | Agent privilege expansion, cross-agent sharing, or confused deputy | Bounded profile/version, subset delegation, task/environment/data scope, no self-grant or credential sharing. |
| T-AI-09 | Approval spoofing, stale approval reuse, replay, or tampering | Authenticated human, exact normalized digest/destination/environment/expiry/preconditions, anti-replay, fail closed. |
| T-AI-10 | Audit/evidence tampering or fabricated Activity Feed | Core-authored material events, immutable IDs/hashes/provenance, PostgreSQL authority, UI projection only. |
| T-AI-11 | Event replay, duplicate, stale, or out-of-order delivery misstates Assistant state | Per-task sequence, cursors, idempotent reducer, gap/resync marker, visibility filtering. |
| T-AI-12 | Tenant/workspace/data-scope escape or cloud-routing violation | Scope on every boundary, classification/routing policy, authorization before delivery, unknown scope denies. |

## Highest-Risk Threats

The highest-consequence risks are credential exfiltration (T-AI-07), confused-deputy/privilege expansion (T-STRIDE-06/T-AI-08), malicious browser/MCP content causing action (T-AI-01/T-AI-02/T-AI-05), approval replay/spoofing (T-AI-09), and fabricated or tampered evidence/events (T-AI-10/T-AI-11). Read-only MVP scope reduces impact but does not remove disclosure, impersonation, integrity, or availability risk.

## Control Principles

- Core is the control plane; no model, agent, UI, vendor subsystem, MCP server, browser, Redis cache, or evidence store bypasses Core policy.
- API/SDK → governed MCP → constrained SDK/CLI → deterministic browser → AI browser → vision → controlled raw input remains the integration preference order.
- PostgreSQL is authoritative for canonical state, material events, policy, approval, evidence, and audit; Redis is transient only.
- AnythingLLM and Obsidian are knowledge sources/subsystems, not workflow or audit authority.
- The MVP has no mutation path. Future consequential actions require exact human approval and separate implementation authorization.

## Traceability

SEC-001..012; FR-TASK, FR-AGENT, FR-TOOL, FR-EVIDENCE, FR-ASSISTANT, FR-CANCEL, FR-FAIL, FR-AUDIT; NFR-SEC-001..003, NFR-PRIV-001..003, NFR-OBS-001..002, NFR-AUDIT-001..003, NFR-ACCESS-001..003, NFR-CANCEL-001..002, NFR-RECOVER-001..002; ADR-001..015.
