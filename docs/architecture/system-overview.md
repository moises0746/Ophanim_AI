# Ophanim AI System Architecture

## Architectural Style

Ophanim AI starts as a modular monolith with explicit domain boundaries and replaceable adapters. The system is divided into interaction, orchestration, agent, tool, policy, knowledge, browser, model, persistence, and observability layers.

## Logical Architecture

```text
Desktop / Voice / Browser UI
          |
          v
     API Gateway
          |
          v
   Ophanim Core
  +-------+--------+--------+---------+
  |       |        |        |         |
Planner  Policy  Context  Approval   Audit
  |                                      |
  v                                      v
Agent Registry                      Evidence Store
  |
  +--> Knowledge Agent --> AnythingLLM / Obsidian
  +--> Browser Agent   --> Playwright / Chromium / Vision
  +--> Ops Agent       --> Approved logs / DB / cloud tools
  +--> Developer Agent --> GitHub / GitLab / CI/CD
  +--> Research Agent  --> Approved web/search tools
  +--> Communication   --> Mail/calendar collaboration adapters
  +--> Content Agent   --> Content generation pipelines

Model Router
  +--> LM Studio
  +--> approved cloud providers
```

## Core Boundaries

### Domain
Pure business concepts: Task, Goal, AgentProfile, Capability, ToolDefinition, ToolCall, Approval, Evidence, Investigation, PolicyDecision, BrowserTask, ConversationEvent, AssistantState.

### Application
Use cases and workflows. Application services orchestrate domain objects and ports but do not depend directly on vendor SDKs.

### Adapters
AnythingLLM, LM Studio, Browser Use, Playwright, cloud LLMs, GitHub, Jira, cloud providers, databases, logs, and other external systems.

### Infrastructure
PostgreSQL, Redis, Celery, object/evidence storage, credential provider, telemetry exporters, deployment manifests.

## Tool Resolution Strategy

Ophanim chooses the safest reliable execution mechanism:

1. approved API/SDK tool
2. deterministic DOM/Playwright skill
3. AI browser reasoning
4. vision-based browser action only when structured page access is insufficient

The LLM plans. Deterministic tools execute.

## Deployment Modes

### Local Developer
Desktop UI, Ophanim Core, AnythingLLM, LM Studio, PostgreSQL, Redis, Chromium/Playwright. Docker Compose may run infrastructure services while desktop/GPU-dependent components run natively.

### Enterprise Workstation
Signed desktop app plus local agent. Central policy, identity, audit, and optional model services may be remote.

### Enterprise Platform
Stateless API/control-plane services may move to Kubernetes later. Browser workers and sensitive tool workers remain isolated by workload and environment.

## Non-Negotiable Boundaries

- no arbitrary SQL
- no arbitrary shell
- no unrestricted filesystem
- no unrestricted browser domains
- no credential values passed to models unless strictly required by a tool contract
- no agent-owned credentials
- no production mutation without explicit policy and approval
- every tool invocation has identity, task, capability, input hash, timestamp, result, and audit context
