Task ID
BOOT-04

Status
COMPLETED (Core-side)

Final Acceptance Status
- Adapter implementation: ACCEPTED
- Real provider inference: BLOCKED BY PROVIDER ACCOUNT/USAGE STATE
- UI end-to-end: BLOCKED BY BOOT-01
Completed at
2026-08-16

Objective
Integrate OpenCode Zen as an eligible CLOUD model provider for Ophanim using the existing routing and provider architecture.

Scope delivered
- Added `OPENCODE_ZEN` provider type to domain model.
- Added OpenCode Zen configuration options to environment Settings.
- Created `OpenCodeZenModelProvider` leveraging the OpenAI-compatible `/chat/completions` schema for API interactions.
- Registered the provider inside the cloud model provider factory.
- Added adapter and router tests specifically verifying OpenCode Zen's integration.

Files changed
- `services/ophanim-core/ophanim/domain/model_routing.py`
- `services/ophanim-core/ophanim/config.py`
- `services/ophanim-core/ophanim/adapters/cloud_model_providers.py`
- `services/ophanim-core/tests/test_cloud_model_providers.py`

Architecture impact
No structural changes. Extends the existing `CloudModelProviderBase` class following the established adapter pattern for Cloud providers. The Hybrid Router logic remains unchanged.

Security impact
The OpenCode Zen API key remains strictly server-side. It is resolved from `Settings` environment configurations via `SecretResolverPort` and sent as a `Bearer` token inside HTTP Authorization headers. It is not exposed to the browser, logs, or routing metadata.

Tests and results
Added tests:
- `test_opencode_zen_adapter_maps_request_and_response`
- Updated `test_router_blocks_configured_cloud_providers_in_local_only_mode`
Results:
- `pytest tests/test_cloud_model_providers.py` (17/17 passed)
- `ruff check .` (0 errors)

Acceptance criteria verification
- "Treat OpenCode Zen as CLOUD": Yes, extended `CloudModelProviderBase` and verified block in `LOCAL_ONLY` mode.
- "API key remains server-side only": Yes, managed via `SecretResolverPort`.
- "Reuse the existing OpenAI-compatible provider adapter": Yes, utilized OpenAI-compatible schema inside `OpenCodeZenModelProvider`.

Migrations/rollback
No database or state migrations required. Rollback simply requires reverting the changes in the four edited files.

Known limitations / Technical Debt
- `context_window=1` is currently used as the repository's unknown sentinel for cloud providers and must never be interpreted as a real one-token context window.
- The `OpenCodeZenModelProvider` adapter duplicates the OpenAI-compatible `/chat/completions` parsing and payload mapping logic.

Open risks/blockers
- Real provider inference cannot be fully claimed until `/chat/completions` returns a real model-generated completion (currently blocked by billing/rate-limit provider state).
- The previously used API credential has been flushed and is treated as compromised because it appeared in local execution logs. Await manual credential rotation.

Recommended next task (informational only)
BOOT-01 - Resume Core/UI Connectivity as the next functional task.
