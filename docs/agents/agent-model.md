# Ophanim AI Agent Model

## Principle

An Ophanim agent is a bounded capability profile executed by Ophanim Core. It is not an autonomous process with unrestricted credentials or tools.

## Initial Agent Profiles

| Agent | Primary responsibility | Initial access |
|---|---|---|
| Browser Agent | Navigate, inspect, extract, capture evidence | Approved browser domains, read-only |
| Knowledge Agent | Retrieve runbooks, policies, project context | AnythingLLM, Obsidian-derived knowledge, read-only |
| Operations Agent | Correlate approved logs, metrics, DB evidence | Approved read-only tools |
| Developer Agent | Inspect repositories, PRs, CI evidence | GitHub/GitLab read-only initially |
| Research Agent | Public/approved research | Approved search/browser tools |
| Communication Agent | Prepare communication and schedules | Draft/read initially; send requires approval |
| Content Agent | Research and prepare content workflows | Draft/generate only initially |

## Agent Registry

Each profile defines:

```yaml
id: browser-agent
name: Browser Agent
version: 1.0.0
capabilities:
  - browser.navigate
  - browser.read
  - browser.extract
  - evidence.capture
allowed_tools:
  - ophanim-browser
risk_tier: low
write_access: false
```

## Delegation

```text
User Goal
   -> Planner
   -> Required capabilities
   -> Policy evaluation
   -> Agent selection
   -> Tool calls
   -> Evidence
   -> Correlation
   -> Response / approval request
```

Agents communicate through typed task/evidence contracts, not free-form hidden agent-to-agent conversations.

## Lifecycle States

`READY`, `PLANNING`, `WORKING`, `WAITING`, `WAITING_FOR_APPROVAL`, `COMPLETED`, `FAILED`, `CANCELLED`.

These states feed both audit logging and the animated Assistant/Agent Mesh UI.

## Credential Rule

Agents never receive or persist credentials directly. Tools resolve credential references at execution time through approved secret providers.
