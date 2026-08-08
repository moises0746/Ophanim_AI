# Ophanim AI Blueprint

## Product Definition

Ophanim AI is a local-first AI coworker and governed agent-orchestration platform. The Assistant is the primary user experience. Specialized agents form a virtual team behind it. Ophanim Core owns task state, orchestration, policy, approvals, tools, evidence, and audit.

Ophanim is not a renamed AnythingLLM fork. AnythingLLM, LM Studio, Ollama, MCP servers, model providers, browser engines, and enterprise systems are replaceable capabilities behind controlled contracts.

## Primary User Experience

The default application route is the Ophanim Assistant, not a dashboard.

```text
User
 ↓
Voice / Text / Desktop UI
 ↓
Animated Ophanim Assistant
 ↓
Ophanim Core Orchestrator
 ↓
Agent Mesh
 ├─ Knowledge Agent
 ├─ Browser Agent
 ├─ Operations Agent
 ├─ Developer Agent
 ├─ Research Agent
 ├─ Communication Agent
 └─ Content Agent
 ↓
Tools / MCP / APIs / Browser / Knowledge / Models
 ↓
Evidence + Result + Approval when needed
```

## Assistant Experience

The animated Ophanim visual is driven by deterministic application events, never direct LLM animation commands.

Assistant states:

- `IDLE`
- `LISTENING`
- `TRANSCRIBING`
- `THINKING`
- `DELEGATING`
- `ORCHESTRATING`
- `RETRIEVING`
- `BROWSING`
- `INVESTIGATING`
- `WAITING_FOR_APPROVAL`
- `SPEAKING`
- `COMPLETE`
- `WARNING`
- `ERROR`
- `PRIVATE_OFFLINE`

The UI must show real agent activity, tool execution, evidence counts, approval needs, and task status.

## Logical Architecture

```text
                           OPHANIM AI

                     Desktop / Assistant UI
                    Tauri + React + TypeScript
                              |
                 Voice / Chat / Agent Activity
                              |
                              v
                         Ophanim Core
              Python 3.12+ / FastAPI / Pydantic
                              |
    +-------------------------+-------------------------+
    |                         |                         |
    v                         v                         v
 Task/Workflow            Policy/Approval           Event Stream
 Orchestration            Audit/Evidence            Assistant State
    |
    v
 Agent Registry + Capability Router
    |
    +----------+-----------+-----------+-----------+
    |          |           |           |           |
    v          v           v           v           v
 Knowledge   Browser     Operations  Developer   Content/etc.
 Agent       Agent       Agent       Agent       Agents
    |          |           |           |
    +----------+-----------+-----------+
               |
               v
         Tool Gateway / Integration Fabric
               |
    +----------+-------------+--------------+----------------+
    |                        |              |                |
    v                        v              v                v
 Official APIs/SDKs         MCP      Deterministic       AI Browser
                                      Browser Skills       Reasoning
                                                           |
                                                           v
                                                        Vision

Knowledge: AnythingLLM + Obsidian
Local inference: LM Studio, optional Ollama
Cloud inference: approved providers through Model Router
Persistence: PostgreSQL
Transient/cache: Redis
Initial jobs: Celery
Future durable orchestration: Temporal
Observability: OpenTelemetry + Prometheus + Grafana
```

## Integration Resolution Order

Ophanim uses the safest reliable integration mechanism available:

1. Official supported API/SDK.
2. MCP tool/resource when it provides a governed standard interface.
3. Approved local SDK/CLI wrapper when deterministic and safely constrained.
4. Deterministic Playwright/DOM browser skill.
5. AI browser reasoning for dynamic/unknown UI workflows.
6. Vision for interfaces without useful structured access.
7. Raw coordinate input only as a last controlled fallback.

MCP is a first-class tool protocol, not a policy bypass. MCP calls still pass through capability authorization, tool allowlists, credential resolution, policy, approval, audit, and evidence capture.

## Agent Mesh

Agents are bounded capability profiles, not independent autonomous services with unrestricted access.

