# AURA Coworker

AURA Coworker is a privacy-first, speaker-aware AI assistant designed to act as a real-time professional coworker.

The initial MVP listens locally, distinguishes the owner from other speakers, detects when a question is directed to the owner, transcribes the conversation, and generates a private suggested response without automatically speaking or sending anything.

> MVP objective: identify **Moises vs. Other Speaker**, detect questions directed to Moises, and generate a useful private response within five seconds.

---

## 1. Product Vision

AURA is not another chatbot.

It is an AI coworker that understands:

- who is speaking
- who is being addressed
- whether the user is asking the AI or speaking to another person
- the current conversation topic
- the safest and most useful response
- when to respond, suggest, or remain silent

Long-term, AURA may integrate with:

- Gmail and Outlook
- Google Calendar and Microsoft 365 Calendar
- Microsoft Teams, Google Meet, Zoom, and Slack
- Jira, Confluence, GitHub, and GitLab
- AWS, Azure, Kubernetes, Linux, Terraform, and Ansible
- screen capture, webcam, mobile, smart glasses, and wearable devices

---

## 2. Core MVP Use Case

### Scenario

A teammate says:

> "Moi, may expected downtime ba during deployment?"

AURA should:

1. detect that the current speaker is not Moises
2. detect that the question is directed to Moises
3. transcribe the question
4. classify the topic and risk
5. generate a private suggested response
6. display the suggestion in a desktop overlay
7. remain silent unless Moises explicitly asks AURA to speak

### Expected Output

```json
{
  "speaker": {
    "identity": "other",
    "confidence": 0.94
  },
  "addressee": "moises",
  "intent": "operational_question",
  "topic": "deployment downtime",
  "requires_response": true,
  "recommended_response": "No downtime is expected based on the approved implementation plan. We will monitor the service during and after the deployment and execute rollback if required.",
  "missing_information": [
    "Confirm final implementation window",
    "Confirm rollback readiness"
  ]
}
```

---

## 3. MVP Scope

### Included

- Windows desktop application
- system tray operation
- microphone capture
- local voice activity detection
- owner voice enrollment
- Moises vs. Other Speaker verification
- speech-to-text transcription
- direct-address detection
- wake-word support
- question and intent detection
- private response recommendation
- confidence scores
- pause and mute controls
- push-to-talk fallback
- local encrypted configuration
- local audit events
- optional cloud LLM provider
- no automatic outbound actions

### Not Included in MVP

- automatic email sending
- automatic Teams or Meet responses
- continuous screen recording
- continuous raw audio storage
- facial recognition
- named identification of all coworkers
- production system changes
- autonomous remediation
- smart glasses integration
- mobile application

---

## 4. Product Principles

### Privacy First

- Raw audio is not stored by default.
- Voice activity detection should run locally.
- Speaker verification should run locally when practical.
- Voice embeddings must be encrypted at rest.
- The user must have a visible listening indicator.
- A global pause or mute control must always be available.
- Sensitive integrations must be read-only by default.
- No message, email, ticket update, or infrastructure action may happen without explicit approval.

### Conservative Automation

AURA should prefer silence over incorrect intervention.

When confidence is low:

```text
Speaker identity uncertain.
Question may be directed to Moises.
Tap to review.
```

### Human-in-the-Loop

AURA may:

- analyze
- summarize
- recommend
- prepare
- draft

AURA must not automatically:

- send
- approve
- deploy
- restart
- delete
- change production resources

unless a future enterprise policy explicitly allows the action.

---

