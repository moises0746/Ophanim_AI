# Ophanim AI

**AI Coworker, Agent Orchestrator, Native AI Browser, and Local-First Assistant Platform**

Ophanim AI is a production-oriented AI coworker platform designed to understand user goals, work with approved knowledge, coordinate specialized AI agents, operate approved web applications through a governed native AI browser, and safely assist with real operational work.

Ophanim is not intended to be a generic chatbot or an unrestricted autonomous agent. AI performs planning, investigation, correlation, summarization, and recommendation. Deterministic tools perform execution. Sensitive actions require explicit approval and every tool action is auditable.

> Product principle: **READ -> ANALYZE -> RECOMMEND -> DRAFT -> APPROVE -> EXECUTE**

---

## Product Vision

Ophanim should feel like a persistent professional coworker rather than a chat window.

The user interacts with an animated and voice-aware **Ophanim Assistant**. Behind that assistant is an orchestrator that delegates work to specialized agents such as Browser, Knowledge, Operations, Developer, Research, Communication, and Content agents.

Ophanim should eventually be able to:

- understand natural-language goals
- recognize the enrolled user and distinguish other speakers
- determine whether speech is directed to Ophanim, the user, or another person
- retrieve approved knowledge from Obsidian, AnythingLLM, documents, runbooks, and policies
- use local models through LM Studio when privacy matters
- use approved cloud models through replaceable provider adapters
- browse and analyze approved web applications through Ophanim Browser
- use APIs and deterministic tools when they are the safer or more reliable integration path
- correlate evidence across portals, logs, source control, tickets, cloud platforms, and documentation
- coordinate specialized AI agents without giving them direct ownership of credentials
- capture screenshots, citations, browser evidence, tool calls, and audit events
- request human approval before production changes, sends, deletes, restarts, retries, approvals, uploads, or other sensitive actions

---

## High-Level Architecture

```text
                           OPHANIM AI

                    Animated AI Assistant
                  Voice | Text | Desktop UI
                            |
                            v
                    Ophanim Orchestrator
        Planning | Context | Policy | Approval | Audit
                            |
           +----------------+----------------+
           |                |                |
           v                v                v
      Agent Registry   Knowledge Layer   Model Router
           |                |                |
   +-------+------+     AnythingLLM       LM Studio
   |       |      |     Obsidian/RAG      Cloud LLMs
   v       v      v
Browser  Ops   Developer
Agent   Agent    Agent
   |
   v
                   Ophanim Native AI Browser
       Chromium + Playwright + DOM + Accessibility + Vision
                            |
             Approved Web Applications / Portals

                            +

        APIs | MCP | GitHub | GitLab | Jira | Confluence
      Microsoft 365 | Google Workspace | AWS | Azure | K8s
```

---

## Core Components

### Ophanim Assistant

The human-facing assistant.

- animated Ophanim avatar
- push-to-talk and optional wake word
- voice activity detection
- speech-to-text
- speaker verification
- text-to-speech
- assistant states such as Idle, Listening, Thinking, Browsing, Investigating, Waiting for Approval, Speaking, Complete, and Error
- desktop overlay and system-tray controls

Animation is driven by deterministic application state events, not directly by an LLM.

### Ophanim Core

The platform control plane.

Recommended initial stack:

- Python 3.12+
- FastAPI
- Pydantic
- asyncio
- PostgreSQL
- Redis
- Celery initially
- OpenTelemetry-ready structured logging

Responsibilities:

- goal intake
- task decomposition
- agent routing
- context management
- policy enforcement
- approval workflow
- tool authorization
- evidence correlation
- audit logging
- provider routing
- workflow state

### Ophanim Agent Mesh

Specialized agents are capability profiles, not independent security principals.

Initial profiles:

- Browser Agent
- Knowledge Agent
- Operations Agent
- Developer Agent
- Research Agent
- Communication Agent
- Content Agent

Agents never own production credentials directly. They request allowlisted capabilities from Ophanim Core.

### Ophanim Knowledge

Initial knowledge stack:

- Obsidian as the human-readable project second brain
- AnythingLLM as the initial RAG/workspace/document layer
- provider-neutral retrieval contracts in Ophanim Core
- future PostgreSQL + pgvector or another approved vector store when needed

AnythingLLM complements Ophanim; it is not the orchestration or security layer.

### Ophanim Local AI

LM Studio is the initial local model runtime.

Use cases:

- local/private inference
- embeddings where appropriate
- OpenAI-compatible model API
- model discovery
- offline-capable workflows after models are available locally

Ophanim must keep model providers replaceable.

### Ophanim Native AI Browser

Ophanim Browser is an AI-native browser product layer built on Chromium rather than a new browser engine.

Execution priority:

```text
1. Official API/SDK when stable and appropriate
2. Deterministic Playwright/DOM automation
3. AI browser reasoning for dynamic or unknown UI
4. Vision-based interaction only as fallback
```

Initial browser capabilities:

- approved-domain navigation
- DOM and accessibility-tree understanding
- read-only page analysis
- structured data extraction
- screenshots and evidence capture
- reusable browser skills
- isolated persistent browser profiles
- explicit approval for state-changing actions

