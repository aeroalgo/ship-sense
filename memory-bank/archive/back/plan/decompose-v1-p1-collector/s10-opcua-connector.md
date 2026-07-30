# Шаг s10: B3 OpcUaConnector: browse, subscription, reconnect
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B3-01, AC-B3-02, AC-B3-03, AC-B3-05, AC-B3-07, AC-B3-08, AC-B3-10

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
B3 OpcUaConnector: browse, subscription, reconnect — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s03, s09; quality mapping используется в s11 (здесь native_quality raw)
- **Produces:** OpcUaConnector + browse + subscription modules; register `opcua`

## Файлы
- `apps/edge/collector/src/collector/plugins/opcua/browse.py` (Создание)
- `apps/edge/collector/src/collector/plugins/opcua/subscription.py` (Создание)
- `apps/edge/collector/src/collector/plugins/opcua/connector.py` (Создание)
- `apps/edge/collector/tests/unit/test_opcua_connector.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `OpcUaConnector(BaseSourceConnector)`
- fn: `browse_nodes(client) → list[RawTagDescriptor]`
- fn: `browse_diff(discovered, map) → added/removed` — hook B8/T7
- class: `SubscriptionManager` — create monitored items, recreate on reconnect, dedup on seam

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_opcua_connector.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Monitored items publishing_interval ~1000 ms.
2. Reconnect: пересоздать subscription без дублей sequence/seam.
3. EUInformation → unit verify vs map (warning mismatch).
4. Keep-alive / session timeout handling.

## Чекпоинт верификации
- browse возвращает descriptors
- reconnect без duplicate storm (unit mock)
- register protocol opcua
