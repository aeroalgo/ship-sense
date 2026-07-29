# Шаг s17: T-001 integration (collector IPC → real writer in compose)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-STO-S17 (из плана §231–232, §1168–1174: emulator → normalizer → writer → DB rows match ±dedup; T-003 import repos; compose wiring)
**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python.SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Провести интеграцию: заменить writer-stub на реальный writer (storage), добавить db сервис (timescale) в compose, настроить зависимости collector → writer+db, endpoint SHIPSSENSE_WRITER_ENDPOINT, healthchecks; убедиться, что T-001 canonical → writer → persisted count совпадает; T-003 может import SemanticEngine, SamplesRepo, EventsRepo без циклов.

## Контекст
- **Consumes:** s09 writer-service (IPC listener), s06–s08 repos, T-001 (IpcCanonicalSink + normalizer complete), s14 ship-pack, s12–s13 semantic.
- **Produces:** обновлённый docker-compose.yml; wiring в storage; интеграционный тест.
- **Downstream:** full edge stack smoke, T-003.
- **План:** §231 (integration gate), §1174 (compose), §232 (T-003 import).

## Файлы
- `docker-compose.yml` (Модификация: +db timescale, writer (реальный вместо stub), collector depends writer+db, volumes tsdata, env SHIPSSENSE_*, healthchecks)
- `apps/edge/storage/__init__.py` (Update — public exports: SamplesRepo, EventsRepo, SemanticEngine, WriterService)
- `infra/timescale/` (опционально .conf или init скрипт если нужно)
- Интеграционный тест в tests/ (или collector integration)

## Интерфейсы (lean — без кода)
- compose service `db`: image timescale/timescaledb:2.14.2-pg16, volumes, shm, tuned postgres conf (из плана §1160).
- `writer`: build apps/edge/storage (или dedicated), command на writer entry, depends db, health via table or port.
- collector: env SHIPSSENSE_WRITER_ENDPOINT=writer:9009, depends db+writer.
- `alembic upgrade head` в entry writer/db init.
- NOTIFY после writer commit.

## TDD
- **Нет** в этом шаге (интеграция).
- Верификация: docker compose up (parent), emulator → collector → writer → count в samples/events; targeted integration test.
- `python -c "from storage import SamplesRepo, SemanticEngine; ..."` из T-003 контекста.

## Подробный процесс выполнения
1. Добавить db сервис (точно как в плане §1149–1172).
2. Заменить writer: context apps/edge/storage (или переименовать writer-stub → writer после), command python -m storage.writer или entry.
3. collector: добавить depends_on db (healthy), env writer endpoint.
4. Миграции: в writer entrypoint или отдельный init контейнер — alembic upgrade head перед run.
5. Health: db healthcheck + writer health после tables.
6. Semantic load: writer и api загружают ship-pack при старте.
7. Smoke: docker compose --profile edge up; проверить row counts, NOTIFY.
8. T-003 import gate: в отдельном тесте (не ломает циклы).

## Верификация
- Integration gate: emulator → ... → DB row count matches injected ±dedup.
- T-003 imports succeed.
- Блокер: s09 (writer runnable), T-001 s-normalizer complete, s01–s05 (tables), s14 (pack).

## Блокеры / CREATIVE
Зависит от T-001 canonical contract финализации.
