"""Unit and integration tests for Hub-Node protocol encoding, decoding, and anti-replay."""

from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest

from ophanim.adapters.protocol import AntiReplayTracker, JsonProtocolCodec
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.protocol import (
    CURRENT_PROTOCOL_VERSION,
    HeartbeatPayload,
    HubNodeMessage,
    LeaseOfferPayload,
    ProtocolHeader,
    ProtocolMessageType,
    SystemMetrics,
)


def test_protocol_codec_encode_decode_roundtrip() -> None:
    codec = JsonProtocolCodec()
    header = ProtocolHeader(
        message_type=ProtocolMessageType.HEARTBEAT,
        device_id="node-device-01",
        sequence=1,
    )
    metrics = SystemMetrics(
        cpu_percent=12.5,
        memory_used_mb=1024.0,
        memory_total_mb=8192.0,
        disk_available_gb=120.5,
    )
    payload = HeartbeatPayload(
        status="active",
        metrics=metrics,
        available_tools=("db.query", "log.search"),
    )

    msg = HubNodeMessage(header=header, payload=asdict(payload))
    encoded = codec.encode(msg)

    decoded = codec.decode(encoded)
    assert decoded.header.protocol_version == CURRENT_PROTOCOL_VERSION
    assert decoded.header.message_type == ProtocolMessageType.HEARTBEAT
    assert decoded.header.device_id == "node-device-01"
    assert decoded.header.sequence == 1
    assert decoded.payload["status"] == "active"
    assert decoded.payload["available_tools"] == ["db.query", "log.search"]


def test_lease_offer_and_execution_report_schemas() -> None:
    codec = JsonProtocolCodec()
    offer = LeaseOfferPayload(
        lease_id="lease-123",
        task_id="task-456",
        task_step_id="step-789",
        tool_name="db.query",
        parameters={"query": "SELECT * FROM transactions LIMIT 5"},
        timeout_seconds=45,
        risk_level="low",
    )
    msg = HubNodeMessage(
        header=ProtocolHeader(
            message_type=ProtocolMessageType.LEASE_OFFER,
            device_id="node-device-01",
            sequence=2,
        ),
        payload=asdict(offer),
    )
    encoded = codec.encode(msg)
    decoded = codec.decode(encoded)
    assert decoded.payload["tool_name"] == "db.query"
    assert decoded.payload["timeout_seconds"] == 45


def test_protocol_version_mismatch_rejected() -> None:
    codec = JsonProtocolCodec()
    raw_invalid_version = """
    {
        "header": {
            "protocol_version": "9.9.9",
            "message_id": "00000000-0000-0000-0000-000000000000",
            "message_type": "node.heartbeat",
            "timestamp_utc": "2026-08-15T12:00:00Z",
            "device_id": "node-01",
            "sequence": 1
        },
        "payload": {}
    }
    """
    with pytest.raises(DomainValidationError, match="Unsupported protocol version"):
        codec.decode(raw_invalid_version)


def test_anti_replay_monotonic_sequences() -> None:
    tracker = AntiReplayTracker(max_drift_seconds=60.0)
    device_id = "node-alpha"

    msg1 = HubNodeMessage(
        header=ProtocolHeader(
            message_type=ProtocolMessageType.HEARTBEAT,
            device_id=device_id,
            sequence=1,
        ),
        payload={},
    )
    msg2 = HubNodeMessage(
        header=ProtocolHeader(
            message_type=ProtocolMessageType.HEARTBEAT,
            device_id=device_id,
            sequence=2,
        ),
        payload={},
    )
    msg_replayed = HubNodeMessage(
        header=ProtocolHeader(
            message_type=ProtocolMessageType.HEARTBEAT,
            device_id=device_id,
            sequence=2,
        ),
        payload={},
    )
    msg_stale = HubNodeMessage(
        header=ProtocolHeader(
            message_type=ProtocolMessageType.HEARTBEAT,
            device_id=device_id,
            sequence=1,
        ),
        payload={},
    )

    tracker.validate_and_record(msg1)
    tracker.validate_and_record(msg2)

    # Replayed sequence 2
    with pytest.raises(DomainValidationError, match="Replay detected"):
        tracker.validate_and_record(msg_replayed)

    # Stale sequence 1
    with pytest.raises(DomainValidationError, match="Replay detected"):
        tracker.validate_and_record(msg_stale)


def test_anti_replay_freshness_drift_window() -> None:
    tracker = AntiReplayTracker(max_drift_seconds=30.0)
    device_id = "node-beta"

    old_time = datetime.now(UTC) - timedelta(seconds=60)
    stale_msg = HubNodeMessage(
        header=ProtocolHeader(
            message_type=ProtocolMessageType.HEARTBEAT,
            timestamp_utc=old_time,
            device_id=device_id,
            sequence=1,
        ),
        payload={},
    )

    with pytest.raises(DomainValidationError, match="timestamp outside freshness window"):
        tracker.validate_and_record(stale_msg)
