# Ophanim AI — Current Handoff

Read this after the required root source-of-truth documents. It records current execution state and does not authorize pending work.

## Project status (2026-08-15)

- `main` and `origin/main` remain at `560ebf1`.
- R1-12 is preserved in local commit `bab5949` on `task/r1-12-assistant-event-stream`; it is not pushed or merged.
- Active branch: `task/r1-06a-cloud-providers`, based on the R1-12 commit.
- R1-06A is implemented and checkpointed in `docs/checkpoints/R1-06A.md`; its changes are uncommitted and unpushed.
- Full validation: 137 Core tests, 9 Desktop tests/build, 4 Rust Node tests, Ruff lint/format, and `git diff --check` pass.
- The user deleted the unrelated `open-webui/` tree; no follow-up decision remains.

## Done — do not rebuild

- Sprint 00 baseline and ADR-001 through ADR-017.
- R1-01 through R1-11 merged; see `docs/progress/RELEASE-1-STATUS.md`.
- R1-12 authenticated default-deny Assistant SSE delivery and truthful Desktop event projection, locally committed but not merged.
- R1-06A governed OpenAI, Gemini, and Anthropic text-model adapters with runtime secret resolution, privacy enforcement, bounded retries, sanitized health, and contract tests.

## Pending — not authorized

### Recommended next task: R1-RUN-01 — Local Runtime Composition & Desktop Chat Launcher

Complete the real Tauri runtime, compose Core identity/event/model services, add an authenticated Core chat use case, acquire credentials outside UI ownership, instantiate the Desktop event/chat client, and add one-command local startup plus smoke tests.

### Remaining Release 1 roadmap

1. R1-RUN-01 — Local Runtime Composition & Desktop Chat Launcher.
2. R1-13 — Governed Browser Automation.
3. R1-14 — Diagnostic DB & Log Tools.
4. R1-15 — Transaction Investigation vertical slice.
5. R1-16 — Observability & Packaging.
6. R1-17 — Hardening & Release Gate.

## R1-06A continuation notes

- Providers are disabled until an explicit model ID is configured.
- Local development keys are read from allowlisted Core process-environment variables at request time; no value belongs in the Desktop or repository.
- OpenAI, Gemini, and Anthropic adapters support normalized text chat only; see `docs/integrations/cloud-model-providers.md`.
- `LOCAL_ONLY` and `PRIVATE` are denied inside cloud adapters before credentials are resolved.
- R1-RUN-01 is required before the Desktop can submit chat and receive cloud/local responses.

## Guardrails

- Implement one explicitly authorized task at a time and stop after its checkpoint.
- Do not modify vendor trees or `Obsidian_Vault/` without explicit scope.
- Never commit `.env`, provider keys, auth state, private notes, or sensitive output.
- Models analyze and recommend; governed deterministic tools alone execute side effects.
- Cloud routing requires explicit `STANDARD` privacy mode and truthful configured capabilities.
