# Шаг s20: Integration: collector B3 ↔ emulator OPC UA
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-I3-02, AC-B3-* happy path

**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Integration: collector B3 ↔ emulator OPC UA — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s10, s17, s13
- **Produces:** integration test_opcua_emulator.py green

## Файлы
- `apps/edge/collector/tests/integration/test_opcua_emulator.py` (Создание)

## Интерфейсы (lean — без кода)
- n/a

## TDD (красная → зелёная)
1. **Тест:** `tests/integration/test_opcua_emulator.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Emulator OPC UA + B3 subscribe → canonical samples.

## Чекпоинт верификации
- monitored items → samples
- StatusCode good → Quality.good
