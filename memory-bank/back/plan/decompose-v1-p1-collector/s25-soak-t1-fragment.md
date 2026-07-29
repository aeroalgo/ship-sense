# Шаг s25: Soak T1 fragment: 24h harness + leak checks
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-I3-15, AC-B1-13, AC-INT-02

**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Soak T1 fragment: 24h harness + leak checks — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s19–s22, s23
- **Produces:** soak test marked slow + docs how to run

## Файлы
- `apps/edge/collector/tests/soak/test_24h_fragment.py` (Создание)
- `apps/edge/collector/README.md` (Модификация) — soak runbook

## Интерфейсы (lean — без кода)
- n/a

## TDD (красная → зелёная)
1. **Тест:** `tests/soak/test_24h_fragment.py` (slow)
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Harness: emulator+collector; периодические connection drops; assert tasks/sockets не растут.
2. Маркер pytest `slow`; короткий CI fragment (напр. 60s) + полный 24h manual.

## Чекпоинт верификации
- short fragment green в CI
- 24h runbook описан
- нет роста tasks сверх допуска
