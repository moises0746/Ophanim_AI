# Ophanim AI — Current Handoff

Read this after the required root source-of-truth documents. It records current execution state and does not authorize pending work.

## Project status (2026-08-15)

- `main` and `origin/main` are at `560ebf1`, where R1-11 was merged through PR #17.
- Active branch: `task/r1-12-assistant-event-stream`.
- R1-12 is implemented and checkpointed in `docs/checkpoints/R1-12.md`; changes are not committed or pushed.
- Full validation: 120 Core tests, 9 Desktop tests/build, 4 Rust Node tests, Ruff lint/format, and `git diff --check` pass.
- `open-webui/` is an unrelated untracked tree and is not part of R1-12.

## Done — do not rebuild

- Sprint 00 baseline and ADR-001 through ADR-015.
- S01-T01 through S01-T05 implementation artifacts and checkpoints, with S01-T03 acceptance caveat retained in Sprint records.
- AAO-001 and ADR-016 deterministic agent orchestration foundation.
- R1-01 through R1-11 merged; see `docs/progress/RELEASE-1-STATUS.md`.
- R1-12 authenticated default-deny SSE delivery, typed Desktop client/projection, truthful live activity/approval presentation, and focused tests.

## Pending — not authorized

### Next eligible task: R1-13 — Governed Browser Automation

Playwright-based read-only browser driver, exact domain allowlist enforcement, and session/evidence capture. Do not start without explicit authorization.

### Remaining Release 1 order

1. R1-13 — Governed Browser Automation.
2. R1-14 — Diagnostic DB & Log Tools.
3. R1-15 — Transaction Investigation vertical slice.
4. R1-16 — Observability & Packaging.
5. R1-17 — Hardening & Release Gate.

## R1-12 continuation notes

- The API's runtime authorizer is intentionally default-deny. Production activation requires an injected R1-05 identity service and a Desktop credential provider outside UI ownership.
- Event fan-out is in-memory and non-replayable; replay/resume and distributed delivery remain deferred.
- No application producer is wired to the broadcaster yet. Future authorized producers inject the port; no public `/emit` route exists.
- The accepted lowercase Core semantic states are explicitly projected to R1-11's uppercase presentation states in the Desktop client.
- Prompt submission, approval decisions, and cancellation are not wired and never claim success locally.

## Guardrails

- Implement one explicitly authorized task at a time and stop after its checkpoint.
- Do not modify `anything-llm/`, `ollama/`, `open-webui/`, or `Obsidian_Vault/` without explicit scope.
- Domain code remains framework/provider independent; all external capabilities use typed ports/adapters.
- No secrets, auth state, private notes, unrestricted SQL/shell/filesystem/browser access, or client-authored authoritative events.
- Consequential actions require policy, approval, deterministic verification, evidence, and audit.

## Open user decision

Decide separately whether the untracked `open-webui/` tree should be governed as vendor source, ignored, or removed. R1-12 does not touch it.