## 5. High-Level Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                     Windows Desktop App                    │
│  System Tray | Status | Overlay | Settings | Voice Enroll │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    Local Desktop Agent                     │
│                                                            │
│  Audio Capture                                             │
│       ↓                                                    │
│  Noise Suppression                                         │
│       ↓                                                    │
│  Voice Activity Detection                                  │
│       ↓                                                    │
│  Speaker Verification                                      │
│       ↓                                                    │
│  Speech-to-Text                                            │
│       ↓                                                    │
│  Addressee + Intent Detection                              │
│       ↓                                                    │
│  Context Orchestrator                                      │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    AI Response Engine                      │
│                                                            │
│  Prompt Guardrails                                         │
│  Conversation Context                                      │
│  Knowledge Retrieval                                       │
│  LLM Provider Adapter                                      │
│  Response Risk Evaluation                                  │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│                   Private Response Overlay                 │
│                                                            │
│  Suggested Answer | Confidence | Missing Facts | Actions  │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Recommended Technology Stack

### Desktop UI

Recommended:

- Tauri
- React
- TypeScript
- Vite

Why Tauri:

- smaller package than Electron
- lower memory usage
- strong desktop integration
- suitable for a continuously running system-tray application

Electron remains a valid fallback when faster JavaScript-only development is more important than resource usage.

### Local Backend

- Python
- FastAPI
- Pydantic
- Uvicorn
- asyncio

### Audio Pipeline

- sounddevice or PyAudio
- WebRTC VAD or Silero VAD
- optional RNNoise for noise suppression
- faster-whisper for local transcription

### Speaker Verification

Recommended first implementation:

- SpeechBrain speaker embeddings

Alternative:

- pyannote.audio

MVP should support only:

```text
Owner: Moises
Other: Any non-owner speaker
Unknown: Insufficient confidence
```

### AI and Reasoning

Use a provider abstraction so AURA is not locked to one model.

Supported adapters may include:

- OpenAI
- Anthropic
- Google Gemini
- local model through Ollama or vLLM

### Storage

MVP:

- SQLite for local configuration, event history, and settings
- encrypted local file or operating-system credential store for secrets

Later:

- PostgreSQL for multi-user and enterprise deployments
- Redis for transient state
- Qdrant or pgvector for long-term knowledge retrieval

### Observability

- structured JSON logs
- OpenTelemetry-ready interfaces
- local log rotation
- optional Prometheus metrics in developer mode

### Packaging

- Tauri bundler for Windows MSI or EXE
- PyInstaller or Nuitka for the Python local agent
- signed release artifacts for production

---

## 7. Repository Structure

