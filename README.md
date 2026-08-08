# Ophanim AI

**A local-first AI coworker platform that can plan, delegate, execute approved work, remember context, and report back.**

Ophanim AI is the product and control plane. LM Studio, Ollama, AnythingLLM, Obsidian, Codex, Claude, and future providers are replaceable capabilities behind stable internal contracts.

The goal is not another chatbot. The goal is a dependable virtual team that can continue bounded work while the owner is away, ask for approval when needed, and leave a complete audit trail.

> Project status: foundation and architecture stage. The current runnable component is `services/nexuvo-core`.

## Product promise

Ophanim AI should let the owner:

- describe an objective in natural language;
- delegate it to one or more specialized AI coworkers;
- use local models for private and routine work;
- use approved cloud models when greater capability is needed;
- retrieve grounded knowledge from AnythingLLM and an Obsidian vault;
- work through APIs, MCP, CLIs, browsers, and desktop applications;
- review sensitive actions before execution;
- receive concise progress, approval, failure, and completion notifications; and
- inspect what every agent saw, decided, changed, and produced.

## Non-negotiable principles

1. **Human authority** — the owner can pause, deny, modify, or stop work at any time.
2. **Local first** — private data and routine inference remain local when practical.
3. **Least privilege** — every agent receives only the tools, data, and time required for its task.
4. **Structured before visual** — prefer APIs and accessible UI controls before screenshot or mouse automation.
5. **Durable work** — jobs survive UI restarts and preserve progress, artifacts, and audit events.
6. **Replaceable providers** — no model runtime, knowledge system, or agent vendor becomes the product boundary.
7. **Evidence over confidence** — important results include sources, verification, and uncertainty.
8. **Safe failure** — uncertain or destructive operations stop for review instead of guessing.

## System architecture

```text
User surfaces
  Desktop app | system tray | chat | notifications | future mobile companion
                                  |
                                  v
                         NEXUVO Core control plane
  API | task service | scheduler | orchestration | policy | approvals | audit
          |                 |                  |                 |
          v                 v                  v                 v
     Model router       Memory service      Tool gateway     Event/notify
      |       |          |          |        |   |   |       |       |
      v       v          v          v        v   v   v       v       v
 LM Studio  Ollama   AnythingLLM  Obsidian  API MCP Desktop  Inbox  Channels
      \       /                            browser/CLI/UIA
       \     /
     optional cloud models and specialist agents
     OpenAI | Anthropic | Codex | Claude | others
```

### Control plane ownership

NEXUVO Core owns:

- task lifecycle and durable execution state;
- agent delegation and budgets;
- provider and capability routing;
- policies, approvals, and emergency stops;
- memory read/write policy;
- tool permissions and credential boundaries;
- audit events, artifacts, verification, and notifications.

Models may propose actions. Only the control plane may authorize tools to execute them.

## Major components

### Desktop application

Planned stack: **Tauri, React, TypeScript, and Vite**.

Primary areas:

- **Home** — priorities, active coworkers, approvals, and system health;
- **Chat** — streaming conversation and visible tool activity;
- **Tasks** — queued, scheduled, active, blocked, and completed work;
- **Memory** — searchable knowledge, sources, and proposed memory updates;
- **Control Center** — models, providers, permissions, privacy, usage, and audit history.

The animated assistant must communicate real state: idle, listening, thinking, delegating, working, waiting for approval, completed, or failed. Desktop control must always display a visible banner and global stop control.

### NEXUVO Core

Current stack: **Python 3.12+, FastAPI, Pydantic, HTTPX, and asyncio**.

The core begins as a modular monolith. Services should be extracted only when scaling, isolation, deployment ownership, or a security boundary justifies it.

### Model router

Applications request capabilities instead of naming a provider directly:

- `fast_chat`
- `deep_reasoning`
- `vision`
- `tool_calling`
- `embedding`
- `code_generation`
- `private_only`

Routing considers privacy mode, model capability, health, latency, VRAM/RAM, queue depth, budget, and owner policy.

Initial providers:

- **LM Studio** — primary local inference and model management;
- **Ollama** — alternate local runtime behind the same contract;
- **AnythingLLM** — initial RAG and document workspace subsystem;
- optional cloud or specialist agents only when policy permits.

Do not load duplicate large models in LM Studio and Ollama by default. A resource manager will later coordinate loading, queueing, and idle eviction.

### Memory and knowledge

**Obsidian is the human-readable source of truth** for preferences, projects, decisions, procedures, notes, and reports.

**AnythingLLM is the retrieval/index layer** for ingestion, embeddings, semantic search, workspace context, and citations.

