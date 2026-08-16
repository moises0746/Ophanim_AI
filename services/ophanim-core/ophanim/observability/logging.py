"""Structured JSONL logging with secret redaction and correlation IDs."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from ophanim.diagnostics.redaction import redact_text

_CORRELATION_ID: ContextVar[str] = ContextVar("ophanim_correlation_id", default="")


def get_correlation_id() -> str:
    """Return the current correlation id (empty when not set)."""
    return _CORRELATION_ID.get()


def set_correlation_id(value: str) -> None:
    """Set the current task/request correlation id for logging."""
    _CORRELATION_ID.set(value)


class JsonlFormatter(logging.Formatter):
    """Emit one JSON object per log record with a stable schema."""

    def __init__(self, *, service_name: str, environment: str) -> None:
        super().__init__()
        self._service_name = service_name
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "service": self._service_name,
            "environment": self._environment,
        }
        if record.exc_info and record.exc_info[1] is not None:
            payload["exception"] = self.formatException(record.exc_info)
        for key in (
            "correlation_id",
            "http_method",
            "path",
            "status_code",
            "duration_ms",
            "action",
            "outcome",
            "tool",
            "skill",
            "classification",
            "component",
            "step",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = redact_text(str(value)) if isinstance(value, str) else value
        return json.dumps(payload, ensure_ascii=True, default=str)


class SecretRedactionFilter(logging.Filter):
    """Redact secret-shaped values from the formatted message."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage() if record.args else str(record.msg)
        if record.args:
            record.msg = message
            record.args = ()
        record.msg = redact_text(record.getMessage())
        for key in ("path", "action", "tool", "step", "component", "detail"):
            value = getattr(record, key, None)
            if isinstance(value, str):
                setattr(record, key, redact_text(value))
        return True


def configure_logging(
    *,
    level: str = "INFO",
    service_name: str = "ophanim-core",
    environment: str = "development",
    log_path: str = "",
) -> None:
    """Configure root logging with structured JSONL output (idempotent).

    Attaches a stderr handler plus an optional rotating file handler when
    ``log_path`` is set. Records are redacted and formatted as JSONL compatible
    with the diagnostics log-search tool.
    """
    root = logging.getLogger()
    if getattr(root, "_ophanim_configured", False):
        return

    parsed_level = getattr(logging, level.strip().upper(), logging.INFO)
    root.setLevel(parsed_level)

    formatter = JsonlFormatter(service_name=service_name, environment=environment)
    redaction_filter = SecretRedactionFilter()

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_path.strip():
        path = Path(log_path.strip())
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        )

    for handler in handlers:
        handler.setLevel(parsed_level)
        handler.setFormatter(formatter)
        handler.addFilter(redaction_filter)
        root.addHandler(handler)

    root._ophanim_configured = True  # type: ignore[attr-defined]
