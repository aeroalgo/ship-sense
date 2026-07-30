# Шаг s01b: Dev DB infra (TimescaleDB compose + Alembic wiring)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-STO-S01b (dev infra: TimescaleDB 16, alembic upgrade s01, psql verify)
**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/supabase-postgres-best-practices/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Поднять локальную dev-инфраструктуру TimescaleDB для проверки миграций s01–s05: заменить stub `postgres:16-alpine` на `timescale/timescaledb:2.14.2-pg16`, выровнять `DATABASE_URL` с Alembic, дать команды parent для `alembic upgrade head` и `psql`.

## Контекст
- **Consumes:** s01 (`001_extensions_timescale.py`, `alembic.ini`, `migrations/env.py`).
- **Produces:** рабочий `db` в compose; согласованный URL для Alembic; README/скрипт smoke для parent.
- **Upstream:** gap decompose — s01 верифицирован только `--sql`, без живой БД.
- **Downstream:** s02–s05 (DDL verify), s06+ (repos/testcontainers опционально позже).

## Файлы
- `docker-compose.yml` (Модификация: service `db` → timescale image, ports, healthcheck, profile)
- `alembic.ini` (Модификация: default URL `postgresql://shipsense:shipsense@localhost:5432/shipsense`)
- `.env.example` (Создание или Модификация: `DATABASE_URL=...`)
- `infra/timescale/README.md` (Создание — команды parent: up, psql, alembic)
- `scripts/dev-db-up.sh` (Создание, опционально — `docker compose up -d db` + wait + `alembic upgrade head`)

## Интерфейсы (lean — без кода)
- compose `db`: image `timescale/timescaledb:2.14.2-pg16`, env `POSTGRES_DB/USER/PASSWORD=shipsense`, port `5432:5432`, volume `tsdata`, `shm_size: 512mb`, healthcheck `pg_isready -U shipsense`.
- profile: `storage-dev` (или убрать `full` — db доступен без полного edge stack).
- `DATABASE_URL` override в env для Alembic (канон = compose credentials).

## TDD (нет)
- **Причина:** infra / compose / wiring; без новой бизнес-логики.
- **Верификация (parent only):**
  1. `docker compose --profile storage-dev up -d db` (или эквивалент из shard).
  2. `docker compose exec db pg_isready -U shipsense` — healthy.
  3. `DATABASE_URL=postgresql://shipsense:shipsense@localhost:5432/shipsense .venv/bin/alembic upgrade head` — PASS.
  4. `docker compose exec db psql -U shipsense -d shipsense -c "SELECT extname FROM pg_extension WHERE extname IN ('timescaledb','uuid-ossp');"` — оба extension.
  5. `docker compose exec db psql -U shipsense -d shipsense -c "\dn"` — schema `shipsense`.
  6. `.venv/bin/alembic downgrade -1` + повторный `upgrade head` — без ошибок.

## Подробный процесс выполнения
1. В `docker-compose.yml` заменить `db.image` на `timescale/timescaledb:2.14.2-pg16` (plan §1128–1151, dev-tuned conf опционально урезать для laptop).
2. Убрать зависимость db только от `profile: full` — ввести `profiles: ["storage-dev"]` или поднимать db в default smoke-профиле storage-работы.
3. Переименовать volume `db-data` → `tsdata` или оставить `db-data` (не ломать существующий volume без нужды).
4. Выровнять `alembic.ini` `sqlalchemy.url` с compose credentials.
5. Добавить `.env.example` с `DATABASE_URL`.
6. Документировать в `infra/timescale/README.md` команды parent (up, psql, alembic, teardown).
7. Опционально: `scripts/dev-db-up.sh` — wait healthy + `alembic upgrade head`.
8. Parent: прогнать верификацию s01 (реальный upgrade, не только `--sql`).

## Верификация
- `docker compose ps db` — Up (healthy).
- `alembic current` — `001_extensions_timescale (head)`.
- Extensions + schema shipsense в psql.
- s01 implement shard можно дополнить отметкой «live DB verified» после этого шага.

## Блокеры / CREATIVE
Нет.

## Зависимости
s01 → **s01b** → s02 (samples hypertable требует timescaledb extension из s01 на живой БД).
