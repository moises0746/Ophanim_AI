"""Protocol codec adapter and message validator for Hub-Node communication."""

from __future__ import annotations

import json
from datetime import datetime

from ophanim.domain.errors import DomainValidationError
from ophanim.domain.protocol import (
    CURRENT_PROTOCOL_VERSION,
    HubNodeMessage,
    ProtocolHeader,
    ProtocolMessageType,
)
from ophanim.ports.protocol import ProtocolCodecPort


class JsonProtocolCodec(ProtocolCodecPort):
    """JSON serde implementation of ProtocolCodecPort."""

    def encode(self, message: HubNodeMessage) -> str:
        data = {
            "header": {
                "protocol_version": message.header.protocol_version,
                "message_id": message.header.message_id,
                "message_type": message.header.message_type.value,
                "timestamp_utc": message.header.timestamp_utc.isoformat(),
                "device_id": message.header.device_id,
                "sequence": message.header.sequence,
                "correlation_id": message.header.correlation_id,
            },
            "payload": message.payload,
        }
        return json.dumps(data)

    def decode(self, raw_json: str) -> HubNodeMessage:
        try:
            data = json.loads(raw_json)
        except Exception as exc:
            raise DomainValidationError(f"Invalid protocol JSON: {exc}") from exc

        if not isinstance(data, dict) or "header" not in data or "payload" not in data:
            raise DomainValidationError("Protocol message must contain 'header' and 'payload'")

        hdr = data["header"]
        if hdr.get("protocol_version") != CURRENT_PROTOCOL_VERSION:
            raise DomainValidationError(
                f"Unsupported protocol version {hdr.get('protocol_version')}; expected {CURRENT_PROTOCOL_VERSION}"
            )

        try:
            timestamp = datetime.fromisoformat(hdr["timestamp_utc"])
            header = ProtocolHeader(
                protocol_version=hdr.get("protocol_version", CURRENT_PROTOCOL_VERSION),
                message_id=hdr["message_id"],
                message_type=ProtocolMessageType(hdr["message_type"]),
                timestamp_utc=timestamp,
                device_id=hdr["device_id"],
                sequence=hdr["sequence"],
                correlation_id=hdr.get("correlation_id"),
            )
        except Exception as exc:
            raise DomainValidationError(f"Invalid protocol header: {exc}") from exc

        return HubNodeMessage(header=header, payload=data["payload"])


class AntiReplayTracker:
    """Stateful sequence and anti-replay tracker for connected device nodes."""

    def __init__(self, max_drift_seconds: float = 60.0) -> None:
        self._max_drift_seconds = max_drift_seconds
        self._device_sequences: dict[str, int] = {}

    def validate_and_record(self, message: HubNodeMessage) -> None:
        """Validate timestamp freshness and monotonic sequence numbers per device."""
        if not message.validate_freshness(self._max_drift_seconds):
            raise DomainValidationError(
                f"Message {message.header.message_id} timestamp outside freshness window (+/-{self._max_drift_seconds}s)"
            )

        device_id = message.header.device_id
        current_seq = self._device_sequences.get(device_id, -1)

        if message.header.sequence <= current_seq:
            raise DomainValidationError(
                f"Replay detected for device {device_id}: received seq {message.header.sequence} <= current seq {current_seq}"
            )

        self._device_sequences[device_id] = message.header.sequence
