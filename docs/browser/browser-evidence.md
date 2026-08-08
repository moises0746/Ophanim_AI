# Browser Evidence Contract

## Required Provenance

Browser evidence is a Core Evidence record, not an arbitrary screenshot or model summary. When applicable it references:

- task, step, agent profile/version, capability, ToolCall, policy decision, browser session, and application/version;
- UTC occurred/captured time and current URL/origin/page title;
- action identity and mechanism (DOM, deterministic Playwright skill, AI proposal, vision, or coordinate fallback);
- relevant extracted fields and source locator/DOM/accessibility reference;
- screenshot/artifact reference, content hash where useful, classification, sanitization status, and verification status.

## Evidence Rules

- Capture only the minimum page region/fields needed for the authorized finding.
- Screenshots are classified artifacts; crop/redact sensitive content where practical and never expose cookies, auth headers, secrets, or unrelated private data.
- DOM/source locators are references, not authority; page text and accessibility labels remain untrusted and may contain prompt injection.
- Model summaries are derived inference, not observed fact. Preserve source/provenance and limitations.
- Evidence links respect identity, workspace, environment, data classification, retention, and artifact authorization.
- A screenshot or extraction is not proof of a state-changing result; required verification uses the strongest available deterministic read-back.
- Integrity failure, missing provenance, unknown classification, or unauthorized visibility makes evidence unavailable/quarantined rather than silently trusted.

## Traceability

FR-BROWSER-002, FR-EVIDENCE-001..003, FR-TOOL-003, FR-AUDIT; SEC-004, SEC-007, SEC-008, SEC-011; NFR-PRIV-001..002, NFR-AUDIT-001..002, NFR-OBS-001.
