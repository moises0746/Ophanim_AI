# Desktop Automation Architecture

## Purpose

Desktop automation exists for applications without an adequate approved API, MCP server, CLI, SDK, or browser interface. It is a governed fallback and not a shortcut around supported integration boundaries.

## Adapter layers

1. **Application APIs and CLIs** — preferred for reliability and verification.
2. **Browser DOM automation** — use element semantics and domain allowlists.
3. **Windows UI Automation** — locate windows and controls by accessible properties and patterns.
4. **Vision grounding** — understand controls unavailable through structured accessibility data.
5. **Raw input** — move/click/type only after a target is grounded and policy allows it.

## Desktop task policy

Every desktop task declares:

- allowed executable/application identities;
- allowed window titles or process IDs where appropriate;
- allowed action categories;
- whether typing, clipboard, file dialogs, authentication, or submission is permitted;
- maximum steps and duration;
- expected starting and ending state;
- approval and verification requirements.

Focus changes, unexpected dialogs, lock-screen state, display-layout changes, or an unknown privileged window stop execution.

## Observation privacy

- Capture the smallest useful window or region instead of the entire desktop.
- Redact known password and sensitive fields before model use when possible.
- Do not retain screenshots by default.
- Evidence screenshots require an explicit retention classification and must avoid unrelated applications.
- Never send desktop imagery to a cloud vision provider unless the task privacy policy explicitly permits it.

## Input safeguards

- Display an always-visible automation indicator.
- Provide a global hotkey and tray control for emergency stop.
- Release held keys and mouse buttons during cancellation and failures.
- Clear sensitive clipboard content immediately after an approved operation.
- Never type a secret by asking a language model to reproduce it; credential insertion must occur in a protected executor.
- Re-observe after every action and verify the intended target before the next one.

## Unattended operation

Unattended desktop work requires a dedicated interactive session that remains available and has no unrelated private applications open. Prefer scheduled API/CLI workflows for work that must continue through screen locks, reboots, or remote-session disconnects.

The first desktop milestone should support one allowlisted application and one reversible workflow before generalizing the adapter.
