# Ophanim AI MVP User Journeys

## Journey Conventions

These journeys describe product behavior and outcomes. Exact APIs, schemas, UI flows, state enums, and transport remain deferred. Every journey is read-only, authorized, scoped, auditable, and cancellable where execution is active.

## JRN-001: Text-Based Transaction Investigation

**Primary persona:** Operations Analyst or L1/L2 Support Engineer.

**Preconditions:** The user is authenticated and authorized for the selected environment/data scope; the reference format is accepted; required read-only sources are configured or can report unavailable.

**Flow:**

1. The user enters a transaction/reference number and selects or confirms allowed context.
2. Ophanim validates input and creates one investigation task.
3. The Assistant shows created/planning state from Core activity.
4. Core forms a bounded plan and delegates matching steps.
5. Governed tools query approved transaction, database, log, knowledge, and optional portal sources.
6. Ophanim correlates evidence and identifies conflicts or missing sources.
7. Ophanim presents classification, findings, limitations, recommendations, and evidence links.

**Success outcome:** The task completes with traceable evidence and no external mutation.

**Alternative outcomes:** Invalid/unauthorized input is denied; unavailable sources create a partial or blocked result; insufficient evidence prevents false certainty.

## JRN-002: Assistant Activity and Progress Visibility

**Primary personas:** All authorized task viewers.

1. The user opens or remains on the Assistant surface.
2. Semantic Assistant state, Agent Mesh connections, tool activity, progress, evidence count, blocked/failure state, and completion derive from sanitized authoritative Core events.
3. The Activity Feed shows real auditable events in understandable language.
4. Reduced-motion and text fallback communicate the same state.

**Guardrails:** Local timers may animate a current state but cannot invent work or transitions. The UI exposes no hidden chain-of-thought, credentials, or raw private provider data.

## JRN-003: Evidence Review

**Primary personas:** Operations Analyst, L1/L2 Support Engineer, Team Lead / Approver.

1. The user opens evidence associated with a finding or source step.
2. Ophanim shows authorized provenance, source, capture time, classification, integrity/verification status, and sanitized content or artifact reference.
3. The user can distinguish evidence from inference and recommendation.
4. Missing, inaccessible, expired, or unverifiable evidence is clearly marked.

**Guardrails:** Evidence access is scoped; screenshot/private content follows retention and classification policy; raw secrets are never displayed.

## JRN-004: Findings and Recommendations Review

**Primary personas:** Operations Analyst, L1/L2 Support Engineer, Team Lead / Approver.

1. The user reviews the likely issue classification and confidence/limitations.
2. Each material finding links to supporting evidence.
3. Recommendations describe next steps for a human or later governed workflow.
4. The product explicitly states that no remediation, retry, communication, or external write occurred.

**Outcome:** The user can accept the result for handoff, request a new authorized investigation, or escalate based on gaps; exact review workflow remains TBD.

## JRN-005: Failure or Blocked Investigation

**Primary personas:** Operations Analyst and L1/L2 Support Engineer; Team Lead reviews escalation.

1. A dependency is unavailable, policy denies a capability, scope is insufficient, a timeout occurs, evidence conflicts, or a safe read-only path does not exist.
2. Core stops or degrades the affected step without broadening authority.
3. The Assistant shows blocked or failed state and a sanitized reason.
4. Completed sources and partial evidence remain visible.
5. The result identifies what is missing and a human-reviewable next step.

**Guardrails:** Failure never silently becomes browser/vision/raw-input escalation outside policy and never produces fabricated completion.

## JRN-006: Cancellation

**Primary persona:** Authorized task owner or operator.

1. The user requests cancellation from the task/Assistant surface.
2. Core records the request and checks it between steps and before tool execution.
3. Active bounded operations receive cooperative cancellation where supported.
4. Core records whether cancellation completed, was too late for an already completed read, or encountered a failure.
5. The Assistant and audit history reflect the authoritative final state.

**Guardrails:** Cancellation does not delete audit/evidence records or imply rollback of an external mutation; the MVP performs no such mutation.

## JRN-007: Knowledge-Assisted Investigation

**Primary personas:** Operations Analyst and L1/L2 Support Engineer.

1. The plan requests an approved knowledge capability for mappings, policies, or runbooks.
2. The knowledge adapter queries explicitly scoped sources.
3. Results include provenance/citations and are treated as untrusted input.
4. Ophanim compares knowledge guidance with observed transaction/system evidence.
5. Findings identify which statements derive from knowledge versus observed systems.

**Alternative outcomes:** Knowledge is unavailable, out of scope, stale, conflicting, or insufficient; the task continues only where safe and reports the limitation.

## Voice Direction

A future push-to-talk journey may replace text entry and add real listening/speaking presentation. It must feed the same Core task, authorization, activity, and cancellation paths. Voice identity alone cannot authorize access or consequential actions. Voice is not required for JRN-001 through JRN-007 in the first transaction-investigation backend slice.

## Journey Traceability

| Journey | Principal requirements |
| --- | --- |
| JRN-001 | FR-TASK, FR-PLAN, FR-AGENT, FR-TOOL, FR-READ, FR-ANALYSIS |
| JRN-002 | FR-ASSISTANT, FR-AUDIT, NFR-ACCESS, NFR-AUDIT |
| JRN-003 | FR-EVIDENCE, FR-AUTH, SEC-004, SEC-008 |
| JRN-004 | FR-RESULT, FR-EVIDENCE, FR-READ |
| JRN-005 | FR-FAIL, FR-POLICY, FR-READ, NFR-RELIABILITY |
| JRN-006 | FR-CANCEL, FR-AUDIT, NFR-CANCEL |
| JRN-007 | FR-KNOW, FR-EVIDENCE, SEC-007 |
