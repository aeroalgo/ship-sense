# Шаг s18: I3 ScenarioRunner + all dirt injectors
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no — **closed** | **tdd:** yes
**AC:** AC-I3-04, AC-I3-05, AC-I3-06, AC-I3-07, AC-I3-08, AC-I3-09, AC-I3-10, AC-I3-11, AC-I3-12, AC-I3-13, AC-I3-14

- **Creative:** [CR-COL-03 / creative-collector-emulator-fidelity.md](../../creative/creative-collector-emulator-fidelity.md) — ScenarioRunner отделяет value/metadata/transport dirt; порядок применения: base model → value overlays → timestamp/quality overlays → transport hooks.

**Контракт потребления s15:** сценарии выбирают `signal_id` из profile, не зашивают APS-specific модель; одинаковый profile + seed + scenario дают детерминированный результат.


**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
I3 ScenarioRunner + all dirt injectors — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s15–s17; plan §10.4 scenarios.yaml
- **Produces:** scenario_runner + injectors; scenarios.yaml

## Файлы
- `apps/edge/emulator/src/emulator/dirt/scenario_runner.py` (Создание)
- `apps/edge/emulator/src/emulator/dirt/injectors/*.py` (Создание) — chatter, connection_drop, out_of_range, stuck_value, time_jump, tag_map_change, bad_frame, nan_inf, duplicate, opc_bad_quality
- `apps/edge/emulator/config/scenarios.yaml` (Создание)
- `apps/edge/emulator/src/emulator/app.py` (Создание)
- `apps/edge/emulator/src/emulator/__main__.py` (Создание)
- `apps/edge/emulator/tests/test_scenarios.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `ScenarioRunner` — enable(name|list), tick inject
- injectors: каждый scenario name из AC-I3-04..13

## TDD (красная → зелёная)
1. **Тест:** `apps/edge/emulator/tests/test_scenarios.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. YAML scenarios; enable by name/combo; deterministic under seed.
2. Wire emulator app entrypoint.

## Чекпоинт верификации
- каждый scenario включается по имени
- детерминизм под seed
- connection_drop реально рвёт TCP
