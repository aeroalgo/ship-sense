# Шаг s07: pymodbus async client wrapper (FC03/04 only)
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B2-01, AC-B2-07, AC-B2-08, AC-B2-09, AC-B2-11

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
pymodbus async client wrapper (FC03/04 only) — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s06 decoder
- **Produces:** async ModbusClient: connect/read/reconnect/timeout; no write FC

## Файлы
- `apps/edge/collector/src/collector/plugins/modbus/client.py` (Создание)
- `apps/edge/collector/src/collector/plugins/modbus/__init__.py` (Создание)
- `apps/edge/collector/tests/unit/test_modbus_client.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `AsyncModbusClient` — connect, disconnect, read_holding, read_input, reconnect
- errors: timeout → typed; exception code → propagate без kill loop
- invariant: API не экспортирует write_*

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_modbus_client.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Обёртка pymodbus async; только FC 03/04.
2. Unit с mock transport: timeout → bad path; exception на одном read не ломает следующий.
3. Статический/тест-гард: нет вызовов write FC 05/06/15/16 в модуле.

## Чекпоинт верификации
- нет write methods в публичном API
- reconnect после disconnect
- timeout → исключение/результат с ошибкой (явный)
