# Реестр шагов (Decompose index)
**Plan ID:** v1-p1-storage
**План:** [plan-v1-p1-storage.md](../plan-v1-p1-storage.md)
**Дата:** 2026-07-29
**Режим:** BACK DECOMPOSE
**Уровень:** L4 (T-002 v1-p1 storage + semantic)

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали — в `sNN-*.md`. Интерфейсы — **lean** (без тел/полного кода).
> **Трекер шагов:** только этот index (не дублировать чеклисты sNN в plan).

## Контекст codebase (verified 2026-07-29)
- `apps/edge/storage/` и `apps/edge/semantic/` — **отсутствуют** (greenfield).
- `apps/edge/writer-stub/` — stub drain-only (IPC length-prefixed framing на 9009); будет заменён реальным writer.
- `migrations/versions/` — содержит `001_extensions_timescale.py` и `002_samples_hypertable.py`.
- `ship-pack/` — **отсутствует**.
 - `docker-compose.yml` — содержит `writer` (stub), `collector`, `emulator`; db/api — stubs; s01b добавил TimescaleDB dev profile.
- Канонические модели: `TelemetrySample`, `Event` в `apps/edge/collector/src/collector/domain/models.py` (T-001 upstream).
- IPC contract: `IpcCanonicalSink` + framing `<4B BE len><JSON {"type","payload"}>`.
- Alembic и базовые Timescale-миграции для `shipsense` уже заведены; semantic tree, quota/degrade ещё отсутствуют.

## Skills в контексте
| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность шагов, files/AC/TDD boundaries |
| `python-testing-patterns` | unit/integration/load тесты (586/s) |
| `supabase-postgres-best-practices` | Alembic, hypertable, policies, best practices для Timescale |
| `python-anti-patterns` | для service (writer, engine) |
| `architecture-patterns` | repo pattern, clean boundaries (T-002/T-003 injection) |

**Per-step канон** (не дублировать пути здесь): каждый `sNN` — `code_surface` + **Impl skills** по карте `back_developer/workflow-decompose.mdc`.

| `code_surface` | Шаги (storage) |
|----------------|----------------|
| `sql` | s01–s05 (+ supabase-postgres) |
| `service` | s06–s11, s13 (+ anti-patterns) |
| `model` | s05 (частично), s12, s14 |
| `infra` | s01b, s16, s17 (+ anti если lifecycle) |
| `test` | s18 (+ testing-patterns) |

## CREATIVE blockers
- CR-STO-01 chunk interval (plan §958) -> blocker for `s16-compression-policy.md`
- CR-STO-02 compression policy (plan §973) -> blocker for `s16-compression-policy.md`
- CR-STO-03 quarantine UX flags (plan §986) -> blockers for `s12-semantic-loader.md`, `s13-semantic-engine.md`, `s15-quarantine-diff.md`
- CR-STO-04 event dual-mode schema (plan §997) -> [closed: frozen core + JSONB envelope](../../creative/creative-event-dual-mode-schema.md)

**Правило:** если `CR-*` нужен для корректной реализации шага, он оформляется как **hard stop** через `needs_creative: yes (...)` в самом `sNN`. Простого упоминания в тексте шага недостаточно.
**Решение:** completed `s01–s05` остаются как уже выполненные foundation/stub. Дальше: `s06` можно делать сразу; `s07` стопится до CR-STO-04; `s12/s13/s15` стопятся до CR-STO-03; `s16` стопится до CR-STO-01/02.

## Compose / pytest execution — parent only
- Docker compose с db (timescale) — только parent.
- Load test 586/s — parent (subagent только готовит).
- Нет frontend.

## Очередь шагов
| step_id | title & files | implement | needs_creative | tdd | ac | next_phase | status |
|:---|:---|:---|:---:|:---:|:---|:---|:---|
| **s01** | [s01-db-extensions.md](s01-db-extensions.md)<br>• `migrations/versions/001_extensions_timescale.py` (create) | s01 | no | no | AC-STO-S01 | BACK IMPLEMENT | completed |
| **s01b** | [s01b-dev-db-infra.md](s01b-dev-db-infra.md)<br>• `docker-compose.yml` (modify: timescale db)<br>• `alembic.ini`, `.env.example`, `infra/timescale/README.md` | s01b | no | no | AC-STO-S01b | BACK IMPLEMENT | completed |
| **s02** | [s02-samples-hypertable.md](s02-samples-hypertable.md)<br>• `migrations/versions/002_samples_hypertable.py` (create) | s02 | no | no | AC-STO-S02 | BACK IMPLEMENT | completed |
| **s03** | [s03-events-store.md](s03-events-store.md)<br>• `migrations/versions/003_events_append_only.py` (create) | s03 | no | no | AC-STO-S03 | BACK IMPLEMENT | completed |
| **s04** | [s04-meta-health-tables.md](s04-meta-health-tables.md)<br>• `migrations/versions/004_time_semantic_health.py` (create) | s04 | no | no | AC-STO-S04 | BACK IMPLEMENT | completed |
| **s05** | [s05-sqlalchemy-models.md](s05-sqlalchemy-models.md)<br>• `apps/edge/storage/schemas.py` (create)<br>• `migrations/versions/005_quota_degrade.py` (create, частично) | s05 | no | yes | AC-STO-S05 | BACK IMPLEMENT | completed |
  | **s06** | [s06-samples-repo.md](s06-samples-repo.md)<br>• `apps/edge/storage/samples_repo.py` (create) | s06 | no | yes | AC-STO-S06 | BACK IMPLEMENT | completed |
