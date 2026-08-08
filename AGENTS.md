# Coding Agent Instructions

These instructions apply to all first-party work in this repository.

## Source of truth

Read `README.md` before designing a feature. Use the focused documents under `docs/` for task, security, automation, and development constraints. If implementation and documentation disagree, call out the mismatch and update both as part of the same change when authorized.

## Scope boundaries

- Put product logic in `services/nexuvo-core`, `apps`, `packages`, or `integrations`.
- Treat `anything-llm-master` and `ollama-main` as vendored upstream source. Do not modify them unless a task explicitly requires an upstream patch.
- Treat `Obsidian_Vault` as potentially private user data. Do not index, rewrite, publish, or include its contents in fixtures without explicit authorization.
- Never commit `.env`, tokens, cookies, browser profiles, passwords, model credentials, private transcripts, or desktop screenshots containing sensitive data.

## Architecture rules

- Keep NEXUVO Core as the control plane; models propose actions but do not directly bypass policy to invoke tools.
- Place external systems behind typed adapter interfaces.
- Request model capabilities rather than hard-coding a provider in domain logic.
- Prefer a modular monolith until an actual isolation or scaling need justifies a service boundary.
- Persist task state before enabling unattended execution.
- Record policy decisions and consequential tool actions as audit events.
- Prefer APIs, MCP, SDKs, and CLIs over visual automation. Raw mouse and keyboard input is the last fallback.

## Safety rules

- Default new integrations and tools to read-only.
- Treat send, publish, upload, delete, overwrite, install, deploy, purchase, credential, and permission operations as approval-sensitive.
- Validate domains, applications, paths, commands, arguments, and destinations at the tool boundary.
- Keep credentials outside prompts and model-visible tool results whenever possible.
- Make cancellation and emergency stop checks available between agent steps.
- Do not claim a side effect succeeded until it is verified.

## Implementation workflow

1. Identify the milestone and module owning the behavior.
2. Define or update typed contracts before wiring providers.
3. Implement the smallest end-to-end behavior.
4. Add success, failure, denial, timeout, and cancellation tests as relevant.
5. Run the narrowest relevant checks, then the service suite.
6. Update documentation and `.env.example` for any new public behavior or configuration.

## Python conventions

- Target Python 3.12+.
- Use Pydantic models at API and adapter boundaries.
- Keep FastAPI route handlers thin; domain behavior belongs in dedicated modules.
- Use async I/O for providers and tools.
- Add timeouts to external calls.
- Use structured logging; do not log secrets or full sensitive prompts by default.
- Run `pytest` and `ruff check .` from `services/nexuvo-core`.

## Completion standard

Follow the definition of done in `README.md`. Leave the repository in a runnable state and report any unverified behavior explicitly.