```text
aura-coworker/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── .editorconfig
├── .gitignore
├── .env.example
├── docker-compose.dev.yml
├── Makefile
├── pyproject.toml
├── package.json
├── pnpm-workspace.yaml
│
├── apps/
│   ├── desktop/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── features/
│   │   │   │   ├── listening-status/
│   │   │   │   ├── response-overlay/
│   │   │   │   ├── voice-enrollment/
│   │   │   │   ├── transcript-view/
│   │   │   │   └── settings/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── stores/
│   │   │   ├── types/
│   │   │   └── main.tsx
│   │   ├── src-tauri/
│   │   │   ├── src/
│   │   │   ├── capabilities/
│   │   │   └── tauri.conf.json
│   │   ├── tests/
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   └── admin-console/
│       └── README.md
│
├── services/
│   ├── local-agent/
│   │   ├── aura_agent/
│   │   │   ├── main.py
│   │   │   ├── api/
│   │   │   ├── config/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── workers/
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── audio-capture/
│   │   ├── aura_audio/
│   │   │   ├── capture.py
│   │   │   ├── buffer.py
│   │   │   ├── devices.py
│   │   │   └── noise_suppression.py
│   │   └── tests/
│   │
│   ├── voice-activity/
│   │   ├── aura_vad/
│   │   │   ├── engine.py
│   │   │   ├── webrtc_adapter.py
│   │   │   └── silero_adapter.py
│   │   └── tests/
│   │
│   ├── speaker-identity/
│   │   ├── aura_speaker/
│   │   │   ├── enrollment.py
│   │   │   ├── embeddings.py
│   │   │   ├── verification.py
│   │   │   ├── thresholds.py
│   │   │   └── crypto.py
│   │   └── tests/
│   │
│   ├── transcription/
│   │   ├── aura_transcription/
│   │   │   ├── base.py
│   │   │   ├── faster_whisper.py
│   │   │   ├── cloud_provider.py
│   │   │   └── language_detection.py
│   │   └── tests/
│   │
│   ├── conversation-context/
│   │   ├── aura_context/
│   │   │   ├── addressee.py
│   │   │   ├── intent.py
│   │   │   ├── question_detection.py
│   │   │   ├── audience.py
│   │   │   ├── topic.py
│   │   │   └── context_window.py
│   │   └── tests/
│   │
│   ├── response-coach/
│   │   ├── aura_coach/
│   │   │   ├── generator.py
│   │   │   ├── prompts.py
│   │   │   ├── policy.py
│   │   │   ├── risk.py
│   │   │   └── validators.py
│   │   └── tests/
│   │
│   └── knowledge/
│       ├── aura_knowledge/
│       │   ├── retrieval.py
│       │   ├── indexing.py
│       │   ├── sources.py
│       │   └── permissions.py
│       └── tests/
│
├── packages/
│   ├── contracts/
│   │   ├── openapi/
│   │   ├── json-schema/
│   │   └── generated/
│   ├── ui/
│   ├── shared-types/
│   ├── prompt-templates/
│   └── telemetry/
│
├── plugins/
│   ├── aura-speaker/
│   ├── aura-context/
│   ├── aura-coach/
│   ├── aura-mail/
│   ├── aura-calendar/
│   ├── aura-screen/
│   ├── aura-cloudops/
│   └── README.md
│
├── integrations/
│   ├── mcp-server/
│   ├── gmail/
│   ├── microsoft-graph/
│   ├── google-calendar/
│   ├── microsoft-teams/
│   ├── google-meet/
│   ├── jira/
│   ├── confluence/
│   ├── github/
│   ├── gitlab/
│   ├── aws/
│   └── azure/
│
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── README.md
│   ├── docker/
│   ├── kubernetes/
│   └── monitoring/
│
├── docs/
│   ├── architecture/
│   │   ├── system-context.md
│   │   ├── container-diagram.md
│   │   ├── threat-model.md
│   │   ├── data-flow.md
│   │   └── decisions/
│   ├── product/
│   │   ├── product-requirements.md
│   │   ├── personas.md
│   │   ├── roadmap.md
│   │   └── acceptance-criteria.md
│   ├── security/
│   │   ├── privacy-model.md
│   │   ├── data-retention.md
│   │   └── secrets-management.md
│   ├── development/
│   │   ├── local-setup.md
│   │   ├── testing.md
│   │   └── release-process.md
│   └── api/
│
├── scripts/
│   ├── bootstrap.ps1
│   ├── bootstrap.sh
│   ├── run-dev.ps1
│   ├── lint.ps1
│   └── package-windows.ps1
│
└── tests/
    ├── integration/
    ├── end-to-end/
    ├── audio-fixtures/
    ├── performance/
    └── security/
```

---

## 8. Domain Model

### Speaker Identity

```python
from enum import StrEnum
from pydantic import BaseModel, Field


class SpeakerType(StrEnum):
    OWNER = "owner"
    OTHER = "other"
    UNKNOWN = "unknown"


class SpeakerIdentity(BaseModel):
    speaker_type: SpeakerType
    name: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
```

### Conversation Event

```python
from datetime import datetime
from pydantic import BaseModel


class ConversationEvent(BaseModel):
    event_id: str
    timestamp: datetime
    transcript: str
    language: str
    speaker: SpeakerIdentity
    addressee: str | None
    intent: str
    topic: str | None
    requires_response: bool
```

### Response Suggestion

```python
class ResponseSuggestion(BaseModel):
    event_id: str
    recommended_response: str
    rationale: str | None = None
    missing_information: list[str] = []
    risk_level: str
    confidence: float
    should_speak: bool = False
    requires_user_approval: bool = True
```

---

## 9. Decision Engine

