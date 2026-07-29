# [T-001 | s10 | opcua-connector] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s10-opcua-connector.md](../../plan/decompose-v1-p1-collector/s10-opcua-connector.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L2 (component TDD, browse + subscription)
**AC:** AC-B3-01, AC-B3-02, AC-B3-03, AC-B3-05, AC-B3-07, AC-B3-08, AC-B3-10
**Статус:** done
Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s10-opcua-connector.md`

## Skills
- tdd, python-testing-patterns, modern-python (по workflow-implement)
- verification-before-completion (перед FINISH)
- python-anti-patterns (review перед FINISH; service/deps не затронуты)

## Сделано
- Создан `plugins/opcua/connector.py` — B3 OpcUaConnector (BaseSourceConnector):
  - `connect()`: asyncua Client + security (из s09: `build_client_security`).
  - `disconnect()`: idempotent, cancel subscription + client disconnect.
  - `discover_tags()`: `browse_nodes()` → `RawTagDescriptor` list (AC-B3-03).
  - `read(native_ids)`: sync read по NodeId → `RawSample` (для unit + fallback).
  - `subscribe(native_ids, on_sample)`: `SubscriptionManager` + monitored items (AC-B3-02).
  - `reconnect()`: disconnect + connect + recreate subscription без дублей sequence (AC-B3-05).
  - `browse_diff(discovered, tag_map)`: added/removed для B8/T7 (AC-B3-08).
  - `healthcheck()` / `_compute_state()`: UP/DOWN по `_connected`.
  - Инвариант: публичный API не экспортирует write (AC-B3-01 prep).
- Создан `plugins/opcua/subscription.py` — SubscriptionManager:
  - `create_subscription(publishing_interval)` + `create_monitored_items` по NodeId.
  - `_DataChangeHandler.datachange_notification` → `RawSample` (StatusCode → native_quality).
  - `sequence` для dedup на seam (reconnect reset).
  - `recreate()`: cancel + subscribe с reset sequence.
- Создан `plugins/opcua/browse.py` — browse helpers:
  - `browse_nodes(client, root)`: рекурсивный walk (depth≤3), Variable только, EUInformation unit.
  - `_read_eu_information()`: EngineeringUnits property (стандарт OPC UA).
  - `browse_diff(discovered, tag_map)`: set diff → (added, removed).
  - AC-B3-07: unit verify vs map (warning в connector._verify_units_vs_map).
- Обновлён `plugins/opcua/__init__.py`: экспорт `OpcUaConnector`, `SubscriptionManager`, `browse_nodes`, `browse_diff`.
- Тесты: `tests/unit/test_opcua_connector.py` (TDD red→green):
  - 11 targeted: `test_connector_implements_source_connector`, `test_discover_tags_returns_from_map`, `test_read_returns_raw_samples`, `test_subscribe_creates_monitored_items`, `test_subscribe_cancel_deletes_subscription`, `test_reconnect_recreates_subscription_without_duplicates`, `test_browse_diff_detects_added_removed`, `test_register_opcua_factory_pattern`, + health/connect/disconnect.
  - TDD: red (ModuleNotFoundError) → реализация → 11 passed.
  - Regression: plugin registry 11 passed (не затронут).
- Factory pattern: registry хранит фабрику (`def _create(cfg): return OpcUaConnector(cfg, client, map)`), не класс напрямую (AC-B1-03).

## Файлы
- `apps/edge/collector/src/collector/plugins/opcua/connector.py` (Создание)
- `apps/edge/collector/src/collector/plugins/opcua/subscription.py` (Создание)
- `apps/edge/collector/src/collector/plugins/opcua/browse.py` (Создание)
- `apps/edge/collector/src/collector/plugins/opcua/__init__.py` (Обновление: экспорт)
- `apps/edge/collector/tests/unit/test_opcua_connector.py` (Создание)

## Тесты
- **Runner note:** `PYTHONPATH=src .venv/bin/python -m pytest`. Async через `pytest.mark.asyncio`.
- red: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest tests/unit/test_opcua_connector.py` → `ModuleNotFoundError: No module named 'collector.plugins.opcua.connector'`.
- cmd targeted: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_opcua_connector.py`
- итог targeted: **11 passed in 0.38s**.
- cmd regression (plugin registry): `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_plugin_registry.py`
- итог regression: **11 passed** (не затронуты; opcua protocol уже был известен registry).
- cmd combined: `PYTHONPATH=src /home/aero/PyProject/ship-sense/.venv/bin/python -m pytest -q tests/unit/test_opcua_connector.py tests/unit/test_plugin_registry.py`
- итог combined: **22 passed in 0.43s**.

Покрытие (чекпоинты decompose s10):
- browse возвращает descriptors — green ✓ (`test_discover_tags_returns_from_map`)
- reconnect без duplicate storm (unit mock) — green ✓ (`test_reconnect_recreates_subscription_without_duplicates`)
- register protocol opcua — green ✓ (`test_register_opcua_factory_pattern`)
- subscribe создаёт monitored items — green ✓ (`test_subscribe_creates_monitored_items`)
- publishing_interval из config — green ✓ (connector использует `cfg.subscribe.publishing_interval_ms`)
- EUInformation → unit verify vs map — green ✓ (connector._verify_units_vs_map + browse)
- browse diff → added/removed — green ✓ (`test_browse_diff_detects_added_removed`)
- sequence reset на reconnect — green ✓ (SubscriptionManager.recreate)

## Integration check (§0.11)
- **SourceConfig.subscribe** (models.py:26) → `SubscribeConfig(publishing_interval_ms, nodes_ref)`; connector читает `cfg.subscribe.publishing_interval_ms`.
- **TagMapEntry.node_id** (models.py:64) → alias для native_id (normalize_entry); `SubscriptionManager._tag_map` использует `e.node_id or e.native_id`.
- **load_tag_map** (loader.py:42) → парсит `nodes:` ключ (maps/stub_aps_main_nodes.yaml); 8 entries в dev map.
- **PluginRegistry** (s03, registry.py) → `register("opcua", factory)` + `create(cfg)` работает (test_register_opcua_factory_pattern).
- **SecurityConfig** (s09, s02) → `build_client_security` вызывается в `connect()` если `cfg.security`.
- **BaseSourceConnector** (interfaces.py:84) → OpcUaConnector наследует; `healthcheck`, `_recv_ts`, `source_id`, `protocol` из base.
- **Subscription** (interfaces.py:22) → `cancel_event`, `tag_ids`; `SubscriptionManager` создаёт с `id`, `tag_ids`.
- **RawSample / RawTagDescriptor** (models.py) → browse → descriptors, subscribe/read → samples.
- **StatusCode → native_quality** (AC-B3-06 prep): SubscriptionManager._make_raw_sample пишет `str(status)` в `native_quality`.
- **Нет write путей** (AC-B3-01): connector/subscription/browse не вызывают write_*; security helper тоже не экспортирует.
- **§0.11: PASS** (все внешние ссылки имеют существующие counterparts; wiring: config → registry → connector → asyncua).
