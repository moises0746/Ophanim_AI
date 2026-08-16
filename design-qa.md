# Design QA — UI-R1-T01

## Comparison set

- Source: `C:\Users\moise\OneDrive\Pictures\Ophanim workplace.jfif`
  (user-provided, 2730×1536, not committed).
- Prototype: `docs/screenshots/UI-R1-T01/desktop-1920x1080.png`.
- Additional responsive captures: 1440×900, 1280×720, and 820×1180 under the
  same screenshot directory.
- Compared state: default Assistant workspace with Core unavailable and no
  fabricated task, activity, source, or workflow data.

## Side-by-side findings

The reference and 1920×1080 prototype were placed in one visual comparison input.
The implementation matches the reference's primary composition: fixed compact
left navigation, low-profile global top bar, broad central Assistant workspace,
right contextual rail, near-black violet surfaces, restrained gold selection,
and fine one-pixel separators. The implementation intentionally carries less
content density in its offline default because the reference contains populated
agent/workflow/analytics data that this release cannot truthfully supply.

| Severity | Finding | Resolution |
|---|---|---|
| P1 | The first pass hard-coded a personal name into the shell and screenshots. | Replaced with privacy-neutral `Local operator` and `Welcome back` copy; captures regenerated. |
| P1 | Approval controls could be read as executing an approval even though no write path exists. | Added an explicit presentation-only notice and non-execution button copy. |
| P2 | The first screenshot produced a favicon console error. | Reused the bundled local Ophanim application mark; rendered checks now have no page/console errors. |
| P2 | The reference search shortcut used a macOS glyph in a Windows-targeted build. | Added a functional `Ctrl+K` focus shortcut and corrected the displayed key hint. |
| P2 | Legacy desktop components preserved a competing presentation implementation. | Removed unused legacy visualizer/activity/status/citation components after route migration. |
| P3 | The CSS presence animation is less illustrative than a future authored Rive asset. | Accepted for this release because every canonical state is distinct, semantic, responsive, and reduced-motion safe; a branded animation asset remains a refinement. |
| P3 | Offline empty-state density is lower than the populated reference dashboard. | Accepted to preserve product truth; density should grow only from authoritative Core events and released capabilities. |

## Verification gate

- P0 findings: none.
- P1 findings: resolved.
- P2 findings: resolved.
- Keyboard, reduced-motion, responsive overflow, route navigation, automated
  accessibility, and browser-console checks are covered by the committed suites.

final result: passed
