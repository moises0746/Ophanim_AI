# Ophanim Native AI Browser

This document is the concise entry point. The authoritative S00-T08 contracts are [Browser Execution Contract](browser-execution-contract.md), [Approved Application Registry](approved-application-registry.md), [Browser Action Model](browser-action-model.md), [Browser Evidence](browser-evidence.md), and [Browser Security](browser-security.md). No browser runtime is implemented by this specification.

## Goal

Provide a governed browser execution environment for approved web applications when APIs/MCP are unavailable, incomplete, or uneconomical to integrate.

## Technology

- Chromium as default automation runtime;
- Microsoft Edge as first-class enterprise profile option;
- Playwright for deterministic browser control;
- AI reasoning for dynamic/unknown UI workflows;
- vision only when DOM/accessibility information is insufficient.

Ophanim does not build a new rendering/browser engine.

## Execution Layers

```text
Known deterministic skill
        ↓
Playwright/DOM
        ↓
AI browser planner when needed
        ↓
Vision fallback
        ↓
Raw coordinate fallback only when explicitly approved
```

## Browser Profiles

Use dedicated Ophanim profiles rather than the user's normal browser profile.

Example logical profiles:

- `automation` — isolated Chromium;
- `microsoft-enterprise` — Edge for approved enterprise/SSO applications;
- `research` — approved public browsing;
- `test-portal` — dedicated non-production application session.

Session cookies/auth state are secrets and must never be committed.

## Application Registry

Each approved application defines domains, environments, available actions and approval policy.

```yaml
id: transaction-test-portal
domains:
  - portal.test.example.com
environments:
  - test
browser_profile: automation
actions:
  read:
    - search_transaction
    - view_transaction
    - capture_evidence
  write: []
```

## Action Classes

- READ
- NAVIGATE
- INPUT
- DOWNLOAD
- UPLOAD
- AUTH
- WRITE

MVP allows only explicitly approved read/navigation actions. Input may be allowed for search/filter fields when it does not mutate server state; this must be classified by the application skill, not guessed generically.

## Evidence

Each meaningful browser step may record:

- task/tool call ID;
- application and environment;
- URL/origin;
- action type;
- extracted structured data;
- DOM/accessibility evidence reference;
- screenshot reference when useful;
- timestamp;
- result/verification;
- model decision metadata where AI navigation was used.

Do not capture/store unnecessary sensitive content.

## Skill Promotion

```text
Unknown workflow
 -> AI-guided discovery
 -> successful verified execution
 -> evidence/review
 -> deterministic Playwright skill
 -> regression tests
```

The AI should not rediscover stable workflows on every run.

## Security

- browser disabled unless configured;
- explicit domain/application allowlists;
- environment separation;
- no bypass of CAPTCHA/access controls/service restrictions;
- no unrestricted downloads/uploads;
- no arbitrary script execution exposed to agents;
- approval required before state-changing actions;
- persistent auth state encrypted/protected;
- emergency stop available between steps;
- prompt injection from web content treated as untrusted input.

Browser execution is subordinate to Ophanim Core policy and the integration preference order. Browser, Browser Agent, Playwright, AI reasoning, vision, and coordinate projections never become policy authority or credential owners.

## MVP Browser Acceptance

Given an approved test portal and reference number, Ophanim can navigate/search/read transaction information, capture evidence and return structured findings without changing external state.

## Legacy Disposition

The existing optional `BrowserUseAgent` and `/browser/tasks` endpoint are preserved experimental behavior, not this target contract. Their reusable ideas are bounded objectives, configured domain allowlists, max-step limits, optional dependency handling, and browser cleanup. They conflict with the target in their lack of a first-party application registry, typed DOM-first action model, dedicated profile/session contract, full navigation/popup/download/clipboard controls, Core event/evidence integration, cancellation reconciliation, and complete read-only state-changing detection. A later task must wrap or replace them behind these contracts; S00-T08 does not modify or expand them.
