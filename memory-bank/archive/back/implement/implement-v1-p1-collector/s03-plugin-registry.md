# [T-001 | s03 | plugin-registry] IMPLEMENT

**Plan ID:** v1-p1-collector
**Decompose step:** [s03-plugin-registry.md](../../plan/decompose-v1-p1-collector/s03-plugin-registry.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26
**Уровень:** L2
**Статус:** done

Путь артефакта (epic): `memory-bank/back/implement/implement-v1-p1-collector/s03-plugin-registry.md`

## Skills

- tdd, modern-python, python-testing-patterns (по workflow-implement)
- verification-before-completion (перед FINISH)

## Сделано

- Создан `domain/interfaces.py`:
  - `Subscription` — frozen dataclass (`id`, `tag_ids`, `cancel_event: asyncio.Event`), метод `async cancel()`.
  - `OnSampleCallback = Callable[[RawSample], Awaitable[None]]`.
  - `SourceConnector` — `@runtime_checkable Protocol` (AC-B1-01): `source_id`, `protocol`; `connect`, `discover_tags`, `read`, `subscribe`, `healthcheck`, `disconnect`. Контракт 1:1 с планом §8.
  - `CanonicalSink` — `Protocol` (plan §21): `write_sample(TelemetrySample)`, `write_event(Event)`.
  - `BaseSourceConnector(ABC)` — helpers: `_recv_ts()` (UTC-aware), `_compute_state()` (default `UP`), `healthcheck()` собирает `HealthStatus`; abstractmethods `connect/discover_tags/read/subscribe/disconnect`.
- Создан `plugins/registry.py` — `PluginRegistry` (AC-B1-02): `register(protocol, cls)` (class-level `_plugins`), `create(config) → SourceConnector`; `unknown protocol → ConfigError`.
- Создан `plugins/__init__.py` (пакет; пустой — превентативная регистрация коннекторов отсутствует: `modbus_tcp`/`opcua` будут `register` в entrypoint шагов s08/s10, см. plan §13.1/§13.2).
- `SourceConfig` импортируется из канонического `collector.config.models` (s02), НЕ дублируется.
- `ConfigError` переиспользован из `collector.domain.errors` (s01).

## Файлы

- `apps/edge/collector/src/collector/domain/interfaces.py` (Создание)
- `apps/edge/collector/src/collector/plugins/__init__.py` (Создание)
- `apps/edge/collector/src/collector/plugins/registry.py` (Создание)
- `apps/edge/collector/tests/unit/test_plugin_registry.py` (Создание)

## Тесты

- red: `PYTHONPATH=apps/edge/collector/src python3 -m pytest -q apps/edge/collector/tests/unit/test_plugin_registry.py` → `ModuleNotFoundError: No module named 'collector.domain.interfaces'`.
- cmd targeted: `PYTHONPATH=apps/edge/collector/src python3 -m pytest -q apps/edge/collector/tests/unit/test_plugin_registry.py`
- итог targeted: `11 passed in 0.09s`.
- cmd regression: `PYTHONPATH=apps/edge/collector/src python3 -m pytest -q apps/edge/collector/tests/unit`
- итог regression: `24 passed in 0.11s` (s01/s02 чисто).

Покрытие targeted:
- `SourceConnector` runtime_checkable (FakeConnector проходит `isinstance`).
- `register('modbus_tcp')` → `create` → `source_id`/`protocol`.
- `register('opcua')` → `create`.
- `create('canbus')` unknown → `ConfigError`.
- registry остаётся usable после unknown protocol (raise не ломает `_plugins`).
- `BaseSourceConnector.healthcheck()` → `HealthStatus` с `state=UP`, `reconnect_count=0`.
- `Subscription.cancel()` → `cancel_event.is_set()`.
- `Subscription` frozen (присваивание поля → raise).
- `CanonicalSink` — `typing.Protocol`.
- `OnSampleCallback` — origin `collections.abc.Callable`.
- `_recv_ts()` — tz-aware, `<= now`.

## Integration check

- [x] N/A — слой интерфейсов и фабрики: нет storage keys / env vars / DB cols / events-handlers (нет counterpart для wire). `unknown protocol → ConfigError` покрыт тестом.
- [x] `ConfigError` — общий доменный error из s01 (не новый).
