"""Tests for the dependency-free metrics registry and Prometheus rendering."""

from __future__ import annotations

from ophanim.observability.metrics import (
    METRICS,
    CounterSnapshot,
    HistogramSnapshot,
    MetricsRegistry,
    record_policy_decision,
    record_request,
    record_skill_run,
    record_tool_call,
)


def test_counter_increment_snapshot() -> None:
    registry = MetricsRegistry()
    registry.increment(name="example_total", help="Example counter.", labels={"kind": "a"})
    registry.increment(name="example_total", help="Example counter.", labels={"kind": "a"})
    registry.increment(name="example_total", help="Example counter.", labels={"kind": "b"})

    snapshots = registry.snapshot()
    counter = next(snap for snap in snapshots if isinstance(snap, CounterSnapshot))
    by_label = {
        tuple(sorted(snap.labels.items())): snap
        for snap in snapshots
        if isinstance(snap, CounterSnapshot)
    }
    assert by_label[(("kind", "a"),)].value == 2
    assert by_label[(("kind", "b"),)].value == 1
    assert counter.help == "Example counter."


def test_histogram_observe_cumulative_buckets() -> None:
    registry = MetricsRegistry(histogram_buckets=(0.1, 0.5, 1.0))
    registry.observe(name="example_seconds", help="Example latency.", value=0.05)
    registry.observe(name="example_seconds", help="Example latency.", value=0.2)
    registry.observe(name="example_seconds", help="Example latency.", value=2.0)

    snapshot = next(snap for snap in registry.snapshot() if isinstance(snap, HistogramSnapshot))
    assert snapshot.buckets == (0.1, 0.5, 1.0)
    assert snapshot.counts == (1, 2, 2)
    assert snapshot.count == 3
    assert snapshot.sum == 2.25


def test_render_prometheus_text_shape() -> None:
    registry = MetricsRegistry()
    registry.increment(name="requests_total", help="Requests.", labels={"method": "GET"})
    registry.observe(name="latency_seconds", help="Latency.", value=0.2)

    text = registry.render_prometheus_text()
    assert "# HELP requests_total Requests." in text
    assert "# TYPE requests_total counter" in text
    assert 'requests_total{method="GET"} 1' in text
    assert "# TYPE latency_seconds histogram" in text
    assert 'latency_seconds_bucket{le="0.25"} 1' in text
    assert 'latency_seconds_bucket{le="0.1"} 0' in text
    assert "latency_seconds_sum" in text
    assert "latency_seconds_count" in text


def test_reset_clears_registry() -> None:
    registry = MetricsRegistry()
    registry.increment(name="requests_total", help="Requests.")
    assert registry.snapshot()
    registry.reset()
    assert registry.snapshot() == ()


def test_record_request_helpers_use_global_registry() -> None:
    METRICS.reset()
    try:
        record_request(method="GET", status_code=200, duration_seconds=0.1)
        record_request(method="POST", status_code=500, duration_seconds=0.3)
        record_policy_decision(action="send_message", outcome="approved")
        record_tool_call(tool="anythingllm_embed", outcome="success")
        record_skill_run(
            skill="transaction-investigation", classification="automated", outcome="success"
        )

        text = METRICS.render_prometheus_text()
        assert 'ophanim_http_requests_total{method="GET",status_code="200"} 1' in text
        assert 'ophanim_http_requests_total{method="POST",status_code="500"} 1' in text
        assert "ophanim_http_request_duration_seconds" in text
        assert 'ophanim_policy_decisions_total{action="send_message",outcome="approved"} 1' in text
        assert 'ophanim_tool_calls_total{outcome="success",tool="anythingllm_embed"} 1' in text
        assert (
            'ophanim_skill_runs_total{classification="automated",outcome="success",skill="transaction-investigation"} 1'
            in text
        )
    finally:
        METRICS.reset()
