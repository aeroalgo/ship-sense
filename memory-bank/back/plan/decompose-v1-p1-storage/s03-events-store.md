# Шаг s03: events append-only store (Alembic 003)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-STO-S03 (из плана §196–207 B6: append-only, trigger, indexes, idempotency, dual-mode stub)
**code_surface:** sql

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`

## Цель
Создать таблицу `events` append-only: UUID PK, idempotency_key UNIQUE, core поля + JSONB params, reconstructed, триггер forbid UPDATE/DELETE, индексы для journal и корреляции.

## Контекст
- **Consumes:** s01; план §373–410 (DDL events + trigger).
- **Produces:** миграция 003; основа EventsRepo (s07).
- **Upstream:** T-001 Event (idempotency_key, event_name, source, *_ts, params, severity, reconstructed).
- **Downstream:** s07, s08 (clock_shift), T-003 journal.

## Файлы
- `migrations/versions/003_events_append_only.py` (Создание)

## Интерфейсы (lean — без кода)
- Таблица events с UNIQUE idempotency_key, CHECK severity, default reconstructed=false.
- Функция + триггер `forbid_events_mutation` BEFORE UPDATE OR DELETE.
- Индексы: official_ts, (event_name, official_ts), source, (params->>'tag_id'), lifecycle active.

## TDD
- DDL; verify через psql + trigger test (попытка UPDATE → exception).
- `alembic upgrade/downgrade`.

## Подробный процесс выполнения
1. DDL точно из плана §376–410.
2. Пример params для alarm (Q4=A) и setpoint_change.
3. Комментарий: dual-mode до Q4 (CR-STO-04) — **closed**, решение: [frozen core + JSONB envelope](../../creative/creative-event-dual-mode-schema.md).
4. Downgrade: DROP TABLE + DROP FUNCTION.

## Верификация
- `INSERT` с duplicate idempotency_key → no-op (unique).
- `UPDATE events SET ...` → RAISE 'append-only'.
- Индексы не seq-scan на типичных фильтрах 7 дней.
- Блокер: s01.

## Блокеры / CREATIVE
CR-STO-04 (event schema dual-mode) — [closed: frozen core + params JSONB](../../creative/creative-event-dual-mode-schema.md).