| **s07** | [s07-events-repo.md](s07-events-repo.md)<br>• `apps/edge/storage/events_repo.py` (create) | s07 | ✅ yes (CR-STO-04 done) | yes | AC-STO-S07 | BACK IMPLEMENT | pending |
| **s08** | [s08-time-axis.md](s08-time-axis.md)<br>• `apps/edge/storage/time_axis.py` (create) | s08 | no | yes | AC-STO-S08 | BACK IMPLEMENT | pending |
| **s09** | [s09-writer-service.md](s09-writer-service.md)<br>• `apps/edge/storage/writer.py` (create) | s09 | no | yes | AC-STO-S09 | BACK IMPLEMENT | pending |
| **s10** | [s10-quota-manager.md](s10-quota-manager.md)<br>• `apps/edge/storage/quota_manager.py` (create) | s10 | no | yes | AC-STO-S10 | BACK IMPLEMENT | pending |
| **s11** | [s11-health-snapshots.md](s11-health-snapshots.md)<br>• `apps/edge/storage/health.py` (create) | s11 | no | yes | AC-STO-S11 | BACK IMPLEMENT | pending |
| **s12** | [s12-semantic-loader.md](s12-semantic-loader.md)<br>• `apps/edge/semantic/loader.py` (create)<br>• `apps/edge/semantic/models.py` (create) | s12 | **yes** (CR-STO-03) | yes | AC-STO-S12 | BACK CREATIVE | pending |
| **s13** | [s13-semantic-engine.md](s13-semantic-engine.md)<br>• `apps/edge/semantic/engine.py` (create) | s13 | **yes** (CR-STO-03) | yes | AC-STO-S13 | BACK CREATIVE | pending |
| **s14** | [s14-ship-pack-makarov.md](s14-ship-pack-makarov.md)<br>• `ship-pack/makarov/vessel.yaml` (create)<br>• `ship-pack/makarov/assets.yaml` (create)<br>• `ship-pack/makarov/tag_map.yaml` (create)<br>• `ship-pack/makarov/native_map_stub.yaml` (create)<br>• `ship-pack/makarov/timezone.yaml` (create) | s14 | no | no | AC-STO-S14 | BACK IMPLEMENT | pending |
| **s15** | [s15-quarantine-diff.md](s15-quarantine-diff.md)<br>• `apps/edge/semantic/quarantine.py` (create) | s15 | **yes** (CR-STO-03) | yes | AC-STO-S15 | BACK CREATIVE | pending |
| **s16** | [s16-compression-policy.md](s16-compression-policy.md)<br>• `migrations/versions/006_compression_retention.py` (create) | s16 | **yes** (CR-STO-01/02) | no | AC-STO-S16 | BACK CREATIVE | pending |
| **s17** | [s17-integration-t001.md](s17-integration-t001.md)<br>• `docker-compose.yml` (modify: writer → реальный, +db)<br>• `apps/edge/storage/__init__.py` (wiring) | s17 | no | no | AC-STO-S17 | BACK IMPLEMENT | pending |
| **s18** | [s18-tests-storage.md](s18-tests-storage.md)<br>• `tests/storage/` (unit + integration + load) | s18 | no | yes | AC-STO-S18 | BACK IMPLEMENT | pending |

**Оценка порядка (из плана):** s01→**s01b** (dev TimescaleDB) → s02–s05 sequential (DDL); s06 сразу; `s07` после CR-STO-04; s08–s11 без creative stop; `s12/s13/s15` после CR-STO-03; s14 параллельно; `s16` после CR-STO-01/02; s17 после T-001 s-normalizer; s18 continuous.

## Следующий режим
BACK IMPLEMENT s06-samples-repo → далее BACK CREATIVE CR-STO-04 (для s07), BACK CREATIVE CR-STO-03 (для s12/s13/s15), BACK CREATIVE CR-STO-01 CR-STO-02 (для s16) → ...

**Handoff:** см. activeContext.md после FINISH.

*Конец index decompose v1-p1-storage.*
