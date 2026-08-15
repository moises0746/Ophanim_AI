# Ophanim AI Architecture Decision Records

All baseline ADRs below are **Accepted**. Their acceptance records architecture direction; it does not authorize the deferred implementation described by each ADR.

| ADR | Decision |
| --- | --- |
| [ADR-001](ADR-001-modular-monolith-first.md) | Modular Monolith First |
| [ADR-002](ADR-002-ai-plans-deterministic-tools-execute.md) | AI Plans, Deterministic Tools Execute |
| [ADR-003](ADR-003-anythingllm-replaceable-knowledge-subsystem.md) | AnythingLLM as Replaceable Knowledge Subsystem |
| [ADR-004](ADR-004-lm-studio-initial-local-model-runtime.md) | LM Studio as Initial Local Model Runtime |
| [ADR-005](ADR-005-mcp-first-class-governed-tool-protocol.md) | MCP as First-Class Governed Tool Protocol |
| [ADR-006](ADR-006-integration-preference-order.md) | Integration Preference Order |
| [ADR-007](ADR-007-chromium-playwright-native-browser-foundation.md) | Chromium/Playwright Native Browser Foundation |
| [ADR-008](ADR-008-agents-do-not-own-credentials.md) | Agents Do Not Own Credentials |
| [ADR-009](ADR-009-consequential-actions-require-human-approval.md) | Consequential Actions Require Human Approval |
| [ADR-010](ADR-010-event-driven-ophanim-assistant-animation.md) | Event-Driven Ophanim Assistant and Animation |
| [ADR-011](ADR-011-postgresql-authoritative-system-of-record.md) | PostgreSQL as Authoritative System of Record |
| [ADR-012](ADR-012-obsidian-human-readable-knowledge-source.md) | Obsidian as Human-Readable Knowledge Source |
| [ADR-013](ADR-013-evidence-audit-first-class-records.md) | Evidence and Audit as First-Class Records |
| [ADR-014](ADR-014-read-only-mvp-first.md) | Read-Only MVP First |
| [ADR-015](ADR-015-vendor-source-isolated.md) | Vendor Source Isolated from Ophanim Product Logic |
| [ADR-016](ADR-016-autonomous-agent-orchestration.md) | Deterministic State-Driven Autonomous Agent Orchestration |
| [ADR-017](ADR-017-polyglot-runtime-boundaries.md) | Polyglot Runtime Boundaries: Python Control Plane and Evidence-Gated Rust |

## Record Format

Each ADR contains status, context, decision, rationale, consequences, rejected alternatives, security impact, operational impact, testing impact, and follow-up/deferred work.

Later changes must preserve history: supersede an accepted ADR with a new record or an explicit status update rather than silently rewriting architecture during implementation.
