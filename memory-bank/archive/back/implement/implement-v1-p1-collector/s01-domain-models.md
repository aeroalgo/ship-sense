# T-001 | s01 | Domain models IMPLEMENT

**Plan ID:** v1-p1-collector  
**Decompose step:** [s01-domain-models.md](../../plan/decompose-v1-p1-collector/s01-domain-models.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-26  
**Уровень:** L2  
**Статус:** done

## Skills

- `tdd`
- `python-testing-patterns`
- `modern-python`
- `verification-before-completion`

## Сделано

- Создан пакет `collector.domain` с экспортом публичных моделей и ошибок.
- Реализованы Pydantic v2-контракты `Quality`, `RawSample`, `RawTagDescriptor`, `TelemetrySample`, `Event`, `HealthStatus`, `CollectorHealthSnapshot` и связанные enum-типы.
- Добавлены `ConnectError` и `ConfigError`.
- Добавлены targeted unit-тесты на enum values, обязательные поля, defaults, nested round-trip и JSON-сериализацию.
- Бизнес-логика нормализации не добавлялась.

## Файлы

- `apps/edge/collector/src/collector/domain/__init__.py`
- `apps/edge/collector/src/collector/domain/models.py`
- `apps/edge/collector/src/collector/domain/errors.py`
- `apps/edge/collector/tests/unit/test_domain_models.py`

## Тесты

- cmd: `PYTHONPATH=apps/edge/collector/src pytest -q apps/edge/collector/tests/unit/test_domain_models.py`
- итог: `8 passed in 0.08s`
- red evidence: до реализации импорт падал с `ModuleNotFoundError: No module named 'collector'`.

## Integration check

- [x] Domain fields match plan §7 contracts.
- [x] No storage keys, env vars, DB columns or event handlers are introduced in this step.
- [x] `Quality`, `SourceState` and event severity are shared public types for following collector steps.
