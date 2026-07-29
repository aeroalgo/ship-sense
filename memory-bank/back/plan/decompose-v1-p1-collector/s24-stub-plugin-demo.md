# Шаг s24: Demo third-party stub plugin (AC-B1-08)
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B1-08

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Demo third-party stub plugin (AC-B1-08) — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s03 PluginRegistry
- **Produces:** plugins/stub connector без правки ядра

## Файлы
- `apps/edge/collector/src/collector/plugins/stub/__init__.py` (Создание)
- `apps/edge/collector/src/collector/plugins/stub/connector.py` (Создание)
- `apps/edge/collector/tests/unit/test_stub_plugin.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `StubConnector(BaseSourceConnector)` — synthetic RawSample
- register: protocol `stub`

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_stub_plugin.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Плагин в отдельном пакете; регистрация entry/import side-effect без изменения core registry code (только register call).

## Чекпоинт верификации
- sources.yaml protocol stub работает
- ядро registry.py не содержит if stub
