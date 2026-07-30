# Шаг s01: DB extensions + schema (Alembic 001)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-STO-S01 (из плана §888: extensions + schema shipsense)
**code_surface:** sql

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`

## Цель
Создать первую миграцию Alembic: включить расширения `timescaledb` и `uuid-ossp`, создать схему `shipsense`, установить `search_path`. Атомарный DDL-шаг без runtime кода.

## Контекст
- **Consumes:** план §330–341 (DDL baseline), §884 (цепочка revisions).
- **Produces:** `migrations/versions/001_extensions_timescale.py`; база для всех последующих миграций.
- **Upstream:** T-001 (пока не зависит); T-003 будет читать из shipsense.
- **Downstream:** s02–s05.

## Файлы
- `migrations/versions/001_extensions_timescale.py` (Создание)
- `alembic.ini` / `migrations/env.py` (Verify — уже должны существовать в проекте; если нет — создать минимально под SQLAlchemy 2 + include_schemas=True)

## Интерфейсы (lean — без кода)
- Миграция `upgrade()`: `CREATE EXTENSION IF NOT EXISTS timescaledb;`, `uuid-ossp;`, `CREATE SCHEMA IF NOT EXISTS shipsense;`, `SET search_path TO shipsense, public;`
- `downgrade()`: `DROP SCHEMA shipsense CASCADE;` (осторожно, только если пусто; в v1 reversible по плану §902).

## TDD
- **Причина:** чистый DDL; верификация через `alembic upgrade head` + `\dt` / `SELECT * FROM pg_extension;`.
- **Верификация (parent):** 
  1. `alembic upgrade head` (или `alembic upgrade +1`).
  2. В psql (timescale image): `\dx` показывает timescaledb; `\dn` показывает shipsense; search_path корректен.
  3. `alembic downgrade -1` + повторный upgrade (без ошибок).

## Подробный процесс выполнения
1. Убедиться, что Alembic настроен (env.py target_metadata=None на этом этапе или из будущих моделей; include_schemas=True).
2. Сгенерировать/написать вручную revision 001 (alembic revision --autogenerate не даст extensions).
3. Вставить точный DDL из плана §334.
4. Добавить комментарий с ссылкой на план §888 и CR-STO-01 (chunk позже).
5. Проверить downgrade reversibility (plan §903).

## Верификация
- Targeted: `alembic current`, `alembic heads`.
- Ручная: `psql -c "SELECT extname FROM pg_extension WHERE extname IN ('timescaledb','uuid-ossp');"`
- Нет unit-тестов (DDL).
- Блокер: отсутствие timescale в dev db → parent запускает compose с timescale/timescaledb:2.14.2-pg16.

## Блокеры / CREATIVE
Нет. Это pre-CREATIVE шаг.

## Зависимости
s01 → s02 (samples hypertable).
