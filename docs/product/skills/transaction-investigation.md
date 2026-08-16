# Transaction Investigation Skill Scope

## Skill Outcome

The first production skill on the orchestration platform lets an authorized operations user submit a transaction/reference number and receive an evidence-grounded issue classification, findings, limitations, and recommended next steps from approved read-only sources. The user can observe real progress through the Ophanim Assistant and review evidence and audit activity. The skill performs no remediation or external write action.

## Primary Workflow

1. The user submits a transaction/reference number with authorized environment/scope context.
2. Ophanim Core instantiates the Transaction Investigation Skill.
3. The Skill execution determines a bounded investigation plan based on its manifest.
4. Policy authorizes the required read-only capabilities and tools.
5. Approved tools retrieve transaction information.
6. If structured interfaces are unavailable or insufficient, Ophanim may navigate an approved test/read-only portal with a dedicated profile.
7. Approved parameterized read-only database tools retrieve relevant records.
8. Approved bounded log tools search relevant logs.
9. Approved knowledge sources may provide policies, mappings, runbooks, and context with provenance.
10. Ophanim correlates evidence and identifies gaps or contradictions.
11. Ophanim classifies the likely issue and records uncertainty.
12. Ophanim generates findings and recommends human-reviewable next steps.
13. Evidence, necessary screenshots, tool activity, policy decisions, and audit metadata are retained according to policy.
14. The user sees real task/activity progress, blocked/failure states, and completion through the Assistant.
15. No remediation or external write action occurs.

## In Scope

- Text-based reference intake.
- Durable task identity and lifecycle when the persistence task is implemented.
- Bounded planning and specialist Agent Mesh delegation.
- Governed deterministic read-only tools.
- Approved portal investigation as a bounded fallback.
- Approved parameterized database retrieval.
- Approved bounded log retrieval.
- Optional approved knowledge retrieval with citations/provenance.
- Evidence and screenshot metadata, correlation, classification, findings, limitations, and recommendations.
- Sanitized authoritative Assistant/Activity Feed presentation.
- Cancellation, safe blocked/failure outcomes, authorization, policy, data/environment scope, and audit metadata.

## Explicit Non-Goals

The Skill does not perform or expose:

- automatic remediation;
- restarting services;
- retrying or replaying transactions;
- modifying databases or arbitrary SQL;
- sending emails, chat messages, notifications to external recipients, or tickets;
- publishing content;
- uploading files to external systems;
- changing cloud, infrastructure, Kubernetes, or application resources;
- changing credentials, permissions, roles, or policies;
- installing software or dependencies;
- purchases, payments, or financial execution;
- unrestricted shell or command execution;
- unrestricted browser automation, personal browser profiles, or unapproved domains;
- unrestricted filesystem access;
- autonomous production changes;
- approval-gated write execution merely because approval UX exists;
- broad autonomous desktop control;
- hidden chain-of-thought display;
- mandatory voice recognition, VAD, STT, TTS, wake word, or always-on microphone processing;
- general-purpose research, content publishing, meeting coaching, or multi-user enterprise administration.

## Read-Only Skill Boundary

Read-only is an execution boundary, not a label. Tool definitions, policy, browser action classification, database operations, log operations, MCP capabilities, and fallbacks must deny state changes. If a source requires a write, unsafe login flow, upload, form submission, arbitrary query, or unsupported fallback, the step stops safely and the result records the limitation.

Future human approval does not make writes part of this Skill MVP. Any future consequential action requires ADR-009 controls and a separately authorized Phase 8 implementation.

## Browser Boundary

Browser use is optional and subordinate to the integration preference order. It is permitted only for registered approved test/read-only applications and domains, using dedicated profiles and bounded read/navigation actions. DOM/accessibility inspection is preferred; AI reasoning and vision are governed fallbacks. Raw coordinate input is not an MVP default and cannot expand scope.

## Voice Boundary

Voice is product direction, not required for the first transaction-investigation backend slice. The initial journey is fully operable through text. Later Assistant work may add push-to-talk and speaking presentation without changing the investigation's read-only authority.

## MVP Entry Conditions

Before production qualification, the vertical slice requires completed contracts and implementations for task state, authorization/policy, read-only tools, evidence/audit, cancellation, Assistant activity, approved-source configuration, and controlled test environments. Exact sequencing remains governed by authorized tasks and ADRs.

## MVP Exit Evidence

Release evidence must demonstrate:

- an authorized reference creates one correlated task;
- only approved read-only sources and scoped tools are used;
- denied writes and scope escapes fail closed;
- source failures and partial results are visible;
- evidence supports classification and findings;
- recommendations are clearly non-executed;
- Activity Feed entries correspond to auditable Core events;
- cancellation produces an accurate final state;
- no external state mutation occurs.

## Product/Business Decisions Still TBD

- Supported transaction systems and reference formats.
- Initial test/read-only portal and database/log source inventory.
- Issue classification taxonomy and confidence/uncertainty presentation.
- Evidence and screenshot retention/export policy.
- Required identity provider, role assignments, and production environment model.
- Production performance, availability, recovery, and capacity targets after representative load testing.
