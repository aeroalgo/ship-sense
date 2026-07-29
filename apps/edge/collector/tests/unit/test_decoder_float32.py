from __future__ import annotations

import math
import struct

import pytest

from collector.plugins.modbus.decoder import decode_float32


def _pack_be(value: float) -> tuple[int, int]:
    """Упаковать float в 2 регистра в порядке ABCD (word=big, byte=big)."""
    b = struct.pack(">f", value)
    return (b[0] << 8) | b[1], (b[2] << 8) | b[3]


# 42.0 = 0x42280000 → ABCD: [0x4228, 0x0000]
FORTY_TWO = {
    "ABCD": [0x4228, 0x0000],
    "CDAB": [0x0000, 0x4228],
    "BADC": [0x2842, 0x0000],
    "DCBA": [0x0000, 0x2842],
}

# 1.0 = 0x3F800000 → A=0x3F B=0x80 C=0x00 D=0x00
ONE = {
    "ABCD": [0x3F80, 0x0000],
    "CDAB": [0x0000, 0x3F80],
    "BADC": [0x803F, 0x0000],
    "DCBA": [0x0000, 0x803F],
}

ORDER_MAP = {
    "ABCD": ("big", "big"),
    "CDAB": ("little", "big"),
    "BADC": ("big", "little"),
    "DCBA": ("little", "little"),
}


@pytest.mark.parametrize(
    "layout",
    ["ABCD", "CDAB", "BADC", "DCBA"],
)
def test_decode_float32_forty_two_all_orders(layout: str) -> None:
    word_order, byte_order = ORDER_MAP[layout]
    regs = FORTY_TWO[layout]

    result = decode_float32(regs, word_order=word_order, byte_order=byte_order)

    assert result == pytest.approx(42.0)


@pytest.mark.parametrize(
    "layout",
    ["ABCD", "CDAB", "BADC", "DCBA"],
)
def test_decode_float32_one_all_orders(layout: str) -> None:
    word_order, byte_order = ORDER_MAP[layout]
    regs = ONE[layout]

    result = decode_float32(regs, word_order=word_order, byte_order=byte_order)

    assert result == pytest.approx(1.0)


def test_decode_float32_negative_value() -> None:
    # -0.5 = 0xBF000000 → ABCD: [0xBF00, 0x0000]
    result = decode_float32([0xBF00, 0x0000], word_order="big", byte_order="big")

    assert result == pytest.approx(-0.5)


def test_decode_float32_pi() -> None:
    # 3.1415927 (float32) → ABCD round-trip через эталонную упаковку
    reg_hi, reg_lo = _pack_be(3.1415927)
    result = decode_float32([reg_hi, reg_lo], word_order="big", byte_order="big")

    assert result == pytest.approx(3.1415927, rel=1e-6)


def test_decode_float32_zero() -> None:
    assert decode_float32([0x0000, 0x0000], word_order="big", byte_order="big") == 0.0


def test_decode_float32_wrong_word_order_mismatches() -> None:
    # ABCD данные, декодированные как CDAB → не 42.0 (AC-B2-12: защита от ПНР mismatch)
    result = decode_float32([0x4228, 0x0000], word_order="little", byte_order="big")

    assert result != pytest.approx(42.0)


def test_decode_float32_accepts_tuple() -> None:
    result = decode_float32((0x4228, 0x0000), word_order="big", byte_order="big")
    assert result == pytest.approx(42.0)


def test_decode_float32_rejects_wrong_length() -> None:
    with pytest.raises((ValueError, TypeError)):
        decode_float32([0x4228], word_order="big", byte_order="big")
    with pytest.raises((ValueError, TypeError)):
        decode_float32([0x4228, 0x0000, 0x0001], word_order="big", byte_order="big")


def test_decode_float32_rejects_invalid_register_value() -> None:
    # регистр — 16 бит; значение вне диапазона → явная ошибка
    with pytest.raises((ValueError, TypeError)):
        decode_float32([0x10000, 0x0000], word_order="big", byte_order="big")


def test_decode_float32_rejects_invalid_order() -> None:
    with pytest.raises((ValueError, TypeError)):
        decode_float32([0x4228, 0x0000], word_order="middle", byte_order="big")
    with pytest.raises((ValueError, TypeError)):
        decode_float32([0x4228, 0x0000], word_order="big", byte_order="middle")


def test_decode_float32_nan() -> None:
    # NaN: 0x7FC00000 → ABCD: [0x7FC0, 0x0000]
    result = decode_float32([0x7FC0, 0x0000], word_order="big", byte_order="big")
    assert math.isnan(result)
