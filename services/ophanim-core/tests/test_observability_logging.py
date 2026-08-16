"""Tests for structured JSONL logging, redaction, and correlation context."""

from __future__ import annotations

import json
import logging

from ophanim.observability.logging import (
    JsonlFormatter,
    SecretRedactionFilter,
    configure_logging,
    get_correlation_id,
    set_correlation_id,
)


def test_jsonl_formatter_emits_stable_schema() -> None:
    logger = logging.getLogger("ophanim.test.formatter")
    logger.handlers.clear()
    captured: list[dict[str, object]] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(json.loads(self.format(record)))

    handler = CaptureHandler()
    handler.setFormatter(JsonlFormatter(service_name="ophanim-core", environment="test"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        logger.info("hello %s", "world", extra={"correlation_id": "corr-1"})
    finally:
        logger.handlers.clear()

    assert len(captured) == 1
    record = captured[0]
    assert record["msg"] == "hello world"
    assert record["level"] == "INFO"
    assert record["logger"] == "ophanim.test.formatter"
    assert record["service"] == "ophanim-core"
    assert record["environment"] == "test"
    assert record["correlation_id"] == "corr-1"
    assert record["ts"].endswith("Z")


def test_secret_redaction_filter_removes_secret_shapes() -> None:
    logger = logging.getLogger("ophanim.test.redaction")
    logger.handlers.clear()
    captured: list[dict[str, object]] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(json.loads(self.format(record)))

    handler = CaptureHandler()
    handler.setFormatter(JsonlFormatter(service_name="ophanim-core", environment="test"))
    handler.addFilter(SecretRedactionFilter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        logger.info("token %s password=%s", "sk-abcdef1234567890", "hunter2-secret")
    finally:
        logger.handlers.clear()

    assert len(captured) == 1
    message = captured[0]["msg"]
    assert "sk-abcdef1234567890" not in message
    assert "hunter2-secret" not in message
    assert "hunter2" not in message
    assert message.count("[REDACTED]") == 2


def test_correlation_context_roundtrip() -> None:
    assert get_correlation_id() == ""
    set_correlation_id("corr-abc")
    assert get_correlation_id() == "corr-abc"
    set_correlation_id("")
    assert get_correlation_id() == ""


def test_configure_logging_is_idempotent_and_writes_jsonl(tmp_path, monkeypatch) -> None:
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_guard = getattr(root, "_ophanim_configured", False)
    root.handlers.clear()
    monkeypatch.setattr(root, "_ophanim_configured", False)
    log_path = tmp_path / "ophanim.jsonl"
    try:
        configure_logging(
            level="INFO",
            service_name="ophanim-core",
            environment="test",
            log_path=str(log_path),
        )
        handler_count_after_first = len(root.handlers)
        assert handler_count_after_first >= 1

        logging.getLogger("ophanim.test.configure").warning("diagnostic message")

        configure_logging(
            level="INFO",
            service_name="ophanim-core",
            environment="test",
            log_path=str(log_path),
        )
        assert len(root.handlers) == handler_count_after_first

        lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        assert lines
        last = lines[-1]
        assert last["msg"] == "diagnostic message"
        assert last["level"] == "WARNING"
        assert last["logger"] == "ophanim.test.configure"
        assert last["service"] == "ophanim-core"
        assert last["environment"] == "test"
    finally:
        root.handlers.clear()
        root.handlers.extend(original_handlers)
        monkeypatch.setattr(root, "_ophanim_configured", original_guard)
