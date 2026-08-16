"""Tests for the OpenTelemetry bridge: graceful degradation and no-op spans."""

from __future__ import annotations

import builtins
import contextlib

import pytest

from ophanim.config import Settings
from ophanim.observability.otel import init_otel, maybe_start_span, shutdown_otel


def test_init_otel_disabled_returns_false() -> None:
    assert init_otel(Settings(environment="test", otel_enabled=False)) is False
    assert maybe_start_span("nope").__class__ is contextlib.nullcontext


def test_init_otel_graceful_when_sdk_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):
        if name == "opentelemetry" or name.startswith("opentelemetry."):
            raise ImportError("simulated missing OpenTelemetry SDK")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert init_otel(Settings(environment="test", otel_enabled=True)) is False
    assert maybe_start_span("nope").__class__ is contextlib.nullcontext


def test_maybe_start_span_is_noop_before_init() -> None:
    shutdown_otel()
    with maybe_start_span("test") as span:
        assert span is None


def test_init_otel_enabled_path(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("opentelemetry.sdk")
    try:
        initialized = init_otel(Settings(environment="test", otel_enabled=True))
        assert initialized is True
        with maybe_start_span("enabled-span") as span:
            assert span is not None
    finally:
        shutdown_otel()
    assert maybe_start_span("after-shutdown").__class__ is contextlib.nullcontext
