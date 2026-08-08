# Frontend and Desktop Standards

## Scope

Future React/TypeScript/Tauri or equivalent desktop work is deferred. This document reserves ownership and prevents frontend authority from becoming ambiguous.

## Ownership

The desktop client owns presentation, local interaction, accessibility, event reduction, and user-visible errors. It does not own policy, credentials, canonical task/agent/tool state, approvals, evidence authority, or execution. Use typed Core API/event clients and feature-based modules; do not call providers, databases, MCP servers, browsers, or secret stores directly.

## Assistant and Agent Mesh

Use the authoritative pipeline:

```text
Core event -> typed client -> reducer/projection -> canonical Assistant semantic state -> animation state machine
```

Assistant state, Agent Mesh connections/status, progress, evidence counts, approval indicators, and Activity Feed rows derive only from authorized sanitized Core events. UI timers may animate within a state but cannot fabricate events, work, completion, evidence, or approval. Mesh and Feed are projections, never authority.

## Accessibility and Safety

Every semantic state has text, icon/shape, screen-reader, focus, and status-announcement support. Reduced-motion mode preserves state and meaning without animation. Color is never the sole signal. Listening/speaking visuals require real capture/playback state; no frontend timer simulates audio. Stop/interruption controls send a Core cancellation request and cannot claim prevention locally. Hidden chain-of-thought, credentials, auth state, and raw provider internals are never rendered.

## Implementation Quality

Use strict TypeScript types generated or maintained from approved contracts, bounded error/loading/empty states, deterministic component tests, keyboard navigation, high contrast, scalable layout, and sanitized links/artifact access. Do not scaffold React/Tauri, Rive/Lottie, voice, or event transport in S00-T09.