Chat history is not trusted long-term memory. A memory record must include source, timestamp, scope, confidence, sensitivity, retention/expiry, and writer identity. Agent-created memories are proposals until policy accepts them.

### Virtual team

Start with functional roles instead of many personalities:

| Role | Responsibility |
| --- | --- |
| Chief of Staff | Interpret priorities, decompose objectives, and delegate work. |
| Researcher | Gather, compare, cite, and verify information. |
| Builder | Create code, documents, configurations, and other artifacts. |
| Operator | Run approved API, browser, CLI, and desktop workflows. |
| Librarian | Retrieve knowledge and maintain proposed memory updates. |
| Reviewer | Check accuracy, safety, completeness, and policy compliance. |
| Reporter | Produce progress updates, exception alerts, and digests. |

Every role uses the same task, identity, policy, approval, memory, and audit infrastructure.

## Task lifecycle

Every delegated objective becomes a durable task record with:

- objective, owner, assignee, priority, and deadline;
- inputs, dependencies, allowed tools, and privacy mode;
- token/cost/time/tool-call budgets;
- plan, current step, status, and heartbeat;
- approval requirements and decisions;
- artifacts, evidence, verification, and final summary;
- complete append-only audit events.

Canonical states:

```text
draft -> queued -> planning -> running -> verifying -> completed
                         |          |
                         v          v
              waiting_for_approval  failed
                         |
                         v
                      running

Any active state -> paused | cancelled
```

Workers must be idempotent where practical. A restarted worker must resume from durable state or safely retry a recorded step rather than silently duplicate it.

## Autonomy and approvals

Each task has one autonomy level:

| Level | Meaning |
| --- | --- |
| Observe | Read, inspect, and summarize without changing external state. |
| Prepare | Create drafts, patches, and plans without publishing or applying them. |
| Act with approval | Pause before each consequential action or approved action group. |
| Trusted automation | Execute only a narrowly defined recurring workflow authorized in advance. |

Sensitive operations normally require approval, including external messages, publishing, purchases, deletion, overwriting, software installation, credential entry, production changes, permission changes, private uploads, and destructive source-control operations.

An approval request must show the exact action, destination, affected resources, data leaving the device, risk, expected result, rollback options, and expiration.

## Tool execution order

Use the most structured and reliable interface available:

1. official API or connector;
2. MCP tool;
3. local CLI or SDK;
4. browser DOM automation;
5. operating-system accessibility automation such as Windows UI Automation;
6. screenshot-and-vision interaction;
7. raw mouse coordinates and keyboard simulation.

Desktop execution follows:

```text
observe -> identify target -> propose action -> policy check
        -> execute -> observe again -> verify -> record evidence
```

Raw input is a fallback, not an API replacement. Screen locks, popups, scaling, layout changes, and focus changes make coordinate automation unreliable. Unattended desktop workflows must run in a dedicated, unlocked session with explicit application and action allowlists.

## Notifications

- **Urgent** — security event, blocked high-priority work, or expiring approval.
- **Important** — completion, deadline risk, or repeated failure.
- **Digest** — routine progress and low-priority results.

Start with an in-app inbox and Windows notifications. Add one authenticated remote channel later. Every notification links to its task and audit history.

## Privacy modes

- **Private** — local storage, retrieval, models, and tools only.
- **Hybrid** — sensitive retrieval/preprocessing stays local; specifically approved context may reach a cloud model.
- **Cloud** — configured cloud providers may be used within task and organization policy.

The selected mode and every routing decision must be visible and auditable.

## Repository map

```text
Ophanim_AI/
|-- README.md                     # Product and architecture source of truth
|-- AGENTS.md                     # Instructions for coding agents
|-- CONTRIBUTING.md               # Development workflow
|-- SECURITY.md                   # Security and vulnerability guidance
|-- .env.example                  # Safe configuration template
|-- apps/
|   `-- desktop/                  # Planned Tauri desktop application
|-- services/
|   `-- nexuvo-core/              # Current Python control plane
|       |-- nexuvo/
|       |   |-- adapters/         # Current AnythingLLM/LM Studio boundaries
|       |   `-- browser/          # Current governed browser fallback
|       `-- tests/
|-- packages/                     # Future shared contracts and UI packages
|-- integrations/                 # Future governed tool integrations
|-- docs/
|   |-- architecture/             # Contracts, task model, execution design
|   |-- product/                  # Scope, UX, roles, and milestones
|   |-- security/                 # Threat model and approval policy
|   |-- development/              # Local setup and implementation workflow
|   `-- decisions/                # Architecture decision records (ADRs)
|-- tests/                        # Future cross-component and E2E tests
|-- Obsidian_Vault/               # Local knowledge vault; protect private data
|-- anything-llm-master/          # Vendored upstream; avoid product logic here
`-- ollama-main/                  # Vendored upstream; avoid product logic here
```

