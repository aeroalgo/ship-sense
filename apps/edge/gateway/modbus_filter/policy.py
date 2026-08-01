from __future__ import annotations

from dataclasses import dataclass

from apps.edge.gateway.modbus_filter.parser import ModbusFrame

ALLOWED_FUNCTION_CODES = frozenset({1, 2, 3, 4})


@dataclass(frozen=True, slots=True)
class FrameDecision:
    allowed: bool
    reason: str | None = None


def classify_frame(frame: ModbusFrame) -> FrameDecision:
    if frame.function_code in ALLOWED_FUNCTION_CODES:
        return FrameDecision(allowed=True)
    return FrameDecision(allowed=False, reason="function_code_not_allowed")


def exception_response(frame: ModbusFrame) -> bytes:
    pdu = bytes([frame.function_code | 0x80, 0x01])
    return (
        frame.transaction_id.to_bytes(2, "big")
        + frame.protocol_id.to_bytes(2, "big")
        + (len(pdu) + 1).to_bytes(2, "big")
        + bytes([frame.unit_id])
        + pdu
    )