AURA must decide whether to respond, suggest, or remain silent.

```text
IF speaker == Moises
AND wake_word_detected == true
AND directed_to == AURA
THEN respond privately or through headset

IF speaker == Other
AND directed_to == Moises
AND question_detected == true
THEN generate private suggested answer

IF speaker == Moises
AND directed_to == Human
THEN stay silent

IF speaker == Other
AND directed_to == Other
THEN stay silent

IF confidence < configured_threshold
THEN do not respond aloud
AND show optional review notification
```

### Suggested Initial Thresholds

```text
Owner verification:
- 0.90 and above: owner
- 0.70 to 0.89: likely owner; require wake word
- below 0.70: unknown

Question-directed confidence:
- 0.85 and above: generate suggestion
- 0.65 to 0.84: show low-confidence prompt
- below 0.65: remain silent
```

These values are starting points only and must be calibrated using real test data.

---

## 10. API Design

### Health

```http
GET /health
```

### Audio Status

```http
GET /api/v1/audio/status
POST /api/v1/audio/start
POST /api/v1/audio/pause
POST /api/v1/audio/resume
POST /api/v1/audio/stop
```

### Voice Enrollment

```http
POST /api/v1/speakers/enroll
GET  /api/v1/speakers/owner
DELETE /api/v1/speakers/owner
```

### Speaker Verification

```http
POST /api/v1/speakers/verify
```

### Conversation Analysis

```http
POST /api/v1/conversations/analyze
```

### Suggestions

```http
GET  /api/v1/suggestions/latest
POST /api/v1/suggestions/{id}/approve
POST /api/v1/suggestions/{id}/dismiss
POST /api/v1/suggestions/{id}/copy
```

### Settings

```http
GET /api/v1/settings
PUT /api/v1/settings
```

---

## 11. Plugin Architecture

Each plugin must follow a standard contract.

```python
from typing import Protocol, Any


class AuraPlugin(Protocol):
    name: str
    version: str

    async def initialize(self, config: dict[str, Any]) -> None:
        ...

    async def health(self) -> dict[str, Any]:
        ...

    async def execute(
        self,
        action: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        ...

    async def shutdown(self) -> None:
        ...
```

### Initial Plugins

#### `aura-speaker`

Responsibilities:

- enroll owner voice
- generate voice embedding
- verify current speaker
- return confidence score
- manage voice profile securely

#### `aura-context`

Responsibilities:

- detect wake word
- detect addressee
- detect question
- classify intent
- identify audience
- maintain short conversation context

#### `aura-coach`

Responsibilities:

- generate suggested response
- identify missing facts
- classify response risk
- adapt tone based on audience
- enforce response policies

---

## 12. Security Design

### Sensitive Data

Treat the following as sensitive:

- voice embeddings
- raw audio
- transcripts
- meeting context
- email content
- calendar content
- company documents
- cloud account data
- API tokens
- access credentials

### Required Controls

- encryption at rest
- TLS for all network calls
- operating-system credential vault for secrets
- explicit consent before audio capture
- visible listening indicator
- configurable transcript retention
- no raw audio retention by default
- user-accessible delete function
- audit event for every connector access
- least-privilege OAuth scopes
- read-only integrations first
- environment separation
- dependency scanning
- signed builds
- secure auto-update mechanism
- secret detection in CI
- software bill of materials for releases

### Threats to Model

- accidental recording
- unauthorized voice enrollment
- replay attack using recorded voice
- speaker spoofing
- prompt injection from spoken content
- prompt injection from emails or documents
- malicious meeting participant
- transcript leakage
- compromised API key
- over-permissioned connector
- model hallucination
- unsafe suggested response
- automatic action without approval

### Anti-Spoofing Roadmap

MVP:

- confidence threshold
- microphone proximity heuristics
- short-lived challenge phrase during enrollment
- no critical action based on voice identity alone

Later:

- liveness detection
- anti-replay model
- device trust
- multimodal identity verification
- hardware-backed credentials

