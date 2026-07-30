# Шаг s03: SourceConnector protocol + PluginRegistry + BaseSourceConnector
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B1-01, AC-B1-02, AC-B1-10

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
SourceConnector protocol + PluginRegistry + BaseSourceConnector — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s01, s02 SourceConfig
- **Produces:** interfaces SourceConnector/CanonicalSink; PluginRegistry; BaseSourceConnector skeleton

## Файлы
- `apps/edge/collector/src/collector/domain/interfaces.py` (Создание)
- `apps/edge/collector/src/collector/plugins/__init__.py` (Создание)
- `apps/edge/collector/src/collector/plugins/registry.py` (Создание)
- `apps/edge/collector/tests/unit/test_plugin_registry.py` (Создание)

## Интерфейсы (lean — без кода)
- protocol: `SourceConnector` — source_id, protocol; connect, discover_tags, read, subscribe, healthcheck, disconnect
- type: `OnSampleCallback`, `Subscription`
- protocol: `CanonicalSink` — write_sample, write_event
- abc: `BaseSourceConnector(ABC)` — helpers metrics/recv_ts; abstract connect/discover/read/subscribe/disconnect
- class: `PluginRegistry` — register(protocol, cls), create(config) → SourceConnector

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_plugin_registry.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Зафиксировать Protocol по plan §8 (без тел плагинов).
2. PluginRegistry: register/create; unknown protocol → ConfigError.
3. Тест: регистрация fake connector; create по sources.yaml protocol; отсутствие plugin → ошибка без падения registry.

## Чекпоинт верификации
- Protocol runtime_checkable
- create('modbus_tcp') / create('opcua') после register
- unknown protocol → ConfigError
