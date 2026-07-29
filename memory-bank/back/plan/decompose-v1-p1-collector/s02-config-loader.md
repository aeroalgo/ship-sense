# Шаг s02: Config loader + validator CLI + stub maps
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-CFG-01, AC-CFG-02, AC-CFG-03, AC-CFG-04, AC-B1-09

**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Config loader + validator CLI + stub maps — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s01 models; plan §16 YAML examples
- **Produces:** loader/validator; sources.dev.yaml; stub maps ≥50 tags; env override

## Файлы
- `apps/edge/collector/src/collector/config/models.py` (Создание) — SourceConfig, PollConfig, PollGroup, SubscribeConfig, SecurityConfig, TagMapEntry, CollectorSettings
- `apps/edge/collector/src/collector/config/loader.py` (Создание)
- `apps/edge/collector/src/collector/config/validator.py` (Создание)
- `apps/edge/collector/config/sources.dev.yaml` (Создание)
- `apps/edge/collector/maps/stub_aps_main.yaml` (Создание)
- `apps/edge/collector/maps/stub_skt_geu.yaml` (Создание)
- `apps/edge/collector/maps/stub_aps_main_nodes.yaml` (Создание)
- `apps/edge/collector/tests/unit/test_config_validator.py` (Создание)

## Интерфейсы (lean — без кода)
- config: `SourceConfig` — id, protocol, endpoint, poll?, subscribe?, tag_map_ref, readonly_profile, security?, extra?
- config: `TagMapEntry` — native_id, tag_id(KKS), datatype, unit?, scale?, offset?, range_min?, range_max?, fc?/node_id?
- fn: `load_sources(path) → list[SourceConfig]`
- fn: `load_tag_map(path) → list[TagMapEntry]`
- fn: `validate_config(...)` — дубли native_id → ConfigError
- CLI: `python -m collector.config validate`
- env: `COLLECTOR_SOURCES_PATH`, `COLLECTOR_MAPS_DIR`

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_config_validator.py` — valid stub, duplicate native_id, missing map, env override
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Pydantic-модели конфига по plan §8/§16.
2. Loader YAML + env override путей.
3. Validator: дубли native_id, неизвестный protocol, битые refs на maps.
4. Stub maps: aps_main ≥50 representative tags всех datatype; skt_geu subset; OPC nodes file.
5. sources.dev.yaml: два logical source `aps_main`, `skt_geu`.

## Чекпоинт верификации
- `python -m collector.config validate` exit 0 на stub
- дубли native_id → ненулевой exit + понятная ошибка
- env override меняет путь загрузки
