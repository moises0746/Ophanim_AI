# Task Checkpoint: R1-13 (Hybrid Routing Refactor)

**Task ID**: R1-13-hybrid-routing
**Status**: COMPLETED
**Completed at**: 2026-08-16

**Objective**: 
Migrate the system from `PrivacyMode` to the more robust `RoutingMode` (LOCAL_ONLY, CLOUD_ONLY, HYBRID_ROUTED) and lay the architectural foundation for a Hybrid Model Provider layer that supports fallbacks without risking local-only data leakage.

**Scope delivered**: 
- Renamed `PrivacyMode` to `RoutingMode` system-wide.
- Updated `ModelCompletionRequest` and `ModelCompletionResponse` domains to include `routing_reason` and `fallback_occurrence`.
- Updated React frontend UI (`ConversationPanel`, `AppShell`) and hooks to use `RoutingMode` and display routing provenance.
- Passed full test suite on backend (pytest, 158 tests) and frontend (vitest, 13 tests).

**Files changed**:
- `services/ophanim-core/ophanim/domain/values.py`
- `services/ophanim-core/ophanim/adapters/model_router.py`
- `services/ophanim-core/ophanim/persistence/sql_models.py`
- `services/ophanim-core/tests/*` (including `test_assistant_chat_api.py`, `test_task_lifecycle.py`, `test_sql_persistence.py`, `test_model_router.py`, `test_domain_types.py`, `test_cloud_model_providers.py`)
- `apps/desktop/src/types/events.ts`
- `apps/desktop/src/hooks/useAssistantWorkspace.ts`
- `apps/desktop/src/app/AppShell.tsx`
- `apps/desktop/src/components/ConversationPanel.tsx`
- `apps/desktop/src/__tests__/*` (including `App.test.tsx`, `runtime.test.ts`)

**Architecture impact**: 
Replaces the binary privacy flag with explicit routing topologies. This allows the Ophanim orchestration layer to route requests through a unified `ModelRouter` interface that gracefully handles fallback attempts while strictly enforcing boundary rules (e.g., `LOCAL_ONLY`).

**Security impact**: 
Prevents accidental cloud dispatch for `LOCAL_ONLY` workloads by formalizing the router boundaries and making data classification explicit. `HYBRID_ROUTED` mode is introduced securely without modifying the strictness of local modes.

**Tests and results**:
- `pytest` on `services/ophanim-core`: Passed (158 passed)
- `ruff check` on `services/ophanim-core`: Passed (0 errors)
- `vitest run` on `apps/desktop`: Passed (13 passed)
- `git diff --check`: Passed (No trailing whitespace)

**Acceptance criteria verification**: 
Verified that all components now read and emit `routing_mode` instead of `privacy_mode`, and the API handles JSON correctly. The provider fallback metrics (`routing_reason`, `fallback_occurrence`) are fully propagated from the backend adapters to the React UI context. 

**Migrations/rollback**: 
The `tasks` table schema dropped `privacy_mode` in favor of `routing_mode`. As this is an early stage, local SQLite databases were recreated to apply the schema changes without explicit Alembic migrations.

**Known limitations**: 
None.

**Open risks/blockers**: 
None.

**Recommended next task (informational only)**: 
Implement task-level overrides of `RoutingMode` within the task execution lifecycle to support dynamic routing policies per skill.
