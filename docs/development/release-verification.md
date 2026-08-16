# Release Verification

## Purpose

`scripts/verify_release.ps1` is the deterministic Release 1 verification gate for Ophanim AI. It runs the required core checks plus the extended desktop, node, and secret-scan checks, and prints a per-check PASS/FAIL/SKIP summary with a non-zero exit code on failure.

## Running the gate

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_release.ps1
```

### Required checks (always run)

| Check | Command | Coverage |
| --- | --- | --- |
| Git whitespace | `git diff --check`, `git diff --cached --check` | Trailing/embedded whitespace errors. Benign Windows CRLF notices are reported but do not fail the gate. |
| Ruff lint | `python -m ruff check ophanim tests` | Python lint, including security-relevant rules, for the first-party core package and its tests. |
| Ruff format | `python -m ruff format --check ophanim tests` | Formatting drift detection. |
| Core tests | `python -m pytest tests -q` | Full Ophanim Core unit/integration/API/architecture/security suite. |

### Extended checks

| Check | Command | Coverage | Skip |
| --- | --- | --- | --- |
| Desktop build | `npm run build` (`tsc && vite build`) | TypeScript type errors and production bundle | `-SkipDesktop` / `-CoreOnly` |
| Desktop unit tests | `npm run test` (`vitest run`) | Component/route/accessibility tests | `-SkipDesktop` / `-CoreOnly` |
| Desktop e2e | `npm run test:e2e` (Playwright) | Responsive Assistant shell + core route flow across four viewports | `-SkipDesktop` / `-CoreOnly`, or SKIP when the runtime prerequisite is unmet |
| Rust node | `cargo test` | Protocol, governed-executor, and store tests in `services/ophanim-node` | `-SkipNode` / `-CoreOnly` |
| Secret scan | git-tracked first-party source scan | `sk-…`, `AIza…`, `AKIA…`, PEM private-key blocks. Synthetic canaries in test suites and vendored trees are excluded. | `-SkipSecretScan` / `-CoreOnly` |

`-CoreOnly` runs only the required checks. `-RequireE2E` converts an unmet e2e prerequisite from SKIP into FAIL.

## Desktop e2e prerequisite

The Playwright suite is an integration test that runs the real Desktop shell in a browser and asserts **truthful connected states**: it expects the authenticated core runtime to be reachable, CORS-enabled for the preview origin, and **configured with no models** so the "no models available" empty state is honest.

The gate probes the configured core URL (`VITE_OPHANIM_CORE_URL` if set in the environment, otherwise `apps/desktop/.env.development`) by requesting `/health` with `Origin: http://127.0.0.1:4173` and checking for `Access-Control-Allow-Origin` on the response. If the runtime is not reachable or not CORS-ready, the e2e step is **SKIPped** with the reason (or FAILs under `-RequireE2E`).

### Provisioning a test runtime

Run a local Ophanim Core that matches the Desktop runtime defaults:

```powershell
$env:OPHANIM_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
$env:OPHANIM_DESKTOP_API_TOKEN = "dev-token-123"
$env:OPHANIM_RUNTIME_TENANT_ID = "00000000-0000-0000-0000-000000000001"
$env:OPHANIM_RUNTIME_WORKSPACE_ID = "00000000-0000-0000-0000-000000000002"
$env:PYTHONPATH = "C:\Projects\Ophanim_AI\services\ophanim-core"
python -m uvicorn ophanim.main:app --host 127.0.0.1 --port 8000
```

Start it from a working directory **without** a model-configured `.env` (or with model env vars explicitly cleared), so `GET /api/v1/assistant/models` returns `[]`. The Desktop client pins workspace `00000000-0000-0000-0000-000000000002` and token `dev-token-123`, so the runtime IDs must match for the event-stream authorizer to allow the connection.

Then run the gate (or e2e alone) with the runtime selected:

```powershell
$env:VITE_OPHANIM_CORE_URL = "http://127.0.0.1:8000"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_release.ps1
```

## Exit codes and CI use

- `0` — all checks passed (SKIPs are non-fatal by default).
- `1` — one or more checks failed.

The gate is self-contained PowerShell 5.1 and expects `git`, `python`, `npm.cmd`, and `cargo` on `PATH`. Full-gate runs for Release 1: **10/10 PASS** (2026-08-16), including `npm run build`, `vitest` (18), Playwright e2e (8), `cargo test` (4), and the secret scan.