Every agent definition includes:

- identity and version;
- capabilities;
- allowed tools;
- data scopes;
- environment scopes;
- model preferences;
- budgets;
- risk tier;
- approval rules.

Agents never own credentials. The tool gateway resolves secure credential references at execution time.

## Native AI Browser

Ophanim Browser is an AI-native controlled browser layer built on Chromium/Edge and Playwright rather than a new browser engine.

Core capabilities:

- approved-domain registry;
- isolated browser profiles;
- DOM/accessibility-tree inspection;
- deterministic skills;
- controlled AI navigation;
- screenshot/vision fallback;
- session/evidence capture;
- explicit read/write distinction;
- approval boundaries;
- workflow promotion from discovered AI path to deterministic skill after review.

Browser policy:

```text
OBSERVE -> ANALYZE -> PROPOSE -> POLICY -> APPROVE(if needed)
        -> EXECUTE -> VERIFY -> EVIDENCE -> AUDIT
```

Read-only browser investigation is the initial scope.

## Knowledge Architecture

```text
Obsidian Vault
  Human-readable project/operational knowledge
        |
        v
AnythingLLM
  ingestion / embeddings / retrieval / workspaces
        |
        v
Knowledge Adapter
        |
        v
Ophanim Knowledge Agent
```

AnythingLLM is the initial RAG subsystem, not Ophanim's control plane. Ophanim must retain source provenance and citations for grounded results.

## Model Architecture

```text
Capability Request
      |
      v
Model Router
  |       |        |
  v       v        v
LM Studio Ollama  Approved Cloud
```

The product requests capabilities such as reasoning, vision, embedding, coding, or private-only inference. Domain logic must not hard-code a provider.

## Voice Architecture

MVP progression:

```text
Push-to-talk
 -> VAD
 -> speech-to-text
 -> Ophanim intent/context
 -> orchestration
 -> text response
 -> optional TTS
 -> animation state events
```

Later:

- wake word;
- speaker verification;
- addressee detection;
- meeting mode;
- private coaching.

Voice identity is not sufficient authorization for sensitive actions.

## Security Architecture

```text
Goal
 ↓
Plan
 ↓
Capability Request
 ↓
Identity / RBAC
 ↓
Environment Scope
 ↓
Tool Allowlist
 ↓
Policy Evaluation
 ↓
Approval when required
 ↓
Credential Resolution
 ↓
Deterministic Execution
 ↓
Verification
 ↓
Evidence + Audit
```

Non-negotiable controls:

- read-only first;
- no arbitrary SQL;
- no arbitrary shell;
- no unrestricted filesystem;
- no unrestricted browser domains;
- no credentials exposed to models unless strictly required by a bounded tool contract;
- no agent-owned credentials;
- no production changes without explicit authorization;
- append-only audit semantics for consequential actions;
- emergency stop and cancellation checks between steps.

## First Business Vertical Slice

AI Transaction Investigation Agent:

```text
Reference Number
   ↓
Task
   ├─ Browser Agent -> approved test portal
   ├─ DB Read Tool -> approved lookup
   ├─ Log Tool -> approved search
   └─ Knowledge Agent -> MOP/runbook/policy
          ↓
Evidence Correlation
          ↓
Issue Classification
          ↓
Findings + Recommended Next Steps
```

No remediation/write action in the MVP.

## Deployment Strategy

### Local Development

- Ophanim Core native or containerized as practical;
- LM Studio native for GPU access;
- desktop app native;
- browser automation native;
- PostgreSQL/Redis/AnythingLLM via Docker Compose where useful;
- local structured logs and telemetry.

### Enterprise Later

- signed desktop application;
- centralized identity/policy/audit control plane;
- isolated browser/tool workers;
- Kubernetes only after operational need is proven;
- Terraform for infrastructure lifecycle;
- Temporal for durable long-running workflows when Celery limitations become material.

## Product Rule

The Assistant is the product-facing orchestrator. Dashboards, models, agents, browser, knowledge, and integrations support the Assistant rather than replacing it.
