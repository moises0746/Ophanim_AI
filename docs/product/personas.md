# Ophanim AI Personas

## Scope

Personas describe user needs and authority boundaries; they do not grant permissions. Actual access is determined by authenticated identity, RBAC, environment/data scope, policy, and tool allowlists.

## MVP Personas

### Operations Analyst

**MVP role:** Primary investigation user.

**Goals:** Quickly understand a transaction failure or anomaly, gather evidence across approved sources, apply policies/runbooks, and produce a defensible finding without manually switching among many systems.

**Needs:** Text-based reference intake, visible progress, source status, evidence provenance, issue classification, findings, recommendations, cancellation, and clear limitations.

**Authority boundary:** May investigate only assigned environments/data scopes using approved read-only tools. Cannot remediate, retry transactions, change records, send communications, or expand scope.

### L1/L2 Support Engineer

**MVP role:** Primary or secondary investigation user.

**Goals:** Triage reported incidents, determine likely ownership/cause, compare evidence with known mappings/runbooks, and prepare escalation information.

**Needs:** Repeatable investigation flow, sanitized Activity Feed, evidence review, partial-failure visibility, citations, and export/share behavior when later authorized.

**Authority boundary:** Same read-only constraints as the Operations Analyst, further limited by assigned systems, customers, environments, and data classifications.

### Team Lead / Approver

**MVP role:** Findings reviewer and governance stakeholder; no MVP write approval execution.

**Goals:** Review investigation quality, confirm evidence supports conclusions, identify blocked work, and supervise cancellation/escalation.

**Needs:** Findings/evidence traceability, audit history, task status, limitations, and role-appropriate access. Future approval UX is relevant, but the MVP exposes no write action to approve.

**Authority boundary:** Review authority does not grant unrestricted source access or tool execution. Future consequential approval must be exact and separately implemented.

## Future/Administrative Personas

### Cloud/Platform Engineer

**MVP role:** Future/optional subject-matter reviewer; not required as the primary user of the transaction slice.

**Future goals:** Investigate infrastructure, cloud, Kubernetes, deployment, and service-health evidence and propose operational responses.

**Future needs:** Scoped cloud/log/metrics integrations, topology context, environment separation, and eventually narrowly approval-gated actions.

**Boundary:** Infrastructure mutation, restart, deploy, permission change, and arbitrary CLI access are outside the MVP.

### Platform Administrator

**MVP role:** Future deployment/governance operator; required operational responsibilities may exist, but a full administration product surface is not part of the transaction slice.

**Future goals:** Configure identity/RBAC, approved tools/sources, environments, secret references, policies, retention, provider health, and audit access.

**Future needs:** Administrative controls, separation of duties, configuration audit, health/observability, backup/recovery, and vendor/provider lifecycle management.

**Boundary:** Administrators configure governance; they do not give agents credentials or bypass audit, data scope, approval, or read-only enforcement.

## Persona-to-Journey Matrix

| Journey | Operations Analyst | L1/L2 Support | Team Lead / Approver | Cloud/Platform Engineer | Platform Administrator |
| --- | --- | --- | --- | --- | --- |
| Text-based investigation | Primary | Primary | Review | Future/optional | Support/configure |
| Activity/progress visibility | Primary | Primary | Oversight | Future | Operational oversight |
| Evidence/findings review | Primary | Primary | Primary reviewer | Future SME | Scoped audit review |
| Failure/blocked handling | Primary | Primary | Escalation oversight | Future | Configuration diagnosis |
| Cancellation | Own/authorized task | Own/authorized task | Policy-dependent oversight | Future | Emergency control |
| Knowledge-assisted investigation | Primary | Primary | Review | Future SME | Configure sources/policy |

## Cross-Persona Requirements

- Users see only tasks, sources, evidence, events, and actions allowed by identity and scope.
- The Assistant never implies that a user has authority they do not possess.
- Accessibility and text fallback apply across personas.
- Hidden chain-of-thought and credentials are never a persona entitlement.
- Persona labels do not replace organization-specific RBAC design, which remains TBD.
