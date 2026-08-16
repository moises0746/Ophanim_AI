"""Secret-aware redaction utilities for diagnostic tool output."""

from __future__ import annotations

import re

_REDACTION_REPLACEMENT = "[REDACTED]"

_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("authorization", re.compile(r"(?i)\bauthorization\b\s*[:=]\s*bearer\s+[^\s,;\"']+")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{20,}")),
    ("api_key", re.compile(r"(?i)\bapi[_-]?key\b\s*[:=]\s*[^\s,;\"']+")),
    ("password", re.compile(r"(?i)\bpassword\b\s*[:=]\s*[^\s,;\"']+")),
    ("secret", re.compile(r"(?i)\bsecret\b\s*[:=]\s*[^\s,;\"']+")),
    ("token", re.compile(r"(?i)\btoken\b\s*[:=]\s*[^\s,;\"']+")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai_sk", re.compile(r"\bsk-[a-z0-9_\-]{16,}", re.IGNORECASE)),
    ("google_ai", re.compile(r"\bAIza[a-z0-9_\-]{20,}", re.IGNORECASE)),
)


def redact_text(value: str) -> str:
    """Replace known secret-shaped substrings with a fixed placeholder."""
    if not value:
        return value
    for _, pattern in _SECRET_PATTERNS:
        value = pattern.sub(_REDACTION_REPLACEMENT, value)
    return value


def redact_value(value: object, *, max_cell_chars: int = 1_000) -> object:
    """Redact secret-shaped scalar values and truncate long strings."""
    if value is None or not isinstance(value, str):
        return value
    if len(value) > max_cell_chars:
        value = f"{value[:max_cell_chars]}...[{len(value) - max_cell_chars} chars truncated]"
    return redact_text(value)


def redact_structure(value: object) -> object:
    """Recursively redact every string leaf in a nested JSON-able structure."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_structure(item) for item in value]
    if isinstance(value, dict):
        return {str(key): redact_structure(item) for key, item in value.items()}
    return value
