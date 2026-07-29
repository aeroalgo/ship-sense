# [T-001 | s19 | integration-modbus] IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s19-integration-modbus.md](../../plan/decompose-v1-p1-collector/s19-integration-modbus.md)  
**Дата:** 2026-07-27  
**Уровень:** L2 по atomic integration test step  
**Статус:** done

## Сделано

- Добавлен live integration harness `apps/edge/collector/tests/conftest.py`.
- Fixture поднимает `ModbusServerAdapter` на ephemeral TCP-порту с минимальным profile-driven `TagGenerator`.
- Fixture создаёт реальный `AsyncModbusClient` и `ModbusTcpConnector` с production tag map subset.
- Добавлен `apps/edge/collector/tests/integration/test_modbus_emulator.py`.
- Тест проверяет end-to-end путь emulator → FC03 client → B2 connector → canonical `TelemetrySample` callback, mapping `TAI4101`/`TAI4104`, numeric value и `Quality.GOOD` для валидных samples.
- Исправлен connector polling: количество регистров и decode offsets учитывают двухрегистровые `float32`/`int32`/`uint32` entries.

## Файлы

- `apps/edge/collector/tests/conftest.py`
- `apps/edge/collector/tests/integration/test_modbus_emulator.py`
- `apps/edge/collector/src/collector/plugins/modbus/connector.py`

## TDD

- red: новый integration test сначала падал с отсутствующей fixture `modbus_integration`.
- green: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src pytest -q apps/edge/collector/tests/integration/test_modbus_emulator.py` → **1 passed in 0.34s**.
- Полный collector/emulator suite не запускался: полный regression относится к BACK QA.

## Integration check (§0.11)

- [x] emulator `ModbusServerAdapter.start(host, port=0)` ↔ fixture передаёт фактический ephemeral `adapter.port` в collector client.
- [x] profile `native_ids.modbus` ↔ server register map ↔ collector `TagMapEntry.native_id`.
- [x] FC03 holding registers ↔ connector `_read_registers`/poll group.
- [x] float32 width (2 registers) ↔ server encoding и connector decode offset.
- [x] connector `RawSample.native_quality="good"` ↔ integration canonical callback maps to `Quality.GOOD`.
- [x] `ModbusTcpConnector.disconnect()` ↔ server fixture teardown.
- [x] targeted pytest green.

## Code review

- Read-only review requested before BACK QA; scope intentionally ограничен integration harness и исправлением register-width bug.