---

## 13. Privacy Modes

### Local Mode

- local transcription
- local speaker verification
- local intent detection when possible
- no external model calls
- limited response quality depending on local model

### Hybrid Mode

- local audio processing
- relevant transcript segments sent to cloud LLM
- no raw audio sent
- recommended default for MVP

### Enterprise Mode

- tenant-managed models and connectors
- centralized policy
- audit logs
- admin controls
- regional data residency
- configurable retention
- private networking where supported

---

## 14. UI Design

### System Tray

States:

```text
Listening
Paused
Muted
Processing
Offline
Error
```

### Main Window

Sections:

- current status
- selected microphone
- voice identity status
- live transcript
- latest detected question
- suggested response
- confidence
- missing information
- event history
- privacy settings

### Private Overlay

```text
┌──────────────────────────────────────────────────┐
│ AURA                                             │
│ Speaker: Other                                   │
│ Directed to: Moises                              │
│ Topic: Deployment downtime                       │
│ Confidence: 94%                                  │
│                                                  │
│ Suggested response:                              │
│ No downtime is expected based on the approved    │
│ implementation plan. We will monitor the service │
│ and execute rollback if required.                │
│                                                  │
│ [Copy] [Speak privately] [Dismiss] [More detail] │
└──────────────────────────────────────────────────┘
```

### Voice Enrollment Screen

The enrollment process should capture:

- normal English
- normal Tagalog
- normal Taglish
- quiet voice
- louder voice
- near microphone
- normal sitting distance

Do not require excessively long enrollment.

---

## 15. Configuration

Example `.env.example`:

```dotenv
AURA_ENV=development
AURA_LOG_LEVEL=INFO

AURA_LOCAL_API_HOST=127.0.0.1
AURA_LOCAL_API_PORT=8765

AURA_DATABASE_URL=sqlite:///./data/aura.db
AURA_DATA_DIR=./data

AURA_TRANSCRIPTION_PROVIDER=faster-whisper
AURA_WHISPER_MODEL=small
AURA_DEFAULT_LANGUAGE=auto

AURA_SPEAKER_PROVIDER=speechbrain
AURA_OWNER_NAME=Moises
AURA_OWNER_THRESHOLD=0.90

AURA_LLM_PROVIDER=openai
AURA_LLM_MODEL=
AURA_LLM_API_KEY=

AURA_WAKE_WORD=AURA
AURA_ENABLE_RAW_AUDIO_STORAGE=false
AURA_TRANSCRIPT_RETENTION_HOURS=24

AURA_TELEMETRY_ENABLED=false
```

Never commit real secrets.

---

## 16. Local Development

### Prerequisites

- Windows 11
- Python 3.12 or later
- Node.js LTS
- pnpm
- Rust toolchain
- Microsoft C++ Build Tools
- FFmpeg
- Git

Verify exact supported versions before implementation and lock them in CI.

### Bootstrap

```powershell
git clone <repository-url>
cd aura-coworker

copy .env.example .env

.\scripts\bootstrap.ps1
```

### Start Local Agent

```powershell
python -m uvicorn aura_agent.main:app `
  --app-dir services/local-agent `
  --host 127.0.0.1 `
  --port 8765 `
  --reload
```

### Start Desktop App

```powershell
pnpm install
pnpm --filter desktop dev
```

### Run Tests

```powershell
python -m pytest
pnpm test
```

---

## 17. Development Standards

### Python

- Ruff
- Black
- mypy
- pytest
- Pydantic models
- dependency injection
- clean architecture
- async-first I/O
- explicit error handling

### TypeScript

- strict mode
- ESLint
- Prettier
- Vitest
- React Testing Library
- typed API client generated from OpenAPI

### Git Workflow

```text
main
develop
feature/*
fix/*
release/*
```

Recommended commit format:

```text
feat(speaker): add owner voice enrollment
fix(vad): prevent duplicate speech segments
docs(architecture): add audio processing flow
test(context): add direct-address scenarios
```

