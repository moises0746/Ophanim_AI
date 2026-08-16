"""Redaction utility tests for diagnostic tool output."""

from __future__ import annotations

from ophanim.diagnostics.redaction import redact_structure, redact_text, redact_value


def test_redact_text_hides_openai_style_keys() -> None:
    assert "sk-abcdefghijklmnop12345" not in redact_text("key=sk-abcdefghijklmnop12345")
    assert "[REDACTED]" in redact_text("key=sk-abcdefghijklmnop12345")


def test_redact_text_hides_google_style_keys() -> None:
    token = "AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    assert token not in redact_text(f"token={token}")


def test_redact_text_hides_bearer_authorization() -> None:
    assert "BEARER abc123" not in redact_text("Authorization: Bearer abc123")


def test_redact_text_hides_key_value_labels() -> None:
    assert redact_text("api_key = 1234567890abcdef").endswith("[REDACTED]")
    assert redact_text("password: hunter2").endswith("[REDACTED]")


def test_redact_value_truncates_long_cells() -> None:
    long_value = "x" * 5_000
    result = redact_value(long_value, max_cell_chars=100)
    assert len(result) < 5_000
    assert "chars truncated" in str(result)


def test_redact_value_leaves_non_strings_untouched() -> None:
    assert redact_value(42) == 42
    assert redact_value(None) is None


def test_redact_structure_recurses() -> None:
    payload = {
        "message": "connect with sk-abcdefghijklmnop12345",
        "items": ["ref", "secret: AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"],
        "count": 3,
    }
    result = redact_structure(payload)
    assert result["count"] == 3
    assert "sk-abcdefghijklmnop12345" not in str(result)
    assert "AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" not in str(result)
