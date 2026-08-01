from __future__ import annotations

from dataclasses import dataclass


class FrameParseError(ValueError):
    """Raised when a Modbus TCP frame has an invalid MBAP header."""


@dataclass(frozen=True, slots=True)
class ModbusFrame:
    raw: bytes
    transaction_id: int
    protocol_id: int
    unit_id: int
    pdu: bytes

    @property
    def function_code(self) -> int:
        return self.pdu[0]


def parse_frame(raw: bytes) -> ModbusFrame:
    if len(raw) < 8:
        raise FrameParseError("frame is shorter than MBAP header and function code")
    length = int.from_bytes(raw[4:6], "big")
    if length < 2 or len(raw) != 6 + length:
        raise FrameParseError("invalid MBAP length")
    return ModbusFrame(
        raw=raw,
        transaction_id=int.from_bytes(raw[0:2], "big"),
        protocol_id=int.from_bytes(raw[2:4], "big"),
        unit_id=raw[6],
        pdu=raw[7:],
    )


def extract_frames(buffer: bytes) -> tuple[list[bytes], bytes]:
    frames: list[bytes] = []
    offset = 0
    while len(buffer) - offset >= 6:
        length = int.from_bytes(buffer[offset + 4 : offset + 6], "big")
        if length < 2:
            raise FrameParseError("invalid MBAP length")
        frame_end = offset + 6 + length
        if len(buffer) < frame_end:
            break
        frame = buffer[offset:frame_end]
        parse_frame(frame)
        frames.append(frame)
        offset = frame_end
    return frames, buffer[offset:]
