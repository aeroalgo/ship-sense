# [T-001 | s21 | integration-dual-source] IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s21-integration-dual-source.md](../../plan/decompose-v1-p1-collector/s21-integration-dual-source.md)  
**Дата:** 2026-07-27  
**Уровень:** L2 по atomic integration test step  
**Статус:** done

## Сделано

- Добавлен `apps/edge/collector/tests/integration/test_dual_source_isolation.py` — live end-to-end harness по образцу s19/s20 (conftest-эмуляторы), но проверяющий **изоляцию двух источников под `SourceSupervisor`** поверх общей `raw_queue`.
- Dual protocol: **A = OPC UA** (`OpcUaConnector`, s10 + `OpcUaServerAdapter`, s17), **B = Modbus** (`ModbusTcpConnector`, s08 + `ModbusServerAdapter`, s16).
- Сценарий покрывает оба checkpoint step-файла:
  1. Оба source живы → ждём по ≥1 сэмплу от каждого в общей очереди.
  2. **Kill A**: `await opcua_emu.stop()` рвёт транспорт OPC UA. Supervisor A уходит в reconnect/backoff (без падения процесса).
  3. После kill **B продолжает стримить** (drain очереди за 1с окно → сэмплы `source_id=aps_main` присутствуют → изоляция не нарушена, AC-B1-04).
  4. `HealthAggregator.update_source(healthcheck())` до и после kill → snapshot покрывает **оба** `source_id` (`aps_main_opcua`, `aps_main`) — агрегированный health отражает оба источника (AC-CFG-01).
- В отличие от unit-теста `test_dual_source_isolation_killing_a_keeps_b_pushing` (s04, `_FakeConnector`), здесь — реальные транспорты, реальные плагины, реальный разрыв соединения стопом эмулятора. Доказывает, что изоляция из ADR-COL-002 (Task-per-source) держится не только на фейках.

## Файлы

- `apps/edge/collector/tests/integration/test_dual_source_isolation.py` (создание)

## Реализация (prod-код)

- **Не потребовалась.** `code_surface: test` — шаг создаёт только тест. Существующая реализация (s04 supervisor + s08/s10 connectors + s14 `HealthAggregator` + s16/s17 эмуляторы) уже обеспечивает проверяемое поведение. Прод-багов, как в s20, этот тест не вскрыл.

## TDD

- red (1-я итерация): `IndexError: list index out of range` — у `ModbusServerAdapter` оставался пустой блок input-registers, т.к. профиль был без boolean-сигнала. Причина — профиль не совпадал с каноническим из `conftest.py::modbus_integration`.
- fix: профиль Modbus выровнен с conftest (добавлен `STATUS` boolean на `41000`).
- red (2-я итерация): `FileNotFoundError: …/apps/apps/edge/collector/maps/…` — `Path(__file__).parents[4]` для файла в `tests/integration/` даёт не корень репо, а `apps/` (conftest лежит на уровень выше, в `tests/`, поэтому у него `parents[4]` = корень).
- fix: `parents[5]` для этого файла.
- green: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src pytest -q apps/edge/collector/tests/integration/test_dual_source_isolation.py` → **1 passed in 3.33s**.
- Regression: integration/ + `test_supervisor.py` → **19 passed in 6.05s**.
- Полный collector/emulator suite не запускался: полный regression относится к BACK QA.

## Integration check (§0.11)

- [x] `OpcUaServerAdapter.start(host, port=0)` ↔ `OpcUaConnector(endpoint=…)` (A).
- [x] `ModbusServerAdapter.start(host, port=0)` ↔ `AsyncModbusClient(host, port=…)` (B).
- [x] profile `native_ids.opcua` (`ns=2;s=AI4104`) ↔ `stub_aps_main_nodes.yaml` `node_id` (A подписан на 1 тег).
- [x] profile `native_ids.modbus` (`40107`) ↔ `stub_aps_main.yaml` `native_id` (B подписан на 1 тег).
- [x] Общий `asyncio.Queue[RawSample]` для двух `SourceSupervisor` (AC-B1-04, ADR-COL-002).
- [x] `RestartPolicy(initial=0.01, max=0.05, jitter=False)` — короткий backoff, чтобы reconnect-цикл A не мешал таймингам теста.
- [x] `HealthAggregator.update_source(connector.healthcheck())` для обоих → snapshot `sources` покрывает `{aps_main_opcua, aps_main}` до и после kill (AC-CFG-01).
- [x] `opcua_emu.stop()` рвёт транспорт → supervisor A ловит разрыв через `Subscription.cancel_event` → backoff, не crash.
- [x] targeted pytest green.

## Чекпоинт верификации (step)

- [x] source A down → B sample_rate > 0 (drain за 1с окно содержит `source_id=aps_main`).
- [x] агрегированный health отражает оба source_id (snapshot до и после kill).

## Code review

- Тест только; прод-код не менялся. Read-only review scope ограничен harness-файлом. Перед BACK QA.
