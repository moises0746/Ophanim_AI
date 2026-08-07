from typing import Any

import httpx

from nexuvo.config import Settings


class AnythingLLMClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = str(settings.anythingllm_base_url).rstrip("/")
        self._timeout = settings.request_timeout_seconds
        self._headers: dict[str, str] = {"Accept": "application/json"}
        if settings.anythingllm_api_key:
            self._headers["Authorization"] = f"Bearer {settings.anythingllm_api_key}"

    async def health(self) -> dict[str, Any]:
        candidates = (
            "/api/ping",
            "/api/v1/system",
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            last_error: str | None = None
            for path in candidates:
                try:
                    response = await client.get(f"{self._base_url}{path}", headers=self._headers)
                    if response.is_success:
                        return {"status": "available", "endpoint": path}
                    last_error = f"HTTP {response.status_code} from {path}"
                except httpx.HTTPError as exc:
                    last_error = str(exc)
        return {"status": "unavailable", "error": last_error or "No health endpoint succeeded"}
