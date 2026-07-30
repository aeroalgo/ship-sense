# Шаг s21: Integration: dual source isolation + dual protocol
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-B1-03, AC-B1-04, AC-CFG-01

**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Integration: dual source isolation + dual protocol — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s04, s08, s10, s19–s20
- **Produces:** test_dual_source_isolation.py

## Файлы
- `apps/edge/collector/tests/integration/test_dual_source_isolation.py` (Создание)

## Интерфейсы (lean — без кода)
- n/a

## TDD (красная → зелёная)
1. **Тест:** `tests/integration/test_dual_source_isolation.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Два source (modbus+opcua или два endpoints); kill одного → второй жив.

## Чекпоинт верификации
- source A down → B sample_rate > 0
- агрегированный health отражает оба
