# Шаг s12: Unit converter: units.yaml + scale/offset
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B4-03, AC-B4-09

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Unit converter: units.yaml + scale/offset — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s01 TelemetrySample unit field; plan §14.3
- **Produces:** unit_converter + units.yaml

## Файлы
- `apps/edge/collector/src/collector/core/unit_converter.py` (Создание)
- `apps/edge/collector/config/units.yaml` (Создание)
- `apps/edge/collector/tests/unit/test_unit_converter.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `UnitConverter` — convert(value, from_unit, to_unit, scale?, offset?) → (value, unit)
- unknown unit → unit=`unknown` + warning (не exception silent)

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_unit_converter.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Справочник units.yaml + aliases; scale/offset из tag map.
2. Тесты: degC↔K, bar↔kPa, unknown → unknown.

## Чекпоинт верификации
- scale/offset применяются
- unknown → unit unknown + log warning path тестируем
