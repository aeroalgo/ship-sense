# [T-001 | s06 | modbus-decoder] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s06-modbus-decoder.md](../../plan/decompose-v1-p1-collector/s06-modbus-decoder.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L1 (2 файла кода + 2 теста, <1ч; pure functions без I/O)
**AC:** AC-B2-02, AC-B2-03, AC-B2-04, AC-B2-12
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s06-modbus-decoder.md`

## Skills
- tdd, modern-python, python-testing-patterns (по workflow-implement)
- verification-before-completion (перед FINISH)

## Сделано
- Создан пакет `collector/plugins/modbus/` (`__init__.py` — пустой).
- Создан `plugins/modbus/decoder.py` — чистые pure-функции, без сетевого I/O
  (план §12.3–12.4, AC-B2-02/03/04/12):
  - `decode_float32(regs, *, word_order, byte_order) → float` — IEEE754 float32
    из 2 регистров. Сборка 4 байт: каждый регистр → 2 байта по `byte_order`
    (порядок байт в слове), затем слова выкладываются по `word_order`
    (big — старшее слово первым). Все 4 варианта endianness
    (ABCD/CDAB/BADC/DCBA) восстанавливаются комбинацией word×byte order.
    `struct.unpack(">f", raw)`.
  - `decode_int(regs, *, datatype, endian) → int` — int16/uint16 (1 рег),
    int32/uint32 (2 рега). `endian` для 16-бит — байтовый порядок в слове,
    для 32-бит — порядок слов (high word first при 'big'). Знак через
    two's-complement коррекцию (0x8000/0x80000000).
  - `extract_bit(register, bit_index) → bool` — native_id pattern
    `{register}.{bit_index}` (план §12.4), bit_index 0..15. Извлечение
    `(register >> bit_index) & 1`. Возвращает строго `bool`.
- Валидация входов (AC-B2-12 edge-cases, §«Чекпоинт верификации»):
  - регистр — 16 бит (0..0xFFFF); вне диапазона / не int / bool → `ValueError`/`TypeError`;
  - `decode_float32` — ровно 2 регистра, иначе явная ошибка;
  - `decode_int` — длина regs по datatype (1 для *16, 2 для *32);
  - `extract_bit` — bit_index в диапазоне 0..15;
  - `word_order`/`byte_order`/`endian` — только `"big"`/`"little"`;
    `datatype` — только из 4 supported; иначе `ValueError`.
- Сигнатура `decode_float32(regs, ...)` — по каноническому decompose step
  (plan §12.3 давал `(reg_hi, reg_lo, ...)`; decompose — source of truth
  для IMPLEMENT, принимает sequence из 2 регистров — удобнее для caller'а
  в s08 connector, который работает со списком regs из pymodbus).

## Файлы
- `apps/edge/collector/src/collector/plugins/modbus/__init__.py` (Создание — пустой пакет)
- `apps/edge/collector/src/collector/plugins/modbus/decoder.py` (Создание)
- `apps/edge/collector/tests/unit/test_decoder_float32.py` (Создание)
- `apps/edge/collector/tests/unit/test_bitfield.py` (Создание)

## Тесты
- **Runner note:** venv в корне репо — `/home/aero/PyProject/ship-sense/.venv/bin/python`;
  `PYTHONPATH=apps/edge/collector/src`. Без `pytest-asyncio` (pure sync функции).
- **Golden vectors** (AC-B2-12): IEEE754 hex-эталоны для всех 4 endianness.
  - 42.0 = 0x42280000 → ABCD `[0x4228,0x0000]`, CDAB `[0x0000,0x4228]`,
    BADC `[0x2842,0x0000]`, DCBA `[0x0000,0x2842]`.
  - 1.0 = 0x3F800000 → аналогично 4 layouts.
  - -0.5 = 0xBF000000, π=3.1415927 (round-trip через `struct.pack(">f")`),
    0.0, NaN (0x7FC00000).
- **Wrong order mismatch** (AC-B2-12 защита от ПНР): ABCD данные,
  декодированные как CDAB → не 42.0.
- **Bit 40200.3** (AC-B2-04): `extract_bit(0x0008, 3) is True`;
  full-range (0xFFFF все set / 0x0000 все clear), LSB/MSB, returns `bool`.
- **Int** (AC-B2-03): uint16/int16 (0xFFFF → 65535 / -1; 0x8000 → -32768),
  uint32/int32 (big/little word order; 100000=0x000186A0 → `[0x0001,0x86A0]`;
  0xFFFFFFFF → -1).
- **Валидация ошибок:** неверная длина regs, регистр вне 16 бит,
  неизвестный datatype, неверный order, bit_index вне 0..15 — все `ValueError`/`TypeError`.
- red: `PYTHONPATH=src ... -m pytest tests/unit/test_decoder_float32.py tests/unit/test_bitfield.py`
  → `ModuleNotFoundError: No module named 'collector.plugins.modbus.decoder'`.
- cmd targeted: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_decoder_float32.py tests/unit/test_bitfield.py`
- итог targeted: `38 passed in 0.03s`.
- cmd regression: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/`
- итог regression: `94 passed in 0.42s` (s01–s05b=56 + 38 новых s06).

Покрытие (чекпоинты decompose §«Чекпоинт верификации»):
- все golden float32 (ABCD/CDAB/BADC/DCBA) — green ✓
- bit 40200.3 корректно (extract_bit) — green ✓
- невалидная длина regs → явная ошибка — green ✓
- без сетевого I/O — pure functions, broker grep не требуется ✓

## Integration check (§0.11)
- Новых routes/keys/env/cols/migrations — **нет**. Шаг = pure decoder-функции
  в новом пакете `plugins/modbus/`. Регистрация в `PluginRegistry` — s08
  (connector), не этот шаг.
- `decoder.py` импортирует только `struct`, `typing` — без I/O, без broker,
  без внешних сервисов. §0.11 counterpart не нужен (нет key/env/event/col/route).
