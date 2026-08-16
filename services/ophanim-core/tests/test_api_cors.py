from fastapi.testclient import TestClient

from ophanim.config import get_settings
from ophanim.main import app


def test_cors_origin_parsing():
    settings = get_settings()
    # By default it should parse the two development URLs
    origins = settings.cors_origin_list
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins


def test_cors_middleware_headers():
    client = TestClient(app)

    # Test valid origin
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Test non-allowed origin
    headers = {
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code == 400  # Starlette returns 400 for bad preflight origin
    # The middleware does not echo back an invalid origin
    assert response.headers.get("access-control-allow-origin") is None
