# s12 — Unit converter: units.yaml + scale/offset IMPLEMENT

**Дата:** 2026-07-27
**Уровень:** L2 (один pure-сервисный модуль + YAML canon + TDD)
**Статус:** done

**Plan:** [plan-v1-p1-collector.md](../../plan/plan-v1-p1-collector.md) (§14.3 Unit conversion, §16.2 units.yaml)
**Decompose:** [s12-unit-converter.md](../../plan/decompose-v1-p1-collector/s12-unit-converter.md)
**AC:** AC-B4-03 (Unit conversion через справочник + scale/offset из карты), AC-B4-09 (unknown unit → unit=unknown + warning log)

## Сделано

UnitConverter (pure core + YAML-canonical rules): alias resolution + per-tag scale/offset calibration + conversion-словарь.

- `core/unit_converter.py`: `ConversionRule(from_, to, scale, offset)` + `UnitRules(aliases, conversions)` (pydantic, validates YAML at load) + `UnitConverter(rules)` + `from_yaml` classmethod + `convert(value, from_unit, to_unit, scale?, offset?) → (value, unit)` + private `_resolve` (alias→canonical) + `_is_numeric` helper.
- `config/units.yaml`: canon правил (aliases: °C/deg C/C→degC, °K/kelvin→K; conversions: degC↔K, bar↔kPa — scale/offset явные).
- Логика `convert` (два уровня, plan §14.3):
  1. non-numeric (None/bool/str) → passthrough, unit = resolved `to_unit`. NaN — числовой (NaN*scale+offset=NaN), non-finite→bad = зона s11 QualityEngine.
  2. per-tag `scale`/`offset` заданы (из TagMapEntry) → калибровка raw→engineering (`scale*value+offset`), conversion-словарь **пропускается** (калибровка уже даёт целевую единицу).
  3. иначе conversion-словарь lookup `(src_canonical, dst_canonical)`; нет правила → **AC-B4-09**: `unit="unknown"` + `logger.warning` (с логом `from`/`to`), value passed through без изменения.
- Alias resolve до identity-check: `°C`→`degC` identity даёт 0-конверсию; `C`→`degC`→`K` применяет conversion.

TDD vertical slices (plan §14.3, 1 test → 1 impl): identity → alias identity → degC→K → K→degC → bar→kPa → kPa→bar → alias-as-source conversion → per-tag scale+offset → per-tag offset → scale-only (offset default) → per-tag skips dictionary → unknown from-unit (unknown+warn) → no-rule (unknown+warn) → None passthrough → bool passthrough → str passthrough → NaN passthrough → canon YAML load → reload edited rule. RED confirmed (ModuleNotFoundError: collector.core.unit_converter) → GREEN.

## Файлы

**Создание:**
- `apps/edge/collector/src/collector/core/unit_converter.py`
- `apps/edge/collector/config/units.yaml`
- `apps/edge/collector/tests/unit/test_unit_converter.py`

## Тесты

- cmd: `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m pytest apps/edge/collector/tests/unit/test_unit_converter.py -q`
- итог: **19 passed** (identity + alias + conversions degC↔K/bar↔kPa + per-tag scale/offset + skip-dictionary + unknown/no-rule warning paths + None/bool/str/NaN passthrough + canon YAML load + reload edited)
- regression cmd: `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m pytest apps/edge/collector/tests/unit/test_quality_engine.py apps/edge/collector/tests/unit/test_unit_converter.py -q`
- regression итог: **49 passed** (s11+s12 core не конфликтуют)

> Запуск: src-layout, пакет не installed → `PYTHONPATH=apps/edge/collector/src` (нет editable install, нет pytest.ini pythonpath — канон прогона как в s11). Полный suite = BACK QA.

## Integration check (§0.11)

- [x] YAML path `config/units.yaml` ↔ `UnitConverter.from_yaml` (canon load test green — degC→K round-trip из canon-файла).
- [x] `from_` alias на pydantic-поле (`from` зарезервировано) ↔ YAML ключ `from` ↔ test. Round-trip валиден.
- [x] defaults в pydantic-моделях (`scale=1.0, offset=0.0`, empty aliases/conversions) — `UnitRules()` без YAML валиден.
- [x] non-numeric contract: `_is_numeric` = `isinstance(int,float) and not bool` — bool не числовой (passthrough), NaN числовой (float).
- [ ] **Wiring в NormalizerWorker (s13)** — вне scope s12. Converter instance не создаётся в pipeline. → s13: `UnitConverter.from_yaml(config/units.yaml)` + `convert(raw_value, map_entry.unit/<tag unit>, map_entry.unit, map_entry.scale, map_entry.offset)` после `QualityEngine.evaluate`.
- [n/a] env / DB / route / migration / column — модуль pure, без I/O кроме однократного YAML-read в `from_yaml`.

## Known / out-of-scope

- Per-tag calibration берёт scale/offset как positional kwargs в тестах (извлекаются из `TagMapEntry` в вызывающем коде). В s13 NormalizerWorker передаст `map_entry.scale`/`map_entry.offset`/`map_entry.unit` напрямую — здесь тестируется контракт `convert(...)`, не интеграция с map.
- Conversion reverse-правила задаются явно в YAML (нет авто-inverse) — соответствует плану (§14.3: явный список `conversions`). `bar↔kPa`, `degC↔K` оба направления прописаны.
- `to_unit=None` / `from_unit=None` edge: `_resolve(None)→""`, identity src==dst="" → passthrough. Не покрыто явным тестом (нет AC-требования), но не падает.
- Cross-quantity no-rule (bar→degC, известные единицы, нет правила) покрыт тестом — AC-B4-09-warning срабатывает и для известных-но-несовместимых пар, не только unknown-строк.
