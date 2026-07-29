# [T-001 | s08 | modbus-connector] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s08-modbus-connector.md](../../plan/decompose-v1-p1-collector/s08-modbus-connector.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L2 (poll scheduler + connector, TDD + creative)
**AC:** AC-B2-05, AC-B2-06, AC-B2-10, AC-B1-03, AC-B1-11
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s08-modbus-connector.md`

## Skills
- tdd, python-testing-patterns, modern-python (по workflow-implement)
- verification-before-completion (перед FINISH)

## Сделано
- Создан `plugins/modbus/poll_scheduler.py` — `PollScheduler` + runtime `PollGroup`:
  - `build_groups(tag_map, *, max_gap=0, max_regs=100, default_hz=1.0, explicit_groups=None) → list[PollGroup]`
  - Разделение по FC (3/4), сортировка по address, greedy merge (gap ≤ max_gap), split по max_regs.
  - hz группы = min(tag hz или default).
  - explicit_groups: если заданы с native_ids — вернуть как есть (validate); остальные теги → auto в "default".
  - Соответствует CR-COL-02 (greedy + explicit passthrough).
- Создан `plugins/modbus/connector.py` — `ModbusTcpConnector(BaseSourceConnector)`:
  - `__init__(config: SourceConfig, client: AsyncModbusClient, tag_map: list[TagMapEntry])`
  - `connect()` / `disconnect()` — делегируют клиенту; disconnect также отменяет poll tasks.
  - `discover_tags()` — из локальной карты → list[RawTagDescriptor].
  - `read(native_ids)` → list[RawSample] (с decode float32/int/bit/boolean/string).
  - `subscribe(native_ids, on_sample)`:
    - Строит группы через PollScheduler.
    - На каждую группу — `asyncio.Task` (`_poll_group`).
    - `_poll_group`: while not cancelled: read_holding/read_input по группе (contiguous), decode per tag, on_sample, sleep(1/hz).
    - На `ModbusClientError` / `ModbusTimeoutError` на группе — все теги группы → RawSample с native_quality=error, quality=BAD (Modbus PDU атомарен).
  - Diag mode (AC-B2-10): если `MODBUS_DEBUG=1` (или config) → `collector.modbus.diag` логирует `raw=...`.
  - Использует: decoder (s06), AsyncModbusClient (s07).
- Тесты: `tests/unit/test_modbus_connector.py` (TDD red→green):
  - 6 тестов PollScheduler (contiguous merge, gap split, max_regs split, hz=min, explicit passthrough, fc split).
  - 11 тестов connector (implements SourceConnector, source_id/protocol, connect/disconnect delegate, discover_tags, read, subscribe creates tasks, cancel stops, group error → bad samples, diag smoke, factory pattern для PluginRegistry).
- TDD: red (ModuleNotFoundError на import connector) → реализация → 17 passed targeted.

## Файлы
- `apps/edge/collector/src/collector/plugins/modbus/poll_scheduler.py` (Создание)
- `apps/edge/collector/src/collector/plugins/modbus/connector.py` (Создание)
- `apps/edge/collector/tests/unit/test_modbus_connector.py` (Создание)

## Тесты
- **Runner note:** `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m pytest`. Async через `pytest.mark.asyncio`.
- red: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_modbus_connector.py` → `ModuleNotFoundError: No module named 'collector.plugins.modbus.connector'`.
- cmd targeted: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_modbus_connector.py`
- итог targeted: **17 passed in 0.17s**.
- cmd regression: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/`
- итог regression: **126 passed in 0.52s** (s01–s07 ~109 + 17 s08).

Покрытие (чекпоинты decompose s08):
- группы не превышают max_regs (AC-B2-05) — green ✓ (`test_build_groups_max_regs_split`)
- gap соблюдён — green ✓ (`test_build_groups_gap_split`)
- subscribe эмулирует poll (AC-B1-11) — green ✓ (subscribe создаёт tasks; cancel останавливает)
- PluginRegistry.create("modbus_tcp") (AC-B1-03) — green ✓ (`test_register_modbus_tcp_factory_pattern`)
- error на группе → bad quality (AC-B2-08/09) — green ✓ (`test_poll_group_error_yields_bad_quality`)
- diag mode (AC-B2-10) — smoke ✓ (`test_diag_mode_logs_raw_and_decoded`)

## Integration check (§0.11)
- Новых routes/keys/env/cols/migrations — **нет** (кроме MODBUS_DEBUG для AC-B2-10, задокументировано в creative CR-COL-02).
- Counterparts:
  - `AsyncModbusClient` (s07) → импортируется и делегируется в connector.
  - `decode_float32` / `decode_int` / `extract_bit` (s06) → импортируются и используются в `_decode`.
  - `BaseSourceConnector` / `SourceConnector` (s03) → наследование + реализация.
  - `PollGroup` (config/models), `TagMapEntry`, `RawSample`, `RawTagDescriptor` (s01/s02) → используются напрямую.
  - Нет Redis/Kafka/broker — чистый TCP (ADR-COL-001).
  - Нет write FC (AC-B2-11) — подтверждено в s07 (grep + тесты); s08 только read.
- §0.11: **PASS** (все внешние ссылки имеют существующие counterparts).
