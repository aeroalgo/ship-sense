# Шаг s07: EventsRepo (append, dedup, journal, correlation)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK CREATIVE
**needs_creative:** yes (CR-STO-04) — **closed** | **tdd:** yes
**Creative:** [CR-STO-04 event dual-mode schema](../../creative/v1-p1-storage/creative-event-dual-mode-schema.md)
**AC:** AC-STO-S07 (из плана §197–207, §1105: insert_batch ON CONFLICT, query_journal, get_with_sample)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `EventsRepo` — append-only insert с дедупом по idempotency_key, query_journal с фильтрами (ts range, event_name, source, params tag/lifecycle), get_with_sample (корреляция по official_ts ± window).

## Контекст
- **Consumes:** s03 events table, s05 schemas.Event, s08 time_axis (official_ts).
- **Produces:** apps/edge/storage/events_repo.py.
- **Upstream:** T-001 Event (idempotency_key обязателен).
- **Downstream:** s09 writer, T-003 journal + correlation.
- **План:** §373 (DDL), §1105 (interface), §204 (storm 200/s), §205 (correlation).

## Файлы
- `apps/edge/storage/events_repo.py` (Создание)
- `tests/storage/test_events_repo.py` (Создание)

## Интерфейсы (lean — без кода)
- class EventsRepo:
  - async def insert_batch(self, events: list[Event]) -> int: ...  # ON CONFLICT DO NOTHING, return inserted count
  - async def query_journal(self, filters: EventFilters, limit: int, offset: int = 0) -> list[EventRow]: ...
  - async def get_with_sample(self, event_id: UUID, window_ms: int = 0) -> EventWithSample: ...
- EventFilters: ts_from, ts_to, event_name?, source?, tag_id?, lifecycle?, ack_state?
- EventRow, EventWithSample — pydantic / dataclass с sample или flag sample_missing.

## TDD
- **Да:** тесты на idempotency (duplicate → count 0), append-only trigger (UPDATE raises), journal filters, correlation.
- Integration: testcontainers.
- Targeted pytest -k "events_repo or correlation"

## Подробный процесс выполнения
1. insert_batch: INSERT ... ON CONFLICT (idempotency_key) DO NOTHING; count affected.
2. query_journal: строит WHERE по фильтрам, ORDER BY official_ts, event_id; использует индексы.
3. get_with_sample: SELECT event + LEFT JOIN samples ON official_ts ± window (или closest).
4. Метрики: writer_events_total, dedup_events_total.
5. Для Q4: поле reconstructed.

## Верификация
- 10 событий + 2 duplicate → total 10, dedup count 2.
- query_journal по alarm active → только matching.
- get_with_sample: sample в ±0 или ±5s возвращается; нет sample → flag.
- Блокер: s03, s05, s08.

## Блокеры / CREATIVE
CR-STO-04 dual-mode — [frozen core + JSONB envelope, Q4=A/B models](../../creative/v1-p1-storage/creative-event-dual-mode-schema.md); reconstructed flag + params JSONB.
