# [v1-p1-storage | s01b | dev-db-infra] IMPLEMENT

**Plan ID:** v1-p1-storage  
**Decompose step:** [s01b-dev-db-infra.md](../../plan/decompose-v1-p1-storage/s01b-dev-db-infra.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-29  
**Уровень:** L2 (локальная инфраструктура и Alembic wiring)  
**Статус:** done

## Сделано

- Переведён compose-сервис `db` на `timescale/timescaledb:2.14.2-pg16`.
- Добавлены credentials `shipsense`, порт `5432:5432`, `shm_size: 512mb`, healthcheck и отдельный профиль `storage-dev`.
- Добавлены именованный volume `tsdata`, `.env.example` с каноническим `DATABASE_URL` и README с командами dev DB.
- `alembic.ini` выровнен с credentials compose.
- Добавлен `scripts/dev-db-up.sh` с ожиданием `pg_isready`.
- Добавлен `psycopg2-binary` в `req.txt`: текущая sync-конфигурация Alembic использует SQLAlchemy URL `postgresql://...`, который требует psycopg2.

## Файлы

- `docker-compose.yml`
- `alembic.ini`
- `.env.example`
- `infra/timescale/README.md`
- `scripts/dev-db-up.sh`
- `req.txt`
- `memory-bank/back/implement/implement-v1-p1-storage/s01b-dev-db-infra.md`

## Верификация

- `docker compose --profile storage-dev config` — PASS.
- `bash -n scripts/dev-db-up.sh` — PASS.
- `docker compose --profile storage-dev up -d db` — PASS; контейнер `shipsense-db` healthy.
- `docker compose exec -T db pg_isready -U shipsense` — PASS.
- `DATABASE_URL=postgresql://shipsense:shipsense@localhost:5432/shipsense .venv/bin/alembic upgrade head` — PASS.
- В БД подтверждены `timescaledb`, `uuid-ossp`, схема `shipsense` и ревизия `001_extensions_timescale`.
- `alembic downgrade -1` + `upgrade head` — PASS.
- `.venv/bin/alembic upgrade head --sql` — PASS.

## Примечания

- Полный pytest не запускался: шаг не добавляет бизнес-логику и тестовые файлы.
- Репозиторий не содержит `.git`, поэтому git diff/status недоступны.
