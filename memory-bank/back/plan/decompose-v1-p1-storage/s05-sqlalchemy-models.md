# Шаг s05: SQLAlchemy models (schemas.py) + finalize quota migration
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-STO-S05 (модели SQLAlchemy 2 зеркалят DDL s02–s04; Alembic target_metadata; базовые mapped classes)
**code_surface:** sql

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`

## Цель
Создать `apps/edge/storage/schemas.py` — SQLAlchemy 2 declarative модели (Sample, Event, SemanticMeta, TagQuarantine, ClockShiftLog, HealthSnapshot, StorageQuotaConfig, SamplesDegradeLog, SamplesDegradeWatermark) точно отражающие DDL из s01–s04. Настроить Alembic env.py на target_metadata. Финализировать миграцию 005 если нужно.

## Контекст
- **Consumes:** s02–s04 DDL; план §105 (schemas.py), §897 (env.py), §236–312 (ERD).
- **Produces:** models для SamplesRepo/EventsRepo (s06/s07); Alembic discover.
- **Upstream:** T-001 TelemetrySample/Event (мэппинг в insert).
- **Downstream:** все repos + writer.

## Файлы
- `apps/edge/storage/schemas.py` (Создание)
- `migrations/env.py` (Verify/минимальная правка если отсутствует: target_metadata = Base.metadata, include_schemas=True)
- `migrations/versions/005_quota_degrade.py` (Update если нужно после моделей)

## Интерфейсы (lean — без кода)
- class Sample(Base): __tablename__ = 'samples'; ts, tag_id, value, quality, source_ts, edge_ts, official_ts
- class Event(Base): ... idempotency_key unique, params JSON, reconstructed
- class SemanticMeta, TagQuarantine, ClockShiftLog, HealthSnapshot, StorageQuotaConfig, SamplesDegradeLog, SamplesDegradeWatermark
- Base = declarative_base() или MappedAsDataclass + Mapped[] (modern SQLA 2).
- __table_args__ для PK, constraints, indexes где нужно.

## TDD
- **Да:** unit тесты на модели (instantiate, constraints validation via SQLA).
- **Тесты:** `tests/storage/test_schemas.py` (create row objects, check columns, relationship stubs если есть).
- alembic upgrade с target_metadata.

## Подробный процесс выполнения
1. Определить Base.
2. Mapped классы 1:1 с DDL (quality SmallInteger CHECK, JSONB как JSON, timestamptz как DateTime(timezone=True)).
3. Для events: relationship на clock_shift_log (optional).
4. Для samples: composite PK.
5. Добавить docstring с ссылкой на план §236 ERD.
6. В env.py: from .schemas import Base; target_metadata = Base.metadata
7. alembic revision --autogenerate (для 005 если нужно) — но вручную держать в sync с DDL.

## Верификация
- `python -c "from storage.schemas import Sample, Event; print('ok')"`
- alembic upgrade head — таблицы созданы, модели маппятся.
- pytest tests/storage/test_schemas.py (если создаём в этом шаге — targeted).
- Блокер: s01–s04.

## Блокеры / CREATIVE
Нет.
