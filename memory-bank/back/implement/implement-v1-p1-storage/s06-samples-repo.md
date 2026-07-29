# [v1-p1-storage | s06 | samples-repo] IMPLEMENT

**Plan ID:** v1-p1-storage
**Decompose step:** [s06-samples-repo.md](../../plan/decompose-v1-p1-storage/s06-samples-repo.md)
**Дата:** 2026-07-29
**Уровень:** L2
**Статус:** completed

## Сделано

- Реализован `SamplesRepo` с async `insert_batch`, `query_trend` и `query_point`.
- Добавлен dedup по `(tag_id, ts)` с lower-is-better quality и last-write-wins при равном качестве.
- Добавлен `SamplePoint` и экспорт из `apps.edge.storage`.
- `query_trend` возвращает raw samples в порядке времени с ограничением `max_points`.
- Добавлена numeric-нормализация значений `TelemetrySample`; нечисловые значения отклоняются явно.

## Файлы

- `apps/edge/storage/samples_repo.py`
- `apps/edge/storage/__init__.py`
- `tests/storage/test_samples_repo.py`

## Верификация

- RED: первый запуск targeted тестов выявил отсутствие реализации и затем отсутствие fixture `async_session`.
- GREEN: `PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_samples_repo.py -k "dedup or trend" -vv` — PASS (2 passed).
- Реальный PostgreSQL/Testcontainers, COPY path и performance thresholds не запускались.

## Handoff

Следующий шаг: BACK IMPLEMENT s07-events-repo.
