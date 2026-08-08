# Product Milestones

## M1 — Dependable control loop

Outcome: a user-created task survives restart, invokes one governed tool, waits for approval when required, verifies the result, and produces a notification and audit trail.

Exit criteria:

- persistent task/step/event/artifact/approval schema;
- migrations and recovery behavior;
- task API and event stream;
- provider capability registry;
- tool policy and approval continuation;
- tests for restart, denial, timeout, cancellation, and duplicate execution risk.

## M2 — Desktop control center

Outcome: the owner can operate and supervise M1 without using raw API calls.

Exit criteria:

- authenticated local desktop-to-core connection;
- Home, Chat, Tasks, Approval, and Settings surfaces;
- clear provider and privacy indicators;
- streaming task timeline;
- pause, cancel, mute, and emergency stop;
- Windows notifications and in-app inbox.

## M3 — Grounded knowledge and memory

Outcome: answers and plans cite approved knowledge; accepted memories remain understandable and editable by the owner.

Exit criteria:

- AnythingLLM retrieval adapter with citations;
- Obsidian read adapter and governed write proposals;
- source, confidence, sensitivity, and retention metadata;
- prompt-injection boundary tests;
- memory review and deletion controls.

## M4 — Governed computer use

Outcome: one browser workflow and one Windows application workflow run safely with observation, policy checks, approval, and verification.

Exit criteria:

- application/domain/action allowlists;
- structured browser and Windows UI Automation targets;
- vision/raw-input fallback policy;
- visible automation state and emergency stop;
- minimal screenshot retention;
- failure recovery and post-action evidence.

## M5 — Virtual team

Outcome: a Chief of Staff can delegate bounded work to specialist roles and deliver a consolidated, reviewed result.

Exit criteria:

- role profiles and versioned instructions;
- child tasks, dependencies, budgets, and bounded delegation;
- independent review for selected tasks;
- scheduled workflows and daily digest;
- remote approval/notification channel;
- quality, cost, latency, and intervention metrics.

## Deferred until the foundation is reliable

- broad autonomous desktop control;
- many character-driven agent personas;
- production infrastructure mutation;
- always-on microphone processing;
- autonomous purchases or financial actions;
- multi-user enterprise administration.
