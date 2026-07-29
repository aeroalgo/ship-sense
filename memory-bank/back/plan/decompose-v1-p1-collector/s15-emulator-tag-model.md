# Шаг s15: I3 emulator tag model: 586 tags + correlations + seed
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no — **closed** | **tdd:** yes
**AC:** AC-I3-03, AC-I3-14 (часть seed), детерминизм T3

- **Creative:** [CR-COL-03 / creative-collector-emulator-fidelity.md](../../creative/creative-collector-emulator-fidelity.md) — универсальная profile-driven архитектура, общий snapshot, generic dependency graph и stable per-signal seed streams.

**code_surface:** model

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
I3 emulator tag model: 586 tags + correlations + seed — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** CR-COL-03 fidelity/seed; stub maps
- **Produces:** emulator tag_model + physics correlations + tags_stub.yaml

## Файлы
- `apps/edge/emulator/src/emulator/tag_model.py` (Создание)
- `apps/edge/emulator/src/emulator/physics/correlations.py` (Создание)
- `apps/edge/emulator/src/emulator/physics/daily_patterns.py` (Создание)
- `apps/edge/emulator/config/tags_stub.yaml` (Создание)
- `apps/edge/emulator/tests/test_determinism.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `TagGenerator` — tick(t) → dict[native_id, value]; seed → deterministic
- fn: `correlate_rpm_temp_pressure(...)`

## TDD (красная → зелёная)
1. **Тест:** `apps/edge/emulator/tests/test_determinism.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. До IMPLEMENT: CR-COL-03 (один/два процесса, seed).
2. Генератор ~586 тегов; корреляции; одинаковый seed → одинаковый поток.

## Чекпоинт верификации
- одинаковый seed → одинаковые N тиков
- корреляции rpm↔temp правдоподобны
