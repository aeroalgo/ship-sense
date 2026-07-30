# [T-001 | s17 | emulator-opcua-server] IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s17-emulator-opcua-server.md](../../plan/decompose-v1-p1-collector/s17-emulator-opcua-server.md)  
**Дата:** 2026-07-27  
**Уровень:** L2 по atomic step; universal architecture задана CR-COL-03  
**Статус:** done

Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s17-emulator-opcua-server.md`

## Сделано

- Создан `OpcUaServerAdapter` в `apps/edge/emulator/src/emulator/protocols/opcua_server.py`.
- Adapter принимает один общий `TagGenerator` через конструктор или `bind()`; отдельной physics-логики и второго snapshot provider нет.
- Реализован lifecycle `start(host, port)` / `stop()`; `port=0` выбирает ephemeral TCP port, фактически используемый asyncua endpoint.
- Профильные `native_ids.opcua` публикуются как OPC UA Variable nodes под объектом `Emulator`; `node_ids` отдаёт опубликованные NodeIds.
- Значения первичного snapshot устанавливаются при старте, затем ticker с частотой `profile.tick_hz` обновляет все опубликованные nodes из следующего общего snapshot.
- Все variable nodes помечаются read-only через `set_read_only()`, поэтому collector может browse/read/subscribe, но не получает client write access.
- Adapter экспортирован через `emulator.protocols`.

## Файлы

- `apps/edge/emulator/src/emulator/protocols/opcua_server.py` (создание)
- `apps/edge/emulator/src/emulator/protocols/__init__.py` (экспорт)
- `apps/edge/emulator/tests/test_opcua_server.py` (создание)

## TDD

- red: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_opcua_server.py` → `ModuleNotFoundError: No module named 'emulator.protocols.opcua_server'` до реализации.
- green: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_opcua_server.py` → **3 passed in 6.77s**.
- targeted regression: `PYTHONPATH=apps/edge/emulator/src .venv/bin/python -m pytest -q apps/edge/emulator/tests/test_opcua_server.py apps/edge/emulator/tests/test_modbus_server.py apps/edge/emulator/tests/test_determinism.py` → **10 passed in 8.23s**.
- Полный collector/emulator suite не запускался: полный regression относится к BACK QA.
- `ruff` не запускался: executable отсутствует в `.venv`; IDE diagnostics после исправления не показывают прежний unused-import в OPC UA adapter.

## Integration check (§0.11)

- [x] profile `native_ids.opcua` ↔ server NodeId map: каждый профильный OPC UA ID получает одну Variable node.
- [x] collector browse counterpart: nodes находятся в Objects → Emulator и имеют стабильные NodeIds из профиля.
- [x] collector subscription counterpart: asyncua client subscription получает data-change notifications при snapshot ticks.
- [x] snapshot contract: adapter потребляет `TagGenerator.tick()` и не содержит собственной physics-логики.
- [x] read-only contract: access level не содержит `CurrentWrite`; тест проверяет отсутствие client write access.
- [x] lifecycle contract: bind до старта обязателен, bind во время работы запрещён, `stop()` идемпотентен.
- [x] port contract: endpoint документирован свойством `endpoint`, runtime port доступен через `adapter.port`; `port=0` покрыт тестами.
- [ ] Docker service `emulator` health/port documentation — относится к s23 Docker Compose; s17 проверяет runtime port contract.

## Code review

- Reviewer проверил server adapter и тесты.
- Найденная проблема с необработанными фоновыми `write_value` task устранена: ticker теперь `await asyncio.gather(...)` для всех записей snapshot.
- Остальные замечания reviewer относятся к низкоуровневой race window выбора ephemeral port и defensive cleanup теста; targeted suite воспроизводимо зелёный, отдельные изменения для них не добавлялись.
