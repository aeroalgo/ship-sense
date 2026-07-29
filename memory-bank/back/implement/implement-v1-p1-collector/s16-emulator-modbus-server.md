# [T-001 | s16 | emulator-modbus-server] IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s16-emulator-modbus-server.md](../../plan/decompose-v1-p1-collector/s16-emulator-modbus-server.md)  
**Дата:** 2026-07-27  
**Уровень:** L2 по atomic step; universal architecture задана CR-COL-03  
**Статус:** done

Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s16-emulator-modbus-server.md`

## Сделано

- Создан `ModbusServerAdapter` в `apps/edge/emulator/src/emulator/protocols/modbus_server.py`.
- Adapter принимает один общий `TagGenerator` через конструктор или `bind()` и не содержит physics/transport logic в модели тегов.
- Реализован lifecycle `start(host, port)` / `stop()`; `port=0` поддерживает ephemeral TCP port для тестов.
- Созданы holding и input register blocks по `native_ids.modbus`: `40xxx` → holding/FC03, остальные `41xxx` → input/FC04; адрес использует offset после `40`/`41`, совместимый с collector `_parse_address()`.
- Значения snapshot кодируются в Modbus registers для `float32`, `int16`/`uint16`, `int32`/`uint32`, `boolean` и `string`.
- Ticker обновляет register values примерно раз в секунду по `profile.tick_hz`.
- Register entries read-only; write requests возвращают Modbus error.
- Экспортирован adapter через `emulator.protocols`.

## Файлы

- `apps/edge/emulator/src/emulator/protocols/__init__.py` (создание)
- `apps/edge/emulator/src/emulator/protocols/modbus_server.py` (создание)
- `apps/edge/emulator/tests/test_modbus_server.py` (создание)

## TDD

- red: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_modbus_server.py` → `ModuleNotFoundError: No module named 'emulator.protocols'`.
- green: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_modbus_server.py` → **2 passed in 0.26s**.
- targeted regression: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_modbus_server.py apps/edge/emulator/tests/test_determinism.py` → **7 passed in 1.23s**.
- Полный collector/emulator suite не запускался: полный regression относится к BACK QA.
- `ruff` не запускался: executable отсутствует в `.venv`; IDE diagnostics после форматирования новых файлов не показывают прежние длинные строки/whitespace diagnostics.

## Integration check

- [x] protocol-neutral snapshot: adapter потребляет `TagGenerator.tick()` и не меняет physics model.
- [x] Modbus native ID ↔ register address counterpart согласован с collector `apps/edge/collector/src/collector/plugins/modbus/connector.py::_parse_address()`.
- [x] FC03/FC04 read path покрыт реальным pymodbus TCP client.
- [x] read-only invariant покрыт write request test.
- [ ] Docker service `emulator` health/port documentation — относится к s23 Docker Compose; s16 проверяет runtime port contract.
