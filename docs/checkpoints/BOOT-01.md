Task ID: BOOT-01
Status: Complete
Completed at: 2026-08-16
Objective: Fix Core Unavailable and Tauri IPC Errors by implementing an HTTP client fallback for browser execution while preserving Tauri transport for desktop.
Scope delivered: 
- Implemented `CORSMiddleware` in FastAPI with an explicit whitelist.
- Configured frontend environments (`.env.development`) with `VITE_OPHANIM_CORE_URL`.
- Implemented `HttpAssistantRuntimeClient` and dynamic runtime client resolution.
- Added tests for runtime resolution, HTTP client mapping, and CORS configuration.
Files changed:
- `services/ophanim-core/ophanim/config.py`
- `services/ophanim-core/ophanim/main.py`
- `services/ophanim-core/tests/test_api_cors.py`
- `apps/desktop/.env.development`
- `apps/desktop/src/services/runtime.ts`
- `apps/desktop/src/main.tsx`
- `apps/desktop/src/__tests__/runtime.test.ts`
Architecture impact:
- Frontend now supports standard browser runtime without Tauri dependencies.
- Backend now accepts CORS from explicitly configured origins, maintaining security.
Security impact:
- Retained strict CORS policies using an explicit allowlist (avoiding wildcard `*`).
Tests and results:
- Passed Python unit tests (pytest) and static analysis (ruff).
- Passed frontend unit tests (vitest).
Acceptance criteria verification:
- Assistant frontend can operate as a standard web application while communicating with the backend over HTTP.
Migrations/rollback:
- No database migrations required. Can be rolled back by reverting changes.
Known limitations:
- Hardcoded fallback to `http://localhost:8000` is currently managed via env var, assumes local setup.
Open risks/blockers:
- None.
Recommended next task (informational only): BOOT-02 — Knowledge End-to-End
