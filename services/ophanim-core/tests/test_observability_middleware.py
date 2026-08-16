"""Tests for the observability HTTP middleware: correlation IDs, metrics, access logs."""

from __future__ import annotations

import json
import logging
import uuid

from fastapi.testclient import TestClient

from ophanim.main import app
from ophanim.observability.logging import JsonlFormatter, SecretRedactionFilter
from ophanim.observability.metrics import METRICS

_SECRET_TOKEN = "sk-testsecret1234567890"


class JsonlCaptureHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.records: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(json.loads(self.format(record)))


def _attach_access_capture() -> JsonlCaptureHandler:
    logger = logging.getLogger("ophanim.access")
    logger.handlers.clear()
    handler = JsonlCaptureHandler()
    handler.setFormatter(JsonlFormatter(service_name="ophanim-core", environment="test"))
    handler.addFilter(SecretRedactionFilter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return handler


def test_correlation_header_is_echoed() -> None:
    client = TestClient(app)
    correlation_id = str(uuid.uuid4())
    response = client.get("/health", headers={"X-Correlation-Id": correlation_id})
    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == correlation_id


def test_generated_correlation_when_header_missing() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    uuid.UUID(response.headers["x-correlation-id"])


def test_invalid_correlation_is_replaced() -> None:
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-Id": "not-a-uuid"})
    assert response.status_code == 200
    generated = response.headers["x-correlation-id"]
    uuid.UUID(generated)
    assert generated != "not-a-uuid"


def test_requests_are_recorded_in_metrics() -> None:
    METRICS.reset()
    client = TestClient(app)
    try:
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200
        assert client.get("/definitely-not-a-route").status_code == 404

        text = METRICS.render_prometheus_text()
        assert 'ophanim_http_requests_total{method="GET",status_code="200"} 2' in text
        assert 'ophanim_http_requests_total{method="GET",status_code="404"} 1' in text
        assert "ophanim_http_request_duration_seconds_count" in text
    finally:
        METRICS.reset()


def test_access_log_carries_correlation_and_redacts_path() -> None:
    handler = _attach_access_capture()
    client = TestClient(app)
    try:
        response = client.get(f"/{_SECRET_TOKEN}")
        assert response.status_code == 404

        assert len(handler.records) == 1
        record = handler.records[0]
        assert record["http_method"] == "GET"
        assert record["status_code"] == 404
        assert record["correlation_id"]
        assert _SECRET_TOKEN not in record["path"]
        assert "REDACTED" in record["path"]
    finally:
        logging.getLogger("ophanim.access").handlers.clear()
