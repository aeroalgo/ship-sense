# BACK IMPLEMENT s24 — Demo third-party stub plugin (AC-B1-08)

**Plan ID:** v1-p1-collector
**Decompose step:** [s24-stub-plugin-demo.md](../../plan/decompose-v1-p1-collector/s24-stub-plugin-demo.md)
**AC:** AC-B1-08
**Level:** L2 (service, targeted TDD)
**code_surface:** service
**Дата:** 2026-07-27
**needs_creative:** no
**Статус:** done ✅

## Цель

Demo third-party stub plugin: доказать, что сторонний плагин источника
регистрируется через **import side-effect** без правки core `PluginRegistry`
(только `register` call). Плагин генерирует синтетические `RawSample`.

## Consumes / Produces

- **Consumes:** s03 — `PluginRegistry`, `BaseSourceConnector`, `SourceConnector`
- **Produces:** `plugins/stub/` — отдельный пакет-коннектор

## Контракт (lean)

- class: `StubConnector(BaseSourceConnector)` — synthetic RawSample
- register: protocol `stub` via `__init__.py` import side-effect

## Файлы

| Файл | Действие |
| :--- | :--- |
| `apps/edge/collector/src/collector/plugins/stub/__init__.py` | Создание |
| `apps/edge/collector/src/collector/plugins/stub/connector.py` | Создание |
| `apps/edge/collector/tests/unit/test_stub_plugin.py` | Создание |

## Реализация

`stub/connector.py`:
- `StubConnector(BaseSourceConnector)`, `__init__` → `super().__init__(config)`, `_connected=False`.
- `connect()` / `disconnect()` — idempotent, переводят `_connected`.
- `discover_tags()` → фиксированный список `RawTagDescriptor` (`ai4101`, `di0101`).
- `read(native_ids)` → по одному `RawSample` на native_id; `raw_value=0.0`,
  `native_quality="stub.synthetic"`, `recv_ts=source_ts=_recv_ts()`,
  `sequence` из module-level `itertools.count(1)`.
- `subscribe(native_ids, on_sample)` → `asyncio.create_task` пушит по одному
  sample на id, затем `cancel_event.set()`; возвращает `Subscription`.
- `_compute_state` наследуется (UP).

`stub/__init__.py`:
- import side-effect: `PluginRegistry.register("stub", StubConnector)`.
- `__all__ = ["STUB_PROTOCOL", "StubConnector"]`.

## TDD

**RED → GREEN** (vertical slices, поведение через public API):

| Тест | Поведение |
| :--- | :--- |
| `test_stub_protocol_registered_on_import` | импорт `collector.plugins.stub` регистрирует protocol `stub`; `registry.create` → StubConnector с правильным `source_id`/`protocol` |
| `test_stub_connector_satisfies_protocol` | `isinstance(connector, SourceConnector)` и `BaseSourceConnector` |
| `test_stub_connect_and_read_yields_synthetic_samples` | `read` → по одному RawSample на native_id; `source_id`, aware `recv_ts` |
| `test_stub_subscribe_pushes_synthetic_samples` | `subscribe` → `on_sample` вызван для каждого native_id (timeout 2s) |
| `test_stub_discover_tags_returns_descriptors` | `discover_tags` → непустой список с `native_id` |
| `test_stub_healthcheck_is_up` | `healthcheck` → state `up` |
| `test_stub_disconnect_is_idempotent` | двойной `disconnect` не падает |
| `test_stub_read_recv_ts_is_aware_utc` | `recv_ts` aware |

### Runner / окружение

- pytest-asyncio отсутствует → async через `asyncio.run` (канон проекта).
- PYTHONPATH (нет editable install): `apps/edge/collector/src:apps/edge/emulator/src`
  (emulator нужен для top-level `tests/conftest.py`).

### Результаты

- **red:** `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src .venv/bin/python -m pytest apps/edge/collector/tests/unit/test_stub_plugin.py -q` → `ModuleNotFoundError: No module named 'collector.plugins.stub'` (ERROR).
- **green:** та же команда → **8 passed in 0.02s**.
- **targeted regression** (registry + stub): `… test_plugin_registry.py test_stub_plugin.py` → **19 passed**.

## Чекпоинты верификации (decompose step)

| Чекпоинт | Доказательство |
| :--- | :--- |
| sources.yaml protocol `stub` работает | `SourceConfig(protocol="stub")` валиден (`extra="allow"` в модели); `registry.create` → StubConnector — `test_stub_protocol_registered_on_import`. `sources.dev.yaml` **не** правлен (YAGNI: compose-smoke файл — не носитель demo-плагина). |
| ядро `registry.py` без `if stub` | `grep -niE "stub" registry.py` → **CLEAN**. Регистрация — только `register` call в `stub/__init__.py` (side-effect). |

## §0.11 integration verification

Плагин-демо без route/key/env/event/col/migration → counterpart-проверка
тривиальна. Новый protocol `stub` потребляется только через `PluginRegistry.create`
(контракт s03, неизменён). Контрpart-массива нет.

## Anti-patterns (service)

- [x] Нет bare `except Exception: pass` (исключений нет).
- [x] Нет blocking sync I/O в async (только asyncio primitives).
- [x] `disconnect` идемпотентен (тест).
- [x] Нет module-level service singleton (registry — class-level по канону s03).
- [x] `register` side-effect один раз на import.

## FINISH

- **Done:** demo stub plugin `plugins/stub/` + 8 unit-тестов; import side-effect регистрация protocol `stub` без правки core.
- **Files:** `apps/edge/collector/src/collector/plugins/stub/{__init__,connector}.py`, `apps/edge/collector/tests/unit/test_stub_plugin.py`.
- **Tests:** stub plugin — **8 passed**; targeted regression registry+stub — **19 passed**.
- **code_changed:** yes.
- **Next:** `BACK QA` (новый чат) — полный collector regression (вкл. stub) + edge-stack compose smoke (T-001).
- **New chat:** yes.