---

## 18. Testing Strategy

### Unit Tests

- VAD segmentation
- speaker threshold logic
- addressee classification
- question detection
- response policy
- risk classification

### Integration Tests

- microphone to transcript
- transcript to identity
- identity to context
- context to response
- UI to local API

### End-to-End Tests

Scenario 1:

```text
Moises: "AURA, what is Azure VPN Gateway?"
Expected: AURA responds.
```

Scenario 2:

```text
Other: "Moi, may downtime ba sa deployment?"
Expected: private suggestion only.
```

Scenario 3:

```text
Moises to teammate: "Paki-check yung logs."
Expected: AURA remains silent.
```

Scenario 4:

```text
Other to another person: "John, check mo nga ito."
Expected: AURA remains silent.
```

Scenario 5:

```text
Unknown noisy speaker.
Expected: low-confidence notification or silence.
```

### Performance Tests

Initial targets:

- VAD detection under 300 ms
- owner verification under 1 second after a speech segment
- transcript first result under 2 seconds when hardware permits
- complete suggestion under 5 seconds
- idle CPU below 10% on a typical developer workstation
- idle memory below 1 GB for the complete desktop stack

Targets must be validated on actual hardware.

---

## 19. Observability

Log events as structured JSON:

```json
{
  "timestamp": "2026-07-11T10:00:00Z",
  "level": "INFO",
  "component": "speaker_identity",
  "event": "speaker_verified",
  "speaker_type": "owner",
  "confidence": 0.94,
  "audio_stored": false
}
```

Do not log:

- raw secrets
- full access tokens
- voice embeddings
- raw audio
- sensitive transcript content unless debug mode is explicitly enabled

---

## 20. CI/CD

Recommended pipeline stages:

```text
validate
lint
type-check
unit-test
integration-test
security-scan
build
package
sign
publish
```

Checks:

- Python dependency audit
- npm dependency audit
- secret scanning
- SAST
- SBOM generation
- license compliance
- artifact signing
- release checksum generation

---

## 21. Roadmap

### Phase 0 — Technical Spike

- microphone capture
- VAD
- local transcription
- console output
- latency measurement

### Phase 1 — Speaker-Aware MVP

- voice enrollment
- Moises vs. Other detection
- wake word
- direct-address detection
- private suggestion overlay
- pause and mute

### Phase 2 — Work Context

- email integration
- calendar integration
- meeting context
- local knowledge files
- approved response templates

### Phase 3 — Screen Awareness

- active application detection
- user-triggered screenshot capture
- OCR
- cloud console recognition
- terminal and editor context

### Phase 4 — Enterprise Integrations

- Teams
- Google Meet
- Jira
- Confluence
- GitHub
- GitLab
- AWS
- Azure

### Phase 5 — Multi-Device

- mobile app
- smart glasses
- wearable audio
- private headset coaching

### Phase 6 — Controlled Actions

- draft email
- create ticket
- generate runbook
- prepare Terraform plan
- request approval
- execute only after explicit authorization

---

## 22. 30-Day MVP Plan

### Week 1

Deliver:

- repository bootstrap
- microphone selection
- audio capture
- VAD
- local transcription
- latency telemetry

Acceptance criteria:

```text
Speech is captured and transcribed reliably.
No raw audio is stored.
```

### Week 2

Deliver:

- voice enrollment
- owner embedding
- Moises vs. Other verification
- confidence calibration
- replay-test fixtures

Acceptance criteria:

```text
Moises is recognized consistently in a quiet room.
Unknown speakers are not incorrectly accepted as Moises.
```

### Week 3

Deliver:

- wake-word detection
- addressee classification
- question detection
- LLM provider abstraction
- suggested response generation

Acceptance criteria:

```text
Questions directed to Moises create a private response suggestion.
Normal conversations do not trigger unnecessary responses.
```

### Week 4

Deliver:

