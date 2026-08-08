# Ophanim AI Blueprint

## Product Definition

Ophanim AI is a local-first AI coworker and agent-orchestration platform. The user interacts primarily through the animated Ophanim Assistant by text or voice. Ophanim decomposes goals, delegates bounded work to specialized agents, invokes governed tools, correlates evidence, and presents findings or approval requests.

## Core Architecture

```text
User
 │
 ├── Text
 ├── Voice
 └── Desktop UI
      │
      ▼
Ophanim Assistant
Animated state + conversation + live activity
      │
      ▼
Ophanim Core
Planner | Context | Policy | Approval | Audit
      │
      ├── Agent Mesh
      │    ├── Browser Agent
      │    ├── Knowledge Agent
      │    ├── Operations Agent
      │    ├── Developer Agent
      │    ├── Research Agent
      │    ├── Communication Agent
      │    └── Content Agent
      │
      ├── Integration Fabric
      │    ├── Native API/SDK
      │    ├── MCP
      │    ├── Deterministic Playwright Skills
      │    ├── AI Browser Reasoning
      │    └── Vision fallback
      │
      ├── Knowledge
      │    ├── AnythingLLM
      │    └── Obsidian-derived sources
      │
      ├── Model Router
      │    ├── LM Studio
      │    └── Approved cloud models
      │
      └── Evidence + Audit
```

## Integration Resolution Order

Ophanim should resolve a requested capability using the safest reliable mechanism available:

1. official API/SDK when stable and appropriate
2. approved MCP server/tool when it provides a governed capability
3. deterministic Playwright/browser skill for known UI workflows
4. AI browser reasoning for dynamic/unknown UI workflows
5. vision-based interaction only when structured browser access is insufficient

MCP is a first-class tool protocol, not an authorization bypass. MCP tools still pass through Ophanim RBAC, policy, approval, audit and secret-resolution layers.

## Assistant Experience

The default route is `/assistant`. Ophanim's animation is driven by deterministic application events.

Primary assistant states:

```text
IDLE
LISTENING
TRANSCRIBING
THINKING
DELEGATING
ORCHESTRATING
RETRIEVING
BROWSING
INVESTIGATING
WAITING_FOR_APPROVAL
SPEAKING
COMPLETE
WARNING
ERROR
PRIVATE_OFFLINE
```

The UI receives AssistantStateEvents through SSE/WebSocket. The LLM never directly commands animation.

## Agent Orchestration

Agents are capability profiles, not independent privileged bots.

```text
Goal
 -> Planner
 -> Capability requirements
 -> Policy check
 -> Agent selection
 -> Deterministic tool calls
 -> Evidence
 -> Correlation
 -> Findings / approval
```

Agent lifecycle:

`READY -> PLANNING -> WORKING -> WAITING -> COMPLETED | FAILED | CANCELLED`

All transitions produce activity events for the Agent Mesh UI and audit trail.

## Native AI Browser

Ophanim Browser is an AI-native execution layer built on Chromium/Playwright rather than a new browser engine.

Capabilities:

- approved-domain navigation
- DOM/accessibility-tree inspection
- structured extraction
- screenshots and evidence
- deterministic browser skills
- AI navigation for unknown workflows
- optional vision fallback
- isolated browser profiles
- approval boundaries for state-changing actions

Modes:

- `OBSERVE`: read/analyze only
- `ASSIST`: prepare/fill, human confirms
- `AUTOMATE`: only pre-approved deterministic workflows; future phase

## Knowledge Architecture

```text
Human-readable knowledge
        │
      Obsidian
        │
        ▼
Knowledge ingestion / indexing
        │
   AnythingLLM
        │
        ▼
Knowledge Agent
        │
        ▼
Ophanim Core
```

AnythingLLM is replaceable and must sit behind a knowledge adapter.

## AI Runtime

LM Studio is the initial local inference runtime. Model providers are behind stable interfaces so cloud or other local providers can be added later.

Privacy modes:

- Private: local models and local knowledge where possible
- Hybrid: sensitive retrieval local, selected approved reasoning remote
- Cloud: configured cloud provider when policy allows

## Security Blueprint

```text
User Goal
 -> Identity / RBAC
 -> Capability Request
 -> Tool Allowlist
 -> Environment Check
 -> Policy Evaluation
 -> Approval if required
 -> Secret resolution inside tool boundary
 -> Deterministic execution
 -> Verification
 -> Evidence + Audit
```

Non-negotiable rules:

- no agent-owned credentials
- no arbitrary SQL
- no arbitrary shell
- no unrestricted filesystem
- no unrestricted browser domains
- no secret disclosure to LLMs unless strictly required by a typed tool contract
- production mutations require human approval
- every tool call and approval decision is auditable

## Initial Infrastructure

Development baseline:

- Python 3.12+
- FastAPI
- PostgreSQL
- Redis
- Celery initially
- React + TypeScript
- Tauri desktop shell
- Playwright + Chromium
- LM Studio
- AnythingLLM
- Docker Compose
- OpenTelemetry-ready structured logging

Future only when justified:

- Temporal
- Terraform
- Kubernetes
- centralized control plane
- distributed browser/tool workers

## First Business Vertical Slice

AI Transaction Investigation Agent:

```text
Reference number
 -> create investigation task
 -> approved test portal via Ophanim Browser
 -> approved read-only database lookup
 -> approved log search
 -> knowledge/runbook retrieval
 -> evidence correlation
 -> issue classification
 -> findings
 -> recommended next steps
```

No remediation/write action is part of the initial MVP.
