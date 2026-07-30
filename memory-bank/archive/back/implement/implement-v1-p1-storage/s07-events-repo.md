# BACK IMPLEMENT s07-events-repo

## Handoff

- **Статус:** completed
- **Цель:** реализован `EventsRepo` для append/dedup событий, journal-фильтров и корреляции события с sample.
- **Изменения:**
  - `apps/edge/storage/events_repo.py`: `insert_batch` с дедупликацией по `idempotency_key` и PostgreSQL `ON CONFLICT DO NOTHING`; `query_journal` с фильтрами `ts_from/ts_to`, `event_name`, `source`, JSONB `tag_id/lifecycle/ack_state`, сортировкой и пагинацией; `get_with_sample` с корреляцией по `official_ts ± window_ms`.
  - `tests/storage/test_events_repo.py`: targeted проверки публичного поведения репозитория.
  - `apps/edge/storage/__init__.py`: публичные экспорты `EventsRepo`, `EventFilters`, `EventRow`, `EventWithSample`.
- **Проверка:** `PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_events_repo.py` — 4 passed.
- **Примечание:** запуск без `PYTHONPATH` невозможен из-за текущей monorepo-структуры импортов (`ModuleNotFoundError: apps`/`collector`); с корректным путём импорты и targeted тесты проходят.
- **Следующий шаг:** BACK IMPLEMENT s08-time-axis.
- **code_changed:** yes
- **New chat:** рекомендуется для следующего атомарного шага.
