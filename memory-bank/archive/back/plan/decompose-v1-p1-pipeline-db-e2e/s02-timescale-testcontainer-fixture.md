# Шаг s02: Timescale testcontainer + alembic + writer_tcp fixture
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** infra (ADR-PIPE-002) — база для AC-PIPE-01..05
**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Пакет `tests/pipeline/` с session-scoped Timescale (`timescale/timescaledb:2.14.2-pg16`), alembic `upgrade head`, async engine/session, truncate autouse, fixture `writer_tcp` на ephemeral port через `start_tcp`. Skip с явной причиной, если Docker недоступен — не silent pass.

## Контекст
- **Consumes:** s01 `start_tcp`; `migration_database_url` из `apps.edge.storage.__main__`; image tag = compose `db`; `testcontainers` в dev deps.
- **Produces:** `tests/pipeline/conftest.py` fixtures для L0/L1.

## Файлы
- `tests/pipeline/__init__.py` (Создание)
- `tests/pipeline/conftest.py` (Создание)
- `pyproject.toml` (Модификация — минимум: `testpaths` += `tests/pipeline` если ещё нет; markers можно отложить до s08)

## Интерфейсы (lean — без кода)
- fixture `timescale_url` (session) → `str` async URL `postgresql+asyncpg://…`; DockerContainer image выше; env `POSTGRES_USER/PASSWORD/DB=shipsense`; wait `pg_isready`; alembic с sync URL через `migration_database_url` / `+psycopg`; teardown stop container.
- fixture `db_engine` / `db_session` (function или module) → AsyncSession; autouse truncate `samples`/`events` (и при необходимости dependent tables) между тестами.
- fixture `writer_endpoint` → `tuple[str, int]`; поднимает `WriterService(session, SamplesRepo, EventsRepo, flush_interval_ms=50)` → `start_tcp("127.0.0.1", 0)` + background `writer_loop` task; yield endpoint; shutdown + cancel task.
- Skip: `shutil.which("docker") is None` или daemon down → `pytest.skip("Docker required for pipeline DB E2E")`.
- Запрещено: SQLite / vanilla PostgresContainer как fallback; запрещён skip success без reason.

## TDD (красная → зелёная)
1. **Тест-smoke фикстуры:** минимальный `tests/pipeline/test_fixture_smoke.py` (или первый assert внутри conftest-проверки через tiny test):
   - `test_timescale_alembic_ready` — `SELECT 1` + таблица `samples` существует после upgrade.
   - Запуск без Docker: skip с reason (не fail CI без Docker).
   - Запуск с Docker: PASS.
2. **Реализация:** conftest по plan §3.3–3.4 / §6.4.
3. **Запуск:** `.venv/bin/pytest tests/pipeline/test_fixture_smoke.py -m integration -q` (parent + Docker).

## Подробный процесс выполнения
1. Создать пакет `tests/pipeline`.
2. Session container + alembic (reuse pattern plan §6.4; cwd = repo root).
3. writer_tcp harness: не вызывать `__main__`; только `WriterService`.
4. Markers: `@pytest.mark.integration` + `slow` на smoke-тесте.
5. Anti-patterns: явные ошибки alembic fail → pytest fail; не глотать migrate errors.

## Чекпоинт верификации
- Docker есть → alembic head + `samples` hypertable доступна.
- `writer_endpoint` порт > 0, shutdown чистый.
- Без Docker → skip reason содержит `Docker required`.

## Зависимости
- Upstream: s01 hard.
- Downstream: s03–s06.

## Frontend
N/A. Docker — parent only.

## Следующий шаг
→ s03 (L0 IPC → DB).
