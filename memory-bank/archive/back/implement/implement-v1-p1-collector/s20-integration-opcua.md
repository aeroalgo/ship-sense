# [T-001 | s20 | integration-opcua] IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s20-integration-opcua.md](../../plan/decompose-v1-p1-collector/s20-integration-opcua.md)  
**Дата:** 2026-07-27  
**Уровень:** L2 по atomic integration test step  
**Статус:** done

## Сделано

- Добавлен `apps/edge/collector/tests/integration/test_opcua_emulator.py` — live end-to-end harness по образцу s19 (Modbus).
- В `apps/edge/collector/tests/conftest.py` добавлен `OpcuaIntegrationSink` + fixture `opcua_integration`:
  - поднимает `OpcUaServerAdapter` (s17) на ephemeral порту с profile-driven `TagGenerator` (2 сигнала: `ns=2;s=AI4101`, `ns=2;s=AI4104`);
  - создаёт реальный `OpcUaConnector` (s10) с production tag map `stub_aps_main_nodes.yaml`;
  - sink маппит `native_quality="opcua.Good"` → `Quality.GOOD`, node_id → `TAI4101`/`TAI4104`.
- Integration-тест вскрыл **три прод-бага** в B3 subscription path (s17), которые unit-тесты на MagicMock не ловили. Исправлены причины, не fallback:
  1. `SubscriptionManager.subscribe` вызывал `create_monitored_items(nodes)` с raw `Node` вместо `MonitoredItemCreateRequest` → `AttributeError: 'Node' object has no attribute 'RequestedParameters'`. Заменён на convenience `subscribe_data_change(nodes)`, который сам строит request.
  2. `_make_raw_sample` создавал `RawSample(recv_ts=None)` — невалидно для обязательного `datetime`. Поставлен реальный `datetime.now(UTC)` (connector всё равно перетирает своим `_recv_ts()`).
  3. `_DataChangeHandler` строил `node_id = str(node.nodeid)` → repr NodeId, не совпадающий с key в `_tag_map` → sample терялся. Заменён на `node.nodeid.to_string()`.
- Обновлены моки в `apps/edge/collector/tests/unit/test_opcua_connector.py`: `mock_sub.create_monitored_items` → `subscribe_data_change` (4 места), чтобы совпадало с прод-API.

## Файлы

- `apps/edge/collector/tests/integration/test_opcua_emulator.py` (создание)
- `apps/edge/collector/tests/conftest.py` (fixture + sink)
- `apps/edge/collector/src/collector/plugins/opcua/subscription.py` (3 баг-фикса)
- `apps/edge/collector/tests/unit/test_opcua_connector.py` (sync моков)

## TDD

- red: новый integration test падал по каскаду реальных ошибок B3 (`create_monitored_items`, `recv_ts=None`, `str(node.nodeid)`).
- green: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src pytest -q apps/edge/collector/tests/integration/test_opcua_emulator.py` → **1 passed in 2.36s**.
- Regression check: targeted OPC UA suite `test_opcua_connector.py` + `test_opcua_server.py` + integration → **15 passed in 8.29s**.
- Полный collector/emulator suite не запускался: полный regression относится к BACK QA.

## Integration check (§0.11)

- [x] emulator `OpcUaServerAdapter.start(host, port=0)` ↔ fixture передаёт `emulator.endpoint` в collector client.
- [x] profile `native_ids.opcua` (`ns=2;s=AI4101`, `ns=2;s=AI4104`) ↔ server variable nodes ↔ collector `TagMapEntry.node_id`.
- [x] monitored items → data change notification → `RawSample` → canonical `TelemetrySample`.
- [x] `StatusCode.good` → `native_quality="opcua.Good"` → `Quality.GOOD`.
- [x] `OpcUaConnector.subscribe` ↔ `SubscriptionManager.subscribe` ↔ `subscribe_data_change(nodes)` (AC-B3-02).
- [x] `OpcUaConnector.disconnect()` ↔ server fixture teardown.
- [x] targeted pytest green.

## Чекпоинт верификации (step)

- [x] monitored items → samples
- [x] StatusCode good → Quality.good

## Code review

- Read-only review requested before BACK QA; scope ограничен integration harness + 3 bug-фикса B3 subscription, вскрытых этим тестом.
