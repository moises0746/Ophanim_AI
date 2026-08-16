from fastapi.testclient import TestClient

from ophanim.config import Settings, get_settings
from ophanim.main import app


def test_cors_origin_parsing():
    settings = Settings(cors_origins="http://localhost:5173,http://127.0.0.1:5173")
    # Explicitly supplied origins parse into a list
    origins = settings.cors_origin_list
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins


def test_cors_middleware_headers():
    settings = get_settings()
    allowed_origin = settings.cors_origin_list[0]
    client = TestClient(app)

    # Test valid origin from the configured allowlist
    headers = {
        "Origin": allowed_origin,
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin

    # Test non-allowed origin
    headers = {
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/health", headers=headers)
    assert response.status_code == 400  # Starlette returns 400 for bad preflight origin
    # The middleware does not echo back an invalid origin
    assert response.headers.get("access-control-allow-origin") is None
