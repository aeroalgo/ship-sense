# BACK REFACTOR — r04 import graph audit

- **Epic:** `rf-fastapi-template-ownership`
- **Step:** `r04`
- **Дата:** 2026-07-30
- **Behavior freeze:** import ownership rules (Shared Kernel); model fields, IPC wire, DB schema, plugin semantics unchanged.

## Реализация / Файлы
- Создан `apps/api/tests/unit/test_domain_no_fastapi.py` (усилен): AST-проверка — `app.telemetry`, `app.events`, `app.semantic` не импортируют `fastapi`, `starlette`, `app.api`, `app.main`.
- Создан `apps/edge/collector/tests/unit/test_plugins_no_app_canonical.py`: transport plugins (`collector/plugins/*`, кроме mapping) не импортируют `app.telemetry` / `app.events` (только Raw* + health).
- Существующий `tests/storage/test_no_collector_domain_canonical.py` подтверждён: storage не импортирует `collector.domain` canonical.
- Обновлён `apps/edge/collector/README.md`: добавлена секция **Ownership** с явными правилами + ссылки на три regression-теста (plan §5.6 Фаза F).

## Верификация / Тесты
- Before (baseline): `.venv/bin/pytest apps/api/tests/unit/test_domain_no_fastapi.py tests/storage/test_no_collector_domain_canonical.py -q --tb=line` → `2 passed`.
- After targeted (3 файла): `PYTHONPATH=apps/edge/collector/src:apps/api:. .venv/bin/pytest apps/api/tests/unit/test_domain_no_fastapi.py tests/storage/test_no_collector_domain_canonical.py apps/edge/collector/tests/unit/test_plugins_no_app_canonical.py -q --tb=line --override-ini="addopts="` → `3 passed`.
- Smoke: collector unit + storage unit (pre-existing pipeline DB integration errors не в scope r04; audit тесты изолированы).
- Pre-FINISH verify (Agent subagent_type=verify): VERDICT PASS
  - AC+: targeted pytest green до/после; поведение/контракт сохранены.
  - AC−: публичный API/контракт вне scope r04 не изменён; не вышел за diff.
  - §0.11: counterparts (writer.py, test_storage_contracts.py) подтверждены; env/config не затронуты.
  - VERIFY команда выполнена успешно.
- `.venv/bin/graphify update .` (запустить на FINISH).

## Статус
`completed`
