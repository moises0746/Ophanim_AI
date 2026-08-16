# Ophanim Assistant Desktop Experience

## Scope

`UI-R1-T01` rebuilds the first-party Tauri/React surface as a dense, desktop-first
AI workspace while preserving Ophanim Core as the authoritative control plane.
The visual direction is grounded in the user-provided Ophanim workplace reference:
dark violet operations shell, compact navigation, a central Assistant workspace,
and a contextual activity rail. The private reference image is not copied into the
repository.

## Route map

| Route | Surface | Runtime truth |
|---|---|---|
| `/` | Assistant | Real model list, chat response, SSE state/events, citations, and connection state |
| `/tasks` | Tasks | Explicitly unavailable until durable task state is connected |
| `/projects` | Projects | Explicitly unavailable |
| `/ai-team` | AI Team | Explicitly unavailable; agents are not represented as autonomous processes |
| `/knowledge` | Knowledge | Renders only Core-returned citations and an honest empty state |
| `/automations` | Automations | Workflow editing/execution explicitly unavailable |
| `/browser` | Browser | Explicitly unavailable until governed browser work is implemented |
| `/approvals` | Approvals | Presentation-only approval boundary; no execution claim |
| `/activity` | Activity | Authoritative Core event projection only |
| `/integrations` | Integrations | Explicitly unavailable |
| `/models` | Models & Runtimes | Real configured model inventory and routing metadata |
| `/system-health` | System Health | Real Desktop-to-Core connection and model counts |
| `/settings` | Settings | Explicitly unavailable |

## Component map

- `AppShell`: responsive sidebar, top bar, route search, model/privacy selectors,
  connection summary, and route outlet.
- `AssistantPage`: primary coworker workspace, conversation, suggestions, composer,
  stop request, and truthful knowledge/workflow/runtime overview.
- `OphanimAssistantVisual`: accessible animated presentation of the twelve canonical
  Core Assistant states.
- `ContextPanel`: Activity, Sources, Steps, and Tools tabs backed only by Core data.
- `ConversationPanel`: safe Markdown/GFM presentation; raw HTML is skipped and only
  HTTPS links are made clickable.
- `ModelsPage`, `KnowledgePage`, `ActivityPage`, `ApprovalsPage`, and
  `SystemHealthPage`: real-data operational surfaces.
- `UnavailablePage`: shared, explicit boundary for routes whose product capability
  is not implemented.

## Design tokens

Tokens live in `apps/desktop/src/index.css`. The primary palette is near-black
canvas/sidebar surfaces with violet and indigo interaction color, cyan focus,
restrained gold emphasis, green success, amber approval, and red failure. Shared
tokens cover surface elevation, subtle/strong/gold borders, typography, radii,
sidebar width, and top-bar height. The UI uses local system fonts and the bundled
Ophanim application mark; it has no external font or image dependency.

## Typed contracts and state mapping

The React boundary in `src/types/events.ts` mirrors the provider-neutral runtime
contracts. Model providers are `lm_studio`, `ollama`, `openai`, `gemini`,
`anthropic`, `cloud`, and `mock`; privacy modes are `LOCAL_ONLY`, `PRIVATE`, and
`CLOUD_ASSISTED`. Runtime connectivity is intentionally separate from the canonical
Assistant semantic state.

| Core state | UI label | Visual intent |
|---|---|---|
| `idle` | Ready | calm presence |
| `listening` | Listening | microphone-active pulse |
| `understanding` | Understanding | interpretive orbit |
| `planning` | Planning | measured orbit |
| `delegating` | Delegating | outward coordination |
| `working` | Working | active multi-ring motion |
| `waiting_for_tool` | Waiting for tool | paused tool boundary |
| `waiting_for_approval` | Approval required | amber gated pulse |
| `speaking` | Speaking | audio-state motion |
| `completed` | Completed | green verified rest state |
| `blocked` | Blocked | amber warning state |
| `error` | Error | red failure state |

Each state includes visible text and an accessible status name. Reduced-motion
preferences disable nonessential animation without changing state semantics.

## Responsive and accessibility behavior

- Desktop widths retain the narrow sidebar, centered workspace, and context rail.
- Medium widths stack the context rail and overview cards without horizontal
  overflow.
- Narrow/tablet widths use an off-canvas navigation drawer and compact top bar.
- Keyboard users receive a skip link, focus-visible treatment, working route search
  (`Ctrl+K`), semantic tabs, labeled inputs, and reachable controls.
- Empty, offline, unavailable, approval, error, and reduced-motion states remain
  textually explicit; color or motion is never the only state signal.

## Dependencies

Iconoir provides the icon system; React Router provides the route shell;
React Markdown plus remark-gfm provide bounded message rendering; Testing Library,
axe-core, and Playwright cover component, accessibility, route, responsive, and
rendered-browser checks. Installed packages were reviewed as MIT or Apache-2.0 and
`npm audit` is part of the task verification.
