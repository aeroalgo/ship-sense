# [T-001 | s07 | modbus-client] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s07-modbus-client.md](../../plan/decompose-v1-p1-collector/s07-modbus-client.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L1 (2 файла, <1ч; wrapper над pymodbus)
**AC:** AC-B2-01, AC-B2-07, AC-B2-08, AC-B2-09, AC-B2-11
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s07-modbus-client.md`

## Skills
- tdd, modern-python, python-testing-patterns (по workflow-implement)
- verification-before-completion (перед FINISH)

## Сделано
- Создан `plugins/modbus/client.py` — `AsyncModbusClient` (async wrapper над `pymodbus.client.AsyncModbusTcpClient`):
  - `__init__(host, port=502, timeout=3.0, device_id=1)`.
  - `connect() → bool`: создаёт `AsyncModbusTcpClient`, вызывает `.connect()`, сохраняет `_client`. Возвращает `True/False` (не роняет на TCP fail).
  - `disconnect()`: вызывает `.close()`, обнуляет `_client`. Идемпотентен.
  - `reconnect() → bool`: `disconnect()` + `connect()`. Для recovery после разрыва (AC-B2-07).
  - `read_holding(address, count=1) → list[int]`: FC03. `asyncio.wait_for(..., timeout)`. На `TimeoutError` → `ModbusTimeoutError`. На `ModbusException` → propagate (AC-B2-08). Проверяет `resp.isError()`.
  - `read_input(address, count=1) → list[int]`: FC04 (аналогично).
  - `@property connected`: делегирует `self._client.connected`.
  - **Инвариант (AC-B2-11):** модуль и экземпляр НЕ экспортируют `write_*` (grep по `write_|FC05|FC06|FC15|FC16` — чисто).
- Созданы typed errors:
  - `ModbusClientError(Exception)` — база.
  - `ModbusTimeoutError(ModbusClientError)` — таймаут (AC-B2-09).
- `__init__.py` остаётся пустым (как в s06) — импорты по полному пути.

## Файлы
- `apps/edge/collector/src/collector/plugins/modbus/client.py` (Создание)
- `apps/edge/collector/src/collector/plugins/modbus/__init__.py` (пустой, уже существовал)
- `apps/edge/collector/tests/unit/test_modbus_client.py` (Создание)

## Тесты
- **Runner note:** `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m pytest`. Async-тесты через `pytest.mark.asyncio` (проект использует `pytest-asyncio` в collector).
- red: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_modbus_client.py` → `ModuleNotFoundError: No module named 'collector.plugins.modbus.client'`.
- cmd targeted: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_modbus_client.py`
- итог targeted: **15 passed in 0.21s**.
- cmd regression: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/`
- итог regression: **109 passed in 0.48s** (s01–s06=94 + 15 новых s07).

Покрытие (чекпоинты decompose §«Чекпоинт верификации»):
- нет write methods в публичном API — green ✓ (2 теста + grep)
- reconnect после disconnect — green ✓ (`test_reconnect_after_disconnect`, `test_read_after_reconnect_uses_fresh_session`)
- timeout → `ModbusTimeoutError` (typed) — green ✓ (`test_read_holding_timeout_raises_typed_error`)
- exception на одном read не ломает следующий — green ✓ (`test_modbus_exception_propagates_without_killing_loop`)
- connect fail → `False`, не роняет — green ✓
- read до connect → `ModbusClientError("not connected")` — green ✓
- read_holding / read_input возвращают `.registers` — green ✓

## Integration check (§0.11)
- Новых routes/keys/env/cols/migrations — **нет**. Шаг = async wrapper в новом модуле `plugins/modbus/client.py`.
- Нет Redis/Kafka/broker — чистый TCP через pymodbus (ADR-COL-001). Grep по `redis|kafka|broker` в модуле — чисто.
- Нет write FC в трафике (AC-B2-11) — статический guard (grep `write_|FC0[56]|FC1[56]`) + 2 теста на отсутствие методов.
- `decoder.py` (s06) не импортируется здесь — декодирование будет в s08 connector (YAGNI).
- §0.11 counterpart не требуется (нет key/env/event/col/route на этом шаге).
