# R1-RUN-01 Checkpoint — Local Runtime Composition & Desktop Chat Launcher

## Status

Complete. Recommended next task: R1-13 — Governed Browser Automation
(informational only; not authorized).

## Completed at

2026-08-15

## Objective

Make the first-party Desktop Assistant runnable against authenticated Ophanim
Core chat and event services, with governed local/cloud model routing and no
provider or Core credential ownership in React.

## Scope delivered

- Added authenticated POST /api/v1/assistant/chat and
  GET /api/v1/assistant/models delivery boundaries.
- Added the Assistant chat application service with workspace/scope checks,
  model routing, sanitized state events, cancellation propagation, and stable
  dependency errors.
- Added explicit provider/model preferences to the provider-neutral routing contract.
- Added a loopback-only OpenAI-compatible LM Studio text provider with bounded
  messages, input, output, timeout, response normalization, and sanitized errors.
- Composed LM Studio and configured OpenAI/Gemini/Anthropic providers behind the
  existing Model Router.
- Added a fail-closed local runtime identity that resolves an ephemeral launcher
  credential at authentication time.
- Replaced the placeholder Rust executable with a real Tauri 1 runtime exposing
  only fixed model/chat/event commands. Rust owns the Core bearer credential and
  restricts Core URLs to loopback.
- Added Desktop model/privacy selection, real conversation rendering, and
  Tauri-forwarded Core SSE projection through the existing typed reducer.
- Added a one-command PowerShell launcher that starts Core, waits for health,
  starts Tauri, and cleans up only its own Core child process.
- Added deterministic application icons and upgraded Vite/Vitest to
  advisory-fixed versions.

## Files changed

- Core domain/application/ports/adapters/API/runtime composition under
  services/ophanim-core/ophanim
- services/ophanim-core/tests/test_assistant_chat_api.py
- Desktop React types/services/components/tests under apps/desktop/src
- Tauri Rust runtime, configuration, lockfile, and icons under apps/desktop/src-tauri
- apps/desktop/scripts/run-local.ps1
- apps/desktop/package.json and package-lock.json
- .env.example and project setup/status/handoff documentation

## Architecture impact

- Preserves Desktop -> authenticated Core API/application -> ModelRouterPort
  <- provider adapters.
- Core remains authoritative for identity scope, routing, provider execution,
  and Assistant events.
- React receives neither the Core session credential nor provider credentials.
- Tauri exposes bounded commands rather than a generic HTTP proxy.
- Model output is returned as chat content and gains no tool or side-effect authority.
- No database migration or vendor/private-tree change was introduced.

## Security impact

- The launcher credential is cryptographically random, process-local, and not
  persisted or displayed.
- Runtime identity fails closed unless tenant, workspace, and token are all
  available; comparison is constant-time and values rotate without restart.
- Chat and model APIs require Bearer authentication, exact workspace scope, and
  dedicated scopes.
- Tauri accepts only loopback Core URLs and fixed API paths.
- Cloud privacy isolation remains enforced by both the router and cloud adapters.
- Chat prompts and responses never enter Assistant event payloads.
- Provider response bodies, credentials, and internal failures are not reflected
  to Desktop errors.
- npm audit reports zero known JavaScript dependency vulnerabilities.

## Tests and results

- Focused Core runtime/provider/event tests: 37 passed.
- Full Core pytest: 147 passed, one upstream Starlette/httpx warning.
- Ruff check/format: passed across 91 Python files.
- Desktop production build: passed.
- Desktop Vitest: 12 passed across 3 files.
- Tauri Rust cargo fmt --check and cargo test: 2 passed.
- Optimized Tauri release build: passed.
- Rust Node cargo test: 4 passed.
- npm audit: 0 vulnerabilities.
- Launcher PowerShell parser check: passed.
- git diff --check: passed.

## Acceptance criteria verification

- Authenticated Desktop-to-Core text chat: satisfied.
- Configured LM Studio/OpenAI/Gemini/Anthropic routing: satisfied.
- Explicit provider/model and privacy selection: satisfied.
- Credentials remain outside React/model/event ownership: satisfied.
- Authoritative real-time state projection during chat: satisfied.
- Missing/invalid/cross-workspace authorization fails closed: satisfied.
- Local provider cannot send prompts to a non-loopback endpoint: satisfied.
- One-command local Core + Tauri development launch: satisfied.
- Success, denial, provider failure, rotation, redaction, and dependency checks:
  satisfied.

## Migrations/rollback

No database migration. Rollback removes the chat/runtime modules and tests,
Tauri HTTP/event bridge and dependencies, icons, launcher, and Desktop
conversation/routing controls. R1-12 and R1-06A remain separately preserved in
commits bab5949 and d6c031d.

## Known limitations

- Local runtime identity uses process-environment custody and is not the
  production identity/OS credential-store solution.
- Conversation history is not durable and is bounded to 40 in-memory messages.
- Provider token streaming, tool-role messages, voice, attachments, and
  multimodal chat are not implemented.
- Emergency stop and explicit in-flight chat cancellation APIs remain deferred.
- No live provider, quota, cost, billing, or production credential test ran.
- Tauri signed packaging and installer release work remain deferred.

## Open risks/blockers

No blocker within R1-RUN-01. Production rollout still requires durable identity,
approved OS/encrypted credential custody, packaging/signing, and hardening.

## Recommended next task

R1-13 — Governed Browser Automation. Informational only; stop and obtain explicit
authorization before implementation.
