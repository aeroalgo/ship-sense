# Шаг s11: Quality engine YAML rules + stale + OPC/Modbus mapping
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no — **closed** (CR-COL-04, 2026-07-27) | **tdd:** yes
**AC:** AC-B4-04, AC-B4-07, AC-B4-08, AC-B4-12, AC-B3-06

- **Creative:** [creative-collector-quality-mapping.md](../../creative/v1-p1-collector/creative-collector-quality-mapping.md) — CR-COL-04 **done** (2026-07-27)

**Creative mapping notes (CR-COL-04):**
- `evaluate(raw, map_entry, now) → EvalResult(quality, value, reason)` (не голый Quality — value encoding по §4 creative)
- `map_opcua_status(name, rules) → Quality` + `map_modbus_exception(token, rules) → Quality` — standalone pure helpers
- `native_quality` контракт: structured token `opcua.<name>` / `modbus.<token>` (success=`None`). Правки: modbus/connector.py, opcua/subscription.py, opcua/connector.py + существующие тесты
- YAML canon: `config/quality_rules.yaml` + pydantic `QualityRules` (см. creative §9)
- Rule priority: fixed order в code: quarantine > native_quality > NaN > range > stale > good (creative §7)
- TDD vertical slices: creative §14.3

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Quality engine YAML rules + stale + OPC/Modbus mapping — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s01 Quality; CR-COL-04 полная таблица StatusCode/exception/NaN
- **Produces:** quality_engine + quality_rules.yaml

## Файлы
- `apps/edge/collector/src/collector/core/quality_engine.py` (Создание)
- `apps/edge/collector/config/quality_rules.yaml` (Создание)
- `apps/edge/collector/tests/unit/test_quality_engine.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `QualityEngine` — evaluate(raw, map_entry, now) → Quality
- fn: `map_opcua_status(status_code) → Quality`
- fn: `map_modbus_exception(code) → Quality`
- rules YAML: stale_threshold_sec, out_of_range→uncertain|bad, nan_inf→bad

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_quality_engine.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. До IMPLEMENT: CR-COL-04.
2. Все 5 Quality достижимы тестами.
3. Правила из YAML без правки кода.

## Чекпоинт верификации
- [x] 5 quality values покрыты тестами — GOOD/UNCERTAIN/STALE/BAD/QUARANTINE (test_quality_engine.py slices 1–5)
- [x] YAML reloadable — `from_yaml` + reload-new-instance test (slice 11); canon load green
- [x] NaN/Inf → bad — slice 2 (nan/inf/-inf parametrized)
- [x] IMPLEMENT: [s11-quality-engine.md](../../implement/implement-v1-p1-collector/s11-quality-engine.md) — done 2026-07-27 (30 passed, 182 regression)