Ophanim Browser must never be used to bypass access controls, CAPTCHA, application restrictions, or authorization boundaries.

---

## Security Model

Security is part of the architecture, not a later hardening task.

Mandatory principles:

- least privilege
- RBAC and capability-based authorization
- explicit tool allowlists
- read-only MVP
- environment separation
- credential vaulting / OS credential store
- no secrets in prompts, logs, Git, or browser artifacts
- isolated browser profiles
- domain allowlists
- human approval for sensitive writes
- immutable or append-only audit records where practical
- evidence provenance
- prompt-injection defenses for retrieved and browser content
- input/output validation for tools
- rollback and verification for future mutation workflows

---

## Repository Structure

```text
Ophanim_AI/
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── .env.example
├── .gitignore
├── docker-compose.dev.yml
├── pyproject.toml
├── package.json
├── pnpm-workspace.yaml
│
├── apps/
│   ├── desktop/                  # Tauri + React + TypeScript
│   └── browser-shell/            # Ophanim Browser UI shell
│
├── services/
│   └── ophanim-core/             # FastAPI orchestration/control plane
│       ├── ophanim/
│       │   ├── api/
│       │   ├── agents/
│       │   ├── approvals/
│       │   ├── audit/
│       │   ├── browser/
│       │   ├── context/
│       │   ├── domain/
│       │   ├── knowledge/
│       │   ├── models/
│       │   ├── policies/
│       │   ├── tools/
│       │   ├── voice/
│       │   └── workflows/
│       └── tests/
│
├── adapters/
│   ├── anythingllm/
│   ├── lmstudio/
│   ├── browser-use/
│   ├── playwright/
│   ├── openai/
│   ├── anthropic/
│   ├── gemini/
│   └── mcp/
│
├── integrations/
│   ├── github/
│   ├── gitlab/
│   ├── jira/
│   ├── confluence/
│   ├── microsoft-365/
│   ├── google-workspace/
│   ├── aws/
│   ├── azure/
│   └── kubernetes/
│
├── packages/
│   ├── contracts/
│   ├── shared-types/
│   ├── prompt-templates/
│   ├── policy-sdk/
│   └── telemetry/
│
├── infrastructure/
│   ├── docker/
│   ├── terraform/
│   ├── kubernetes/
│   └── observability/
│
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── agents/
│   ├── browser/
│   ├── security/
│   ├── infrastructure/
│   ├── development/
│   └── decisions/
│
└── tests/
    ├── architecture/
    ├── integration/
    ├── end-to-end/
    ├── browser/
    ├── security/
    └── performance/
```

Start as a modular monolith. Extract services only when independent scaling, security boundaries, failure isolation, or deployment ownership justify the complexity.

---

## Development Roadmap

### Phase 0 — Foundation and Architecture

Define product scope, architecture, security boundaries, agent model, browser model, UX, data model, APIs, infrastructure, ADRs, acceptance criteria, and test strategy.

### Phase 1 — Local Read-Only Vertical Slice

Deliver a runnable desktop + core environment that can:

1. accept a natural-language task
2. route to a local model through LM Studio
3. retrieve approved knowledge through AnythingLLM
4. open an approved test web application through Ophanim Browser
5. read information without modifying the application
6. capture evidence
7. summarize findings
8. display results and agent activity in the Ophanim Assistant UI

### Phase 2 — Voice and Animated Assistant

- animated state-driven Ophanim avatar
- push-to-talk
- VAD
- faster-whisper transcription
- owner/other/unknown speaker verification
- optional wake word
- private TTS/headset mode

### Phase 3 — Agent Mesh and Professional Memory

- Agent Registry
- capability definitions
- task delegation
- scoped memory
- Obsidian/AnythingLLM project knowledge
- evidence/citation model

### Phase 4 — Enterprise Read-Only Integrations

- GitHub/GitLab
- Jira/Confluence
- Microsoft 365 / Google Workspace
- AWS / Azure
- Kubernetes / Linux
- approved logs and databases

### Phase 5 — Approval-Gated Actions

Introduce deterministic state-changing tools only after policy, approval, verification, rollback, and audit requirements are proven.

---

## MVP Reference Use Case

**AI Transaction Investigation Agent**

```text
Reference Number
      |
      v
Ophanim Task
      |
      +--> Browser Agent -> Approved test portal
      |
      +--> Knowledge Agent -> Runbooks / policy / Obsidian / AnythingLLM
      |
      +--> Log Tool -> Approved logs
      |
      +--> DB Tool -> Approved read-only queries
      |
      v
Evidence Correlation
      |
      v
Issue Classification
      |
      v
Findings + Recommended Next Step
```

No remediation or write action occurs without explicit approval.

---

## Current Status

**Foundation in progress.**

Existing Phase 1 work already includes FastAPI scaffolding, LM Studio and AnythingLLM adapter boundaries, and an initial guarded Browser Use/Playwright browser-agent layer. The current foundation work rebrands and expands that architecture under Ophanim AI.

See the `docs/` directory for the authoritative product, architecture, security, UX, agent, browser, infrastructure, and roadmap documents.
