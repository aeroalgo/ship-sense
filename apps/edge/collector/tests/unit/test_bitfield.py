from __future__ import annotations

import pytest

from collector.plugins.modbus.decoder import (
    decode_int,
    extract_bit,
)


# --- extract_bit: native_id pattern "40200.3" (AC-B2-04) ---


def test_extract_bit_set() -> None:
    # регистр = 0b1000 (8), бит 3 → True
    assert extract_bit(0x0008, 3) is True


def test_extract_bit_clear() -> None:
    # регистр = 0b0100 (4), бит 3 → False
    assert extract_bit(0x0004, 3) is False


def test_extract_bit_all_set_register() -> None:
    for i in range(16):
        assert extract_bit(0xFFFF, i) is True


def test_extract_bit_zero_register() -> None:
    for i in range(16):
        assert extract_bit(0x0000, i) is False


def test_extract_bit_lsb_and_msb() -> None:
    assert extract_bit(0x0001, 0) is True
    assert extract_bit(0x8000, 15) is True
    assert extract_bit(0x4000, 15) is False


def test_extract_bit_high_bit_only() -> None:
    # 0x8000 → только бит 15
    assert extract_bit(0x8000, 14) is False
    assert extract_bit(0x8000, 15) is True


def test_extract_bit_returns_bool_not_int() -> None:
    assert extract_bit(0x0008, 3) is True
    assert isinstance(extract_bit(0x0008, 3), bool)


def test_extract_bit_rejects_out_of_range_index() -> None:
    with pytest.raises((ValueError, IndexError)):
        extract_bit(0x0001, 16)
    with pytest.raises((ValueError, IndexError)):
        extract_bit(0x0001, -1)


def test_extract_bit_rejects_invalid_register_value() -> None:
    with pytest.raises((ValueError, TypeError)):
        extract_bit(0x10000, 0)


# --- decode_int: int16/uint16/int32/uint32 (AC-B2-03) ---


def test_decode_uint16() -> None:
    assert decode_int([0x1234], datatype="uint16", endian="big") == 0x1234


def test_decode_int16_negative() -> None:
    # 0xFFFF unsigned = 65535, signed = -1
    assert decode_int([0xFFFF], datatype="int16", endian="big") == -1


def test_decode_int16_min() -> None:
    assert decode_int([0x8000], datatype="int16", endian="big") == -32768


def test_decode_uint16_max() -> None:
    assert decode_int([0xFFFF], datatype="uint16", endian="big") == 65535


def test_decode_uint32_big() -> None:
    # word=big: regs[0] high, regs[1] low
    assert decode_int([0x0001, 0x0002], datatype="uint32", endian="big") == 0x00010002


def test_decode_uint32_little() -> None:
    # word=little: regs[0] low, regs[1] high
    assert decode_int([0x0001, 0x0002], datatype="uint32", endian="little") == 0x00020001


def test_decode_int32_negative() -> None:
    assert decode_int([0xFFFF, 0xFFFF], datatype="int32", endian="big") == -1


def test_decode_int32_big_endian_from_golden() -> None:
    # 100000 = 0x000186A0 → regs [0x0001, 0x86A0], big
    assert decode_int([0x0001, 0x86A0], datatype="int32", endian="big") == 100000


def test_decode_int_wrong_length_for_uint32() -> None:
    with pytest.raises((ValueError, TypeError)):
        decode_int([0x0001], datatype="uint32", endian="big")
    with pytest.raises((ValueError, TypeError)):
        decode_int([0x0001, 0x0002, 0x0003], datatype="uint32", endian="big")


def test_decode_int_wrong_length_for_uint16() -> None:
    with pytest.raises((ValueError, TypeError)):
        decode_int([0x0001, 0x0002], datatype="uint16", endian="big")


def test_decode_int_unknown_datatype() -> None:
    with pytest.raises((ValueError, TypeError)):
        decode_int([0x0001], datatype="float64", endian="big")


def test_decode_int_rejects_invalid_register_value() -> None:
    with pytest.raises((ValueError, TypeError)):
        decode_int([0x10000], datatype="uint16", endian="big")
