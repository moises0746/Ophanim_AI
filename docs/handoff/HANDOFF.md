# Ophanim AI — Current Handoff

Read this after the required root source-of-truth documents. It records current
execution state and does not authorize pending work.

## Project status (2026-08-15)

- main and origin/main remain at 560ebf1.
- R1-12 is preserved in local commit bab5949.
- R1-06A is preserved in local commit d6c031d.
- Active branch: task/r1-run-01-runtime-composition, based on R1-06A.
- R1-RUN-01 is implemented and checkpointed; its changes are uncommitted and unpushed.
- Full validation: 147 Core tests, 12 Desktop tests/build, 2 Tauri Rust tests,
  4 Rust Node tests, Ruff lint/format, npm audit, and Git whitespace checks pass.
- The user deleted the unrelated open-webui tree; it remains absent.

## Done — do not rebuild

- Sprint 00 baseline and ADR-001 through ADR-017.
- R1-01 through R1-11 merged; see the Release 1 tracker.
- R1-12 authenticated default-deny Assistant SSE delivery.
- R1-06A governed OpenAI, Gemini, and Anthropic text-provider adapters.
- R1-RUN-01 authenticated Core chat/model APIs, loopback LM Studio text adapter,
  local runtime composition, Tauri-held ephemeral credential, Desktop chat/model
  controls, sanitized Core event projection, and one-command local launcher.

## Run locally

Configure at least one explicit model ID and any matching credential in the
current process, then run:

~~~powershell
cd apps/desktop
npm.cmd run app:dev
~~~

See docs/development/local-setup.md for LM Studio, OpenAI, Gemini, and Anthropic
examples.

## Pending — not authorized

1. R1-13 — Governed Browser Automation.
2. R1-14 — Diagnostic DB & Log Tools.
3. R1-15 — Transaction Investigation vertical slice.
4. R1-16 — Observability & Packaging.
5. R1-17 — Hardening & Release Gate.

## Runtime limitations

- The environment-backed ephemeral Desktop identity is local-development only;
  production identity and OS credential-store integration remain future work.
- Chat history is process/UI memory only and is not durable.
- Text chat is request/response; provider token streaming is not implemented.
- Emergency stop and explicit chat cancellation are not wired yet.
- Provider models/capabilities must be configured truthfully by the operator.
- Live provider, quota, billing, and production credential tests are opt-in and
  were not executed.

## Guardrails

- Implement one explicitly authorized task at a time and stop after its checkpoint.
- Do not modify vendor trees or Obsidian_Vault without explicit scope.
- Never commit environment files, provider keys, auth state, private notes, or sensitive output.
- Models analyze and recommend; governed deterministic tools alone execute side effects.
- Cloud routing requires explicit STANDARD privacy mode.