Empty future implementation folders are represented by local README files until their phase begins.

## Build order

### Milestone 1 — Dependable control loop

Deliver one complete path:

```text
create task -> select provider -> retrieve context -> propose tool action
-> approve if needed -> execute -> verify -> save evidence -> notify owner
```

Required work:

- task, step, event, artifact, and approval schemas;
- persistent local database and migrations;
- durable queue, scheduler, recovery, and cancellation;
- provider registry and capability router;
- policy engine and append-only audit log;
- streaming task/event API;
- integration and recovery tests.

### Milestone 2 — Desktop control center

- Tauri shell and local authenticated IPC;
- Home, Chat, Tasks, Approvals, Memory, and Settings views;
- streaming responses and task timelines;
- tray operation, notifications, pause, and emergency stop;
- accessible state-driven assistant animation.

### Milestone 3 — Knowledge and memory

- AnythingLLM retrieval with source metadata;
- Obsidian indexing and governed memory writes;
- retention, sensitivity, and provenance controls;
- citations in user-visible answers.

### Milestone 4 — Governed automation

- API/MCP/CLI tool gateway;
- browser authentication and approval workflow;
- Windows UI Automation adapter;
- screenshot/vision fallback;
- application, domain, command, and action allowlists;
- post-action verification and rollback metadata.

### Milestone 5 — Virtual team and unattended work

- role profiles and delegation;
- dependencies, budgets, retries, and timeouts;
- scheduled workflows and daily digest;
- remote notifications and approval links;
- evaluator/reviewer agent and outcome metrics.

Voice coworker features remain an important later vertical slice, but durable tasks and governed execution come first because they are the foundation for safe unattended work.

## Current implementation

Implemented:

- FastAPI core health endpoint;
- LM Studio and AnythingLLM health adapters;
- optional Browser Use integration;
- browser domain allowlists, maximum steps, and write-like approval gating;
- initial unit tests and local setup documentation.

Not yet implemented:

- durable task database, queue, and scheduler;
- approval continuation endpoint and authenticated desktop UI;
- Ollama, Obsidian, desktop UI, UI Automation, or notification adapters;
- multi-agent delegation and unattended execution;
- production credential storage, threat model, and release hardening.

## Development quick start

Prerequisites:

- Python 3.12+
- LM Studio local server, normally at `http://localhost:1234/v1`
- AnythingLLM, normally at `http://localhost:3001`

```powershell
cd services/nexuvo-core
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item ..\..\.env.example .env
uvicorn nexuvo.main:app --reload --host 127.0.0.1 --port 8080
```

Run checks:

```powershell
cd services/nexuvo-core
pytest
ruff check .
```

See [local development setup](docs/development/local-setup.md), [implementation guide](docs/development/implementation-guide.md), and [contribution guidance](CONTRIBUTING.md).

## Definition of done

A feature is complete only when:

- its behavior and boundaries are documented;
- inputs and outputs use typed contracts;
- policy and approval implications are explicit;
- secrets and sensitive content are not logged;
- success, denial, timeout, cancellation, and failure paths are handled;
- tests cover the relevant behavior;
- important actions produce audit events and verification evidence; and
- user-facing state is understandable without reading logs.

## What Ophanim AI is not

Ophanim AI is not:

- a renamed AnythingLLM or Ollama fork;
- a generic chat frontend;
- an always-recording surveillance tool;
- an unrestricted autonomous desktop bot;
- a system that hides where information was sent;
- a collection of agents with separate, inconsistent permission systems.

The product owns the experience, control plane, safety model, memory policy, orchestration, integrations, and evidence trail.

## Documentation index

- [Architecture overview](docs/architecture/overview.md)
- [Task and agent model](docs/architecture/task-and-agent-model.md)
- [Desktop automation](docs/architecture/desktop-automation.md)
- [Product milestones](docs/product/milestones.md)
- [Security model](docs/security/security-model.md)
- [Implementation guide](docs/development/implementation-guide.md)
- [Architecture decisions](docs/decisions/README.md)

## Naming

**Ophanim AI** is the working product name. **NEXUVO Core** is the current internal name of the control-plane service. Before commercial launch, complete trademark, domain, corporate-name, and jurisdiction-specific legal review.
