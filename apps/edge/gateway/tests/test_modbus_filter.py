from __future__ import annotations

import hashlib
import json

import pytest

from apps.edge.gateway.modbus_filter.parser import (
    FrameParseError,
    extract_frames,
    parse_frame,
)
from apps.edge.gateway.modbus_filter.policy import (
    ALLOWED_FUNCTION_CODES,
    classify_frame,
    exception_response,
)
from apps.edge.gateway.main import ModbusFilterGateway


def make_request(transaction_id: int, pdu: bytes, unit_id: int = 1) -> bytes:
    return (
        transaction_id.to_bytes(2, "big")
        + b"\x00\x00"
        + (len(pdu) + 1).to_bytes(2, "big")
        + bytes([unit_id])
        + pdu
    )


def test_read_function_codes_are_allowed() -> None:
    for function_code in ALLOWED_FUNCTION_CODES:
        frame = parse_frame(make_request(7, bytes([function_code, 0, 0, 0, 1])))
        assert classify_frame(frame).allowed is True


@pytest.mark.parametrize("function_code", [5, 6, 15, 16, 99])
def test_write_and_unknown_function_codes_are_rejected(function_code: int) -> None:
    frame = parse_frame(make_request(7, bytes([function_code, 0, 0, 0, 1])))
    decision = classify_frame(frame)
    assert decision.allowed is False
    assert decision.reason == "function_code_not_allowed"


def test_rejected_frame_gets_modbus_illegal_function_exception() -> None:
    request = make_request(12, b"\x06\x00\x10\x00\x01", unit_id=3)
    frame = parse_frame(request)
    assert exception_response(frame) == make_request(12, b"\x86\x01", unit_id=3)


def test_fragmented_mbap_is_reassembled() -> None:
    request = make_request(1, b"\x03\x00\x00\x00\x02")
    frames, remainder = extract_frames(request[:4])
    assert frames == []
    assert remainder == request[:4]
    frames, remainder = extract_frames(remainder + request[4:])
    assert frames == [request]
    assert remainder == b""


def test_multiple_requests_are_extracted_from_one_buffer() -> None:
    first = make_request(1, b"\x01\x00\x00\x00\x01")
    second = make_request(2, b"\x04\x00\x00\x00\x01")
    assert extract_frames(first + second) == ([first, second], b"")


def test_invalid_mbap_length_is_rejected() -> None:
    with pytest.raises(FrameParseError, match="invalid MBAP length"):
        parse_frame(b"\x00\x01\x00\x00\x00\x01\x01\x03")


def test_rejected_write_log_contains_required_fields(tmp_path) -> None:
    gateway = ModbusFilterGateway(log_path=tmp_path / "rejected_writes.log")
    request = make_request(4, b"\x10\x00\x01\x00\x01")

    gateway.log_rejected(request, source_ip="10.0.0.4")

    record = json.loads((tmp_path / "rejected_writes.log").read_text())
    assert record["function_code"] == 16
    assert record["source_ip"] == "10.0.0.4"
    assert record["raw_pdu_hash"] == hashlib.sha256(b"\x10\x00\x01\x00\x01").hexdigest()
    assert "ts" in record
