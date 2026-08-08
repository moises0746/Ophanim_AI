# Ophanim Native AI Browser

## Goal

Provide a governed AI-native browser capable of analyzing and completing approved web workflows when an API is unavailable, impractical, or insufficient.

## Runtime

- Chromium as default automation runtime
- Microsoft Edge as important enterprise secondary
- Playwright as deterministic browser control layer
- Browser Use or equivalent reasoning adapter for dynamic workflows
- vision fallback for canvas, image-heavy, or structurally inaccessible interfaces

## Execution Strategy

```text
Known stable workflow -> deterministic Playwright skill
Unknown/dynamic workflow -> AI browser planner
No useful DOM/accessibility structure -> vision fallback
```

## Browser Skill Learning

When an AI-discovered workflow becomes stable, promote it into a reviewed deterministic skill rather than rediscovering the steps on every run.

Example:

```text
First run:
AI discovers Transaction -> Search -> Reference -> Details

Reviewed skill:
transaction_portal.search(reference_number)

Future runs:
Use deterministic skill with verification and evidence capture
```

## Security

- disabled until explicitly configured
- approved application/domain registry
- isolated Ophanim browser profiles
- no reuse of unrestricted personal browser profiles
- browser session state treated as credential material
- downloads stored in controlled evidence workspace
- uploads disabled in read-only MVP
- navigation limits and maximum-step budgets
- no CAPTCHA/access-control bypass
- cross-domain navigation denied unless policy allows it
- writes, submissions, approvals, deletes, uploads and authentication changes require approval

## Evidence

Each meaningful step can record:

- task ID
- timestamp
- application and URL
- action type
- sanitized structured extraction
- screenshot reference
- DOM/accessibility evidence reference
- policy decision
- result

## MVP Acceptance Criteria

Given an allowlisted test portal and a transaction reference, Ophanim Browser can navigate to the portal, search/read the transaction, capture evidence, and return structured results without performing any state-changing action.
