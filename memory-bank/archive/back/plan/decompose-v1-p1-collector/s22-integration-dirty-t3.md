# Шаг s22: Integration: all dirt scenarios through B4
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-I3-04..13, AC-B4-13, AC-B4-07, AC-B4-08

**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Integration: all dirt scenarios through B4 — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s18, s13, s11
- **Produces:** test_normalizer_dirty.py — все сценарии грязи

## Файлы
- `apps/edge/collector/tests/integration/test_normalizer_dirty.py` (Создание)

## Интерфейсы (lean — без кода)
- n/a

## TDD (красная → зелёная)
1. **Тест:** `tests/integration/test_normalizer_dirty.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Прогнать каждый dirt scenario: ожидания quality/behavior по AC.
2. Normalizer не падает.

## Чекпоинт верификации
- матрица scenario→expected quality покрыта
- нет uncaught exceptions в worker
