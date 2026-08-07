from fastapi import FastAPI

from nexuvo.adapters.anythingllm import AnythingLLMClient
from nexuvo.adapters.lmstudio import LMStudioClient
from nexuvo.config import get_settings

app = FastAPI(title="NEXUVO Core", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexuvo-core"}


@app.get("/status/providers")
async def provider_status() -> dict[str, object]:
    settings = get_settings()
    anythingllm = AnythingLLMClient(settings)
    lmstudio = LMStudioClient(settings)

    return {
        "anythingllm": await anythingllm.health(),
        "lmstudio": await lmstudio.health(),
    }
