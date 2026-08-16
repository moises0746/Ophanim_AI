"""Dependency-free in-process metrics registry with Prometheus text rendering."""

from __future__ import annotations

import threading
from collections.abc import Mapping
from dataclasses import dataclass

_DEFAULT_HISTOGRAM_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)

_ESCAPE_TRANSLATION = {
    "\\": "\\\\",
    "\n": "\\n",
    '"': '\\"',
}


def _escape(value: str) -> str:
    return "".join(_ESCAPE_TRANSLATION.get(char, char) for char in value)


@dataclass(frozen=True, slots=True)
class CounterSnapshot:
    name: str
    help: str
    labels: Mapping[str, str]
    value: int


@dataclass(frozen=True, slots=True)
class HistogramSnapshot:
    name: str
    help: str
    labels: Mapping[str, str]
    buckets: tuple[float, ...]
    counts: tuple[int, ...]
    sum: float
    count: int


def _label_key(labels: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(key), str(value)) for key, value in labels.items()))


def _labels_text(labels: Mapping[str, str]) -> str:
    if not labels:
        return ""
    inner = ",".join(f'{key}="{_escape(str(value))}"' for key, value in sorted(labels.items()))
    return f"{{{inner}}}"


class MetricsRegistry:
    """Thread-safe counters and histograms keyed by (metric name, labels)."""

    def __init__(
        self, *, histogram_buckets: tuple[float, ...] = _DEFAULT_HISTOGRAM_BUCKETS
    ) -> None:
        self._lock = threading.RLock()
        self._buckets = tuple(histogram_buckets)
        self._counters: dict[
            tuple[str, tuple[tuple[str, str], ...]],
            tuple[str, dict[str, str], int],
        ] = {}
        self._histograms: dict[
            tuple[str, tuple[tuple[str, str], ...]],
            tuple[str, dict[str, str], tuple[int, ...], float, int],
        ] = {}

    def increment(self, *, name: str, help: str, labels: Mapping[str, str] | None = None) -> None:
        label_map = dict(labels or {})
        key = (name, _label_key(label_map))
        with self._lock:
            current = self._counters.get(key)
            if current is None:
                self._counters[key] = (help, label_map, 1)
            else:
                self._counters[key] = (help, label_map, current[2] + 1)

    def observe(
        self, *, name: str, help: str, value: float, labels: Mapping[str, str] | None = None
    ) -> None:
        label_map = dict(labels or {})
        key = (name, _label_key(label_map))
        with self._lock:
            current = self._histograms.get(key)
            if current is None:
                counts = tuple(1 if bucket >= value else 0 for bucket in self._buckets)
                self._histograms[key] = (help, label_map, counts, value, 1)
            else:
                _, _, counts, total, count = current
                updated = tuple(
                    existing + 1 if bucket >= value else existing
                    for existing, bucket in zip(counts, self._buckets, strict=True)
                )
                self._histograms[key] = (help, label_map, updated, total + value, count + 1)

    def snapshot(self) -> tuple[CounterSnapshot | HistogramSnapshot, ...]:
        with self._lock:
            counters = tuple(
                CounterSnapshot(name=name, help=help_text, labels=dict(labels), value=value)
                for (name, _), (help_text, labels, value) in sorted(self._counters.items())
            )
            histograms = tuple(
                HistogramSnapshot(
                    name=name,
                    help=help_text,
                    labels=dict(labels),
                    buckets=self._buckets,
                    counts=counts,
                    sum=total,
                    count=count,
                )
                for (name, _), (help_text, labels, counts, total, count) in sorted(
                    self._histograms.items()
                )
            )
        return counters + histograms

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._histograms.clear()

    def render_prometheus_text(self) -> str:
        """Render all metrics in the Prometheus text exposition format."""
        lines: list[str] = []
        for snapshot in self.snapshot():
            labels = _labels_text(snapshot.labels)
            if isinstance(snapshot, CounterSnapshot):
                lines.append(f"# HELP {snapshot.name} {_escape(snapshot.help)}")
                lines.append(f"# TYPE {snapshot.name} counter")
                lines.append(f"{snapshot.name}{labels} {snapshot.value}")
            elif isinstance(snapshot, HistogramSnapshot):
                lines.append(f"# HELP {snapshot.name} {_escape(snapshot.help)}")
                lines.append(f"# TYPE {snapshot.name} histogram")
                for bucket, count in zip(snapshot.buckets, snapshot.counts, strict=True):
                    lines.append(f'{snapshot.name}_bucket{{le="{bucket:g}"}} {count}')
                lines.append(f"{snapshot.name}_sum{labels} {snapshot.sum:g}")
                lines.append(f"{snapshot.name}_count{labels} {snapshot.count}")
        return "\n".join(lines) + "\n"


METRICS = MetricsRegistry()


def record_request(*, method: str, status_code: int, duration_seconds: float) -> None:
    """Record one HTTP request outcome and its latency."""
    METRICS.increment(
        name="ophanim_http_requests_total",
        help="Total HTTP requests handled by Ophanim Core.",
        labels={"method": method, "status_code": str(status_code)},
    )
    METRICS.observe(
        name="ophanim_http_request_duration_seconds",
        help="HTTP request latency in seconds.",
        value=duration_seconds,
        labels={"method": method},
    )


def record_policy_decision(*, action: str, outcome: str) -> None:
    """Record one policy evaluation outcome for an action."""
    METRICS.increment(
        name="ophanim_policy_decisions_total",
        help="Total policy decisions evaluated by Ophanim Core.",
        labels={"action": action, "outcome": outcome},
    )


def record_tool_call(*, tool: str, outcome: str) -> None:
    """Record one governed tool execution outcome."""
    METRICS.increment(
        name="ophanim_tool_calls_total",
        help="Total governed tool executions by Ophanim Core.",
        labels={"tool": tool, "outcome": outcome},
    )


def record_skill_run(*, skill: str, classification: str, outcome: str) -> None:
    """Record one skill run outcome."""
    METRICS.increment(
        name="ophanim_skill_runs_total",
        help="Total skill run outcomes by Ophanim Core.",
        labels={"skill": skill, "classification": classification, "outcome": outcome},
    )
