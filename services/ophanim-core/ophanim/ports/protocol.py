"""Port interfaces for Hub-Node protocol encoding, decoding, and dispatch."""

from __future__ import annotations

from typing import Protocol

from ophanim.domain.protocol import HubNodeMessage


class ProtocolCodecPort(Protocol):
    """Protocol encoder and decoder supporting JSON/WSS serde."""

    def encode(self, message: HubNodeMessage) -> str:
        """Serialize a protocol message to standard JSON string."""
        ...

    def decode(self, raw_json: str) -> HubNodeMessage:
        """Deserialize and validate raw JSON into a HubNodeMessage envelope."""
        ...