- Tauri desktop UI
- system tray
- private overlay
- pause and mute
- settings
- packaging
- end-to-end demo

Acceptance criteria:

```text
Installable Windows MVP completes the full workflow in under five seconds under normal conditions.
```

---

## 23. Codex Development Instructions

Use the following implementation order.

### Step 1

Create the monorepo structure and initial configuration.

Do not implement every future integration.

Prioritize:

```text
desktop
local-agent
audio-capture
voice-activity
speaker-identity
transcription
conversation-context
response-coach
```

### Step 2

Implement the local FastAPI service with:

- `/health`
- audio start and stop endpoints
- voice enrollment endpoint
- speaker verification endpoint
- conversation analysis endpoint
- latest suggestion endpoint

### Step 3

Implement audio capture and VAD.

Requirements:

- microphone selection
- bounded audio buffer
- asynchronous processing
- no raw audio persistence
- graceful device disconnect handling
- testable interfaces

### Step 4

Implement local transcription using a provider interface.

Requirements:

- language auto-detection
- English, Tagalog, and Taglish support
- partial and final transcripts
- cancellation support
- timeout handling

### Step 5

Implement voice enrollment and speaker verification.

Requirements:

- encrypted owner embedding
- configurable confidence thresholds
- Moises, Other, and Unknown classifications
- no critical action based solely on voice identity
- unit tests with audio fixtures

### Step 6

Implement conversation intelligence.

Requirements:

- wake-word detection
- named-address detection for Moi and Moises
- question detection
- directed-to-AI versus directed-to-human classification
- conservative default behavior
- short context window

### Step 7

Implement the response coach.

Requirements:

- provider-independent LLM interface
- structured JSON response
- missing-information detection
- risk level
- confidence score
- no invented operational facts
- explicit uncertainty
- approval required

### Step 8

Implement the Tauri desktop application.

Requirements:

- status indicator
- microphone selection
- voice enrollment wizard
- transcript panel
- private suggestion overlay
- copy, dismiss, pause, and mute controls
- system tray
- local API health monitoring

### Step 9

Add tests, packaging, and documentation.

Do not consider the MVP complete until:

- tests pass
- secrets are not committed
- the application can be installed on Windows
- microphone permissions are handled
- the app can be paused instantly
- no raw audio is saved by default
- the end-to-end demo works

---

## 24. Definition of Done

The MVP is complete when all of the following are true:

- Moises can enroll his voice.
- AURA can detect Moises versus another speaker.
- AURA can detect when someone says "Moi" or "Moises."
- AURA can detect a question directed to Moises.
- AURA can distinguish a direct AI command from normal human conversation.
- AURA generates a private recommended response.
- AURA does not automatically speak to other people.
- AURA does not automatically send any message.
- AURA can be paused or muted instantly.
- Raw audio is not stored by default.
- The complete response is produced in under five seconds under normal conditions.
- The application is packaged as an installable Windows build.
- Security and privacy behavior is documented.

---

## 25. Future Product Modules

```text
AURA Voice
AURA Coach
AURA Mail
AURA Calendar
AURA Meetings
AURA Screen
AURA Knowledge
AURA CloudOps
AURA Security
AURA Mobile
AURA Glasses
```

The core platform should remain provider-neutral and plugin-based.

---

## 26. Product Positioning

Do not market AURA as:

> AI that listens to everything.

Recommended positioning:

> A private, speaker-aware AI coworker that understands when you need help and gives you the right response at the right time.

Primary target users:

- cloud engineers
- DevOps engineers
- support engineers
- consultants
- technical account managers
- project managers
- sales engineers
- executives
- customer support teams

---

## 27. Important Engineering Note

The hardest part of this product is not speech-to-text or calling an LLM.

The hardest parts are:

- reliable speaker verification
- correct addressee detection
- low false activation rate
- low-latency orchestration
- privacy-preserving operation
- grounded responses
- safe human approval workflows

Optimize for trust before adding more features.
