from typing import Any

import httpx

from nexuvo.config import Settings


class LMStudioClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = str(settings.lmstudio_base_url).rstrip("/")
        self._timeout = settings.request_timeout_seconds
        self._headers: dict[str, str] = {}
        if settings.lmstudio_api_key:
            self._headers["Authorization"] = f"Bearer {settings.lmstudio_api_key}"

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}/models", headers=self._headers)
            response.raise_for_status()
            payload = response.json()
        return payload.get("data", [])

    async def health(self) -> dict[str, Any]:
        try:
            models = await self.list_models()
            return {
                "status": "available",
                "model_count": len(models),
                "models": [model.get("id") for model in models if model.get("id")],
            }
        except httpx.HTTPError as exc:
            return {"status": "unavailable", "error": str(exc)}
