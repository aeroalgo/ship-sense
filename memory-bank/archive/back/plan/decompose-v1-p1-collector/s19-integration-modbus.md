# Шаг s19: Integration: collector B2 ↔ emulator Modbus
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-I3-01, AC-B2-* happy path, AC-INT-03 fragment

**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Integration: collector B2 ↔ emulator Modbus — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s08, s16, s13–s14
- **Produces:** integration test_modbus_emulator.py green

## Файлы
- `apps/edge/collector/tests/integration/test_modbus_emulator.py` (Создание)
- `apps/edge/collector/tests/conftest.py` (Создание/Модификация)

## Интерфейсы (lean — без кода)
- n/a — integration harness

## TDD (красная → зелёная)
1. **Тест:** `tests/integration/test_modbus_emulator.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Поднять emulator modbus + collector B2; получить TelemetrySample stream через MockSink.
2. Проверить rate и mapping subset tags.

## Чекпоинт верификации
- samples приходят с quality good на happy path
- pytest integration green
