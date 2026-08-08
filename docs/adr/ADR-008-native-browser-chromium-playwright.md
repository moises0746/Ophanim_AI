# ADR-008: Native Browser Uses Chromium/Playwright

Status: Accepted

## Decision

Ophanim Browser is an AI-native controlled browser layer built on Chromium/Edge plus Playwright. Ophanim will not build a new browser engine.

## Consequences

- Chromium is the default automation runtime;
- Edge is a supported enterprise profile target;
- DOM/accessibility automation is preferred over screenshots;
- browser profiles are isolated from normal personal browsing;
- browser skills can be promoted from discovered AI flows to deterministic workflows after review.
