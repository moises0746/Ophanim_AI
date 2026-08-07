# Local Development Setup

## Prerequisites

- Python 3.12+
- AnythingLLM running locally or reachable over HTTP
- LM Studio with its local server enabled

## Run NEXUVO Core

```powershell
cd services/nexuvo-core
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item ../../.env.example .env
uvicorn nexuvo.main:app --reload --host 127.0.0.1 --port 8080
```

Check core health:

```text
GET http://127.0.0.1:8080/health
```

Check provider connectivity:

```text
GET http://127.0.0.1:8080/status/providers
```

Expected behavior:

- `anythingllm.status=available` when the configured AnythingLLM endpoint responds.
- `lmstudio.status=available` when LM Studio responds to its OpenAI-compatible `/models` endpoint.
- A provider being unavailable must not prevent NEXUVO Core itself from starting.

## Configuration

Copy `.env.example` and configure only the values required for your environment.

Do not commit `.env`, API keys, tokens, model credentials, or enterprise integration secrets.
