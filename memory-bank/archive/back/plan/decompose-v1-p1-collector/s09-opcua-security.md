# Шаг s09: OPC UA security: certs, trust store, readonly session helpers
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B3-04, AC-B3-09, AC-B3-01 (readonly session prep)

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
OPC UA security: certs, trust store, readonly session helpers — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s02 SecurityConfig
- **Produces:** security helpers; trust store paths; readonly session factory

## Файлы
- `apps/edge/collector/src/collector/plugins/opcua/security.py` (Создание)
- `apps/edge/collector/src/collector/plugins/opcua/__init__.py` (Создание)
- `apps/edge/collector/tests/unit/test_opcua_security.py` (Создание)

## Интерфейсы (lean — без кода)
- fn: `build_client_security(config: SecurityConfig) → security_args`
- fn: `ensure_trust_store(path)`
- invariant: session создаётся без Write privileges (флаги/policy)

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_opcua_security.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Dev auto-cert path + configurable trust store.
2. Тесты: загрузка policy SignAndEncrypt; missing cert → явная ConfigError.

## Чекпоинт верификации
- trust store configurable
- missing cert → понятная ошибка
- нет Write service в security helper API
