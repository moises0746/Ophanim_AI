# UI-R1-T01 Checkpoint — Ophanim Assistant Desktop Experience

## Status

Complete. Recommended next task: R1-13 — Governed Browser Automation
(informational only; not authorized).

## Completed at

2026-08-15

## Objective

Rebuild the first-party Tauri/React UI around the Assistant as the default product
surface, closely following the supplied Ophanim workplace visual direction while
remaining truthful to existing Core contracts and unavailable capabilities.

## Scope delivered

- Added a responsive route shell with requested product and operational navigation.
- Made the Assistant the default route with real chat, model/privacy selection,
  Core event state, activity, citations, stop request, and offline behavior.
- Replaced the legacy visualizer with one accessible presentation system for all
  twelve canonical Assistant states.
- Added Models, Knowledge, Activity, Approvals, and System Health operational views.
- Added explicit unavailable states for Tasks, Projects, AI Team, Automations,
  Browser, Integrations, and Settings rather than fabricating functionality.
- Added safe Markdown message rendering and local application assets/icons.
- Added desktop, compact-desktop, and narrow/tablet responsive behavior.
- Added component, event, runtime, accessibility, route, console, reduced-motion,
  and multi-viewport browser tests with committed screenshots.
- Added the route/component/token/state contract in
  `docs/product/desktop-experience.md` and the visual review in `design-qa.md`.

## Architecture impact

- Preserves React/Tauri -> authenticated Core APIs/events as the only runtime data
  direction; no provider credential or provider SDK enters React.
- Keeps the twelve-state vocabulary identical to the Core event contract and keeps
  runtime connectivity as a separate UI concern.
- Adds no domain, persistence, provider, database, vendor, or private-vault change.
- Unreleased surfaces share one unavailable-state component and make no side-effect
  or capability claim.

## Security and privacy impact

- No secret, token, provider response body, private reference asset, or Obsidian
  content is committed or rendered.
- Removed the user's personal name from static UI and screenshots.
- Markdown skips raw HTML and only permits HTTPS anchors.
- Approval presentation explicitly cannot execute; Core remains authoritative.
- Browser-retrieved content and external integrations are not enabled by this task.

## Acceptance criteria verification

- Supplied visual hierarchy and visual language: satisfied and documented in
  `design-qa.md`.
- Assistant-first route shell and working core navigation: satisfied.
- Twelve canonical, text-backed semantic states: satisfied.
- Real models/runtime/knowledge/activity surfaces: satisfied.
- Truthful unavailable workflow and unreleased routes: satisfied.
- Responsive 1920×1080, 1440×900, 1280×720, and 820×1180 states: satisfied.
- Keyboard, focus, semantic status/tabs, and reduced motion: satisfied.
- No fake activity, analytics, workflow execution, or approval execution: satisfied.

## Tests and results

- Desktop production build: passed (1,967 modules; 416.24 kB JS / 124.61 kB gzip;
  32.07 kB CSS / 7.15 kB gzip).
- Vitest/Testing Library/axe: 13 passed across 3 files.
- Playwright: 8 passed across 1920×1080, 1440×900, 1280×720, and 820×1180.
- Tauri Rust `cargo fmt --check`: passed.
- Tauri Rust `cargo test`: 2 passed.
- `npm audit --audit-level=high`: 0 vulnerabilities.
- `git diff --check`: passed.

## Known limitations

- The state presence uses a lightweight CSS implementation; a future branded Rive
  asset may improve expression without changing the typed state contract.
- Conversation history remains in memory and provider token streaming, voice,
  attachments, and multimodal chat remain outside this task.
- Workflow editing/execution, browser automation, integrations, and settings are
  intentionally unavailable.
- Approval responses remain presentation-only in Desktop.

## Recommended next task

R1-13 — Governed Browser Automation. Informational only; stop and obtain explicit
authorization before implementation.
