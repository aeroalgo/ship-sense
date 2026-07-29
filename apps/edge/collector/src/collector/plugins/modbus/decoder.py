from __future__ import annotations

import struct
from typing import Literal, Sequence

__all__ = ["decode_float32", "decode_int", "extract_bit"]

WordOrder = Literal["big", "little"]
ByteOrder = Literal["big", "little"]
Datatype = Literal["uint16", "int16", "uint32", "int32"]

_REGISTER_MASK = 0xFFFF


def _validate_register(value: int) -> int:
    """16-битный регистр Modbus: 0..0xFFFF. Любое отклонение → ValueError."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"register must be int, got {type(value).__name__}")
    if value < 0 or value > _REGISTER_MASK:
        raise ValueError(f"register out of 16-bit range: {value}")
    return value


def _word_bytes(register: int, byte_order: ByteOrder) -> bytes:
    """2 байта одного регистра в порядке byte_order (AC-B2-02).

    big  → [hi, lo]   (старший байт первым, естественный порядок слова)
    little → [lo, hi] (байты в слове переставлены)
    """
    hi = (register >> 8) & 0xFF
    lo = register & 0xFF
    if byte_order == "big":
        return bytes([hi, lo])
    if byte_order == "little":
        return bytes([lo, hi])
    raise ValueError(f"byte_order must be 'big' or 'little', got {byte_order!r}")


def decode_float32(
    regs: Sequence[int],
    *,
    word_order: WordOrder,
    byte_order: ByteOrder,
) -> float:
    """AC-B2-02 / AC-B2-12: IEEE754 float32 из 2 регистров Modbus.

    Порядок сборки 4 байт:
      1. Каждый регистр → 2 байта по ``byte_order`` (порядок байт в слове).
      2. Слова выкладываются по ``word_order`` (big — старшее слово первым).

    Все 4 варианта endianness (ABCD/CDAB/BADC/DCBA) восстанавливаются
    комбинацией word_order × byte_order. Без сетевого I/O.
    """
    if word_order not in ("big", "little"):
        raise ValueError(f"word_order must be 'big' or 'little', got {word_order!r}")
    if not isinstance(regs, (list, tuple)):
        raise TypeError(f"regs must be a sequence of 2 ints, got {type(regs).__name__}")
    if len(regs) != 2:
        raise ValueError(f"float32 needs exactly 2 registers, got {len(regs)}")

    w0 = _validate_register(regs[0])
    w1 = _validate_register(regs[1])
    b0 = _word_bytes(w0, byte_order)
    b1 = _word_bytes(w1, byte_order)
    raw = b0 + b1 if word_order == "big" else b1 + b0
    return struct.unpack(">f", raw)[0]


def decode_int(
    regs: Sequence[int],
    *,
    datatype: Datatype,
    endian: WordOrder,
) -> int:
    """AC-B2-03: int16/uint16 (1 рег) и int32/uint32 (2 рега).

    ``endian`` — порядок: для 16-бит это байтовый порядок в слове,
    для 32-бит это порядок слов (high word first при 'big').
    """
    if endian not in ("big", "little"):
        raise ValueError(f"endian must be 'big' or 'little', got {endian!r}")
    if not isinstance(regs, (list, tuple)):
        raise TypeError(f"regs must be a sequence of ints, got {type(regs).__name__}")
    if datatype not in ("uint16", "int16", "uint32", "int32"):
        raise ValueError(f"unsupported datatype: {datatype!r}")

    if datatype in ("uint16", "int16"):
        if len(regs) != 1:
            raise ValueError(f"{datatype} needs exactly 1 register, got {len(regs)}")
        value = _validate_register(regs[0])
        if endian == "little":
            value = ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
        if datatype == "int16" and value >= 0x8000:
            value -= 0x10000
        return value

    # 32-битные: 2 регистра
    if len(regs) != 2:
        raise ValueError(f"{datatype} needs exactly 2 registers, got {len(regs)}")
    w0 = _validate_register(regs[0])
    w1 = _validate_register(regs[1])
    value = (w0 << 16) | w1 if endian == "big" else (w1 << 16) | w0
    if datatype == "int32" and value >= 0x80000000:
        value -= 0x100000000
    return value


def extract_bit(register: int, bit_index: int) -> bool:
    """AC-B2-04: native_id ``{register}.{bit_index}`` → бит по индексу 0..15.

    Извлечение: ``(register >> bit_index) & 1`` (план §12.4).
    """
    _validate_register(register)
    if isinstance(bit_index, bool) or not isinstance(bit_index, int):
        raise ValueError(f"bit_index must be int, got {type(bit_index).__name__}")
    if bit_index < 0 or bit_index > 15:
        raise ValueError(f"bit_index out of 0..15 range: {bit_index}")
    return bool((register >> bit_index) & 1)
