"""Liveness and readiness health probe routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ophanim.config import Settings, get_settings
from ophanim.observability.readiness import probe_readiness

router = APIRouter(tags=["health"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/health")
async def health(settings: SettingsDep) -> dict[str, str]:
    """Liveness probe: the process is up and serving."""
    return {"status": "ok", "service": settings.service_name}


@router.get("/readyz")
async def readyz(settings: SettingsDep) -> JSONResponse:
    """Readiness probe: aggregate dependency status with truthful detail."""
    report = await probe_readiness(settings)
    status_code = 200 if report.ready else 503
    return JSONResponse(
        content=report.to_dict(),
        status_code=status_code,
    )
