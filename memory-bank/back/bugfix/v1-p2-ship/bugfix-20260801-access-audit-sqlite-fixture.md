# [T-005 | QA-3] BUGFIX — SQLite schema для access_audit

**Дата:** 2026-08-01  
**Эпик:** `v1-p2-ship`  
**Источник:** [qa-20260801-v1-p2-ship.md](../../qa/v1-p2-ship/qa-20260801-v1-p2-ship.md) → QA-3  
**Статус:** completed

## Симптом

`apps/api/tests/api/test_session.py::test_session_lifecycle_sets_cookie_and_writes_events` падал на чистой default SQLite базе с `sqlite3.OperationalError: no such table: access_audit`. После создания таблицы вручную проявлялась следующая несовместимость: SQLite не умеет bind-ить `UUID` напрямую (`sqlite3.ProgrammingError: Error binding parameter 3: type 'UUID' is not supported`).

## Root cause

API session dependency использует default `sqlite+aiosqlite:///./shipsense.db`, но API test fixture не инициализировал схему `access_audit` перед вызовом `AccessAuditWriter`. Production migration `migrations/versions/009_access_audit.py` рассчитана на PostgreSQL и не является SQLite test setup. Дополнительно writer передавал доменный `UUID` непосредственно в raw SQL bind, что несовместимо с SQLite.

## Исправление

- `apps/api/tests/conftest.py` получил autouse async fixture `database_schema`: перед каждым API-тестом создаёт SQLite-совместимую append-only storage table `access_audit`, после теста удаляет её строки.
- `apps/api/app/audit/writer.py` сериализует `session_id` в строку перед raw SQL bind; `None` сохраняется как `None`.
- `apps/api/tests/audit/test_access_audit.py` закрепляет контракт строковой передачи UUID в writer.
- Исправление не маскирует ошибку в endpoint: test DB получает минимальную схему, необходимую фактическому `AccessAuditWriter`.

## Файлы

- `apps/api/tests/conftest.py`
- `apps/api/app/audit/writer.py`
- `apps/api/tests/audit/test_access_audit.py`

## Тесты

- cmd: `.venv/bin/pytest apps/api/tests/api/test_session.py -q --tb=line`
- итог: `2 passed`
- cmd: `.venv/bin/pytest apps/api/tests/audit/test_access_audit.py -q --tb=line`
- итог: `2 passed`
- cmd: `.venv/bin/pytest apps/api/tests/api/test_assets_tree.py apps/api/tests/api/test_series.py -q --tb=line`
- итог: `3 errors` — независимый QA-4: `vessel.yaml` содержит 3 tags вместо обязательных 4.

## Integration check

- [x] SQLite test schema создаётся до session endpoint и очищается после теста
- [x] `access_audit` columns ↔ `AccessAuditWriter` INSERT fields
- [x] UUID domain value сериализуется перед SQLite raw SQL bind
- [x] PostgreSQL migration и production append-only contract не изменены
- [ ] полный backend suite — ожидает отдельного QA-4 BUGFIX

## Следующая проверка

`BACK BUGFIX привести test vessel pack к обязательным четырём tags`, затем `BACK QA v1-p2-ship`.
