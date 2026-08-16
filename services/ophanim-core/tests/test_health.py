from fastapi.testclient import TestClient

from ophanim.main import app
from ophanim.observability.metrics import METRICS


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ophanim-core"}


def test_metrics_endpoint_renders_registry() -> None:
    METRICS.reset()
    client = TestClient(app)
    try:
        client.get("/health")
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert 'ophanim_http_requests_total{method="GET",status_code="200"}' in response.text
        assert "ophanim_http_request_duration_seconds_count" in response.text
    finally:
        METRICS.reset()
