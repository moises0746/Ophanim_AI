# Ophanim Agent Mesh and Agent Registry

## Principle

An Ophanim agent is a bounded capability profile executed through Ophanim Core. It is not an independently privileged autonomous process.

## Initial Agent Profiles

| Agent | Responsibility | Initial access |
| --- | --- | --- |
| Knowledge Agent | Retrieve project/company knowledge | AnythingLLM/Obsidian-derived knowledge, read-only |
| Browser Agent | Navigate approved web apps and capture evidence | Approved domains, read-only |
| Operations Agent | Correlate logs, metrics and DB evidence | Approved read-only tools |
| Developer Agent | Inspect source, PRs and CI evidence | Approved GitHub/GitLab read-only initially |
| Research Agent | Gather/cite approved public information | Approved search/browser tools |
| Communication Agent | Draft communications/schedules | Draft/read initially; send requires approval |
| Content Agent | Research and prepare content workflows | Draft/generate initially |

## Agent Profile Contract

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
environment_scopes:
  - test
risk_tier: low
write_access: false
budgets:
  max_tool_calls: 50
  max_runtime_seconds: 300
```

## Delegation Flow

```text
User Goal
 -> Planner
 -> Required Capabilities
 -> Policy Evaluation
 -> Agent Selection
 -> Tool Calls
 -> Evidence
 -> Correlation/Verification
 -> Response or Approval Request
```

Agents communicate through typed task/result/evidence contracts rather than uncontrolled hidden agent-to-agent conversations.

## Lifecycle

- `READY`
- `PLANNING`
- `WORKING`
- `WAITING`
- `WAITING_FOR_APPROVAL`
- `VERIFYING`
- `COMPLETED`
- `FAILED`
- `CANCELLED`

Lifecycle changes emit AgentActivity events for audit and the live Agent Mesh UI.

## Credentials

Agents never persist or directly receive credential values. Tools receive credential references and resolve them through an approved secret provider at execution time.

## Budgets and Limits

Every delegated task should support bounded:

- runtime;
- tool calls;
- model tokens/cost;
- retries;
- browser steps;
- data scope;
- environment scope.

Exhausting a budget produces a controlled blocked/failed state rather than silently expanding autonomy.

## Agent Registry

The registry stores versioned profiles/capabilities and supports deterministic selection by the orchestrator. Profile changes affecting permissions/risk require review and audit history.
