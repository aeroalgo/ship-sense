# BACK REFLECT — T-002 / v1-p1-storage

**Дата:** 2026-07-30  
**Уровень:** L4  
**Статус:** completed  
**Основание:** [Epic QA PASS (re-QA)](../../archive/back/qa/v1-p1-storage/qa-20260730-v1-p1-storage-reqa.md) · путь: [QA-0729 blocked](../../archive/back/qa/v1-p1-storage/qa-20260729-v1-p1-storage.md) → [BUGFIX package-path](../../archive/back/bugfix/v1-p1-storage/bugfix-20260729-package-path-compose-runtime.md) → [QA-0730 blocked](../../archive/back/qa/v1-p1-storage/qa-20260730-v1-p1-storage.md) → [BUGFIX runtime](../../archive/back/bugfix/v1-p1-storage/bugfix-20260730-qa-storage-runtime.md) → re-QA PASS  
**Scope:** s01–s18 (+ s01b); CR-STO-01..04. Pipeline-db-e2e — отдельный epic (уже archived + [reflection](reflection-T-002-v1-p1-pipeline-db-e2e.md)).

## Сравнение с планом и decompose

План L4: Timescale samples (B5), append-only events (B6), time axis (B7), semantic + ship-pack ~586 KKS (B8), WriterService IPC batch, quota 80%, health snapshots, compression/retention. Не shore/API.

Decompose **s01–s18 completed**:

| Блок | Шаги | Итог |
|------|------|------|
| DDL / infra | s01, s01b, s02–s05, s16 | extensions, Timescale compose, hypertables, events, meta/quota, models, compression/retention |
| Repos / services | s06–s11 | samples/events repos, time axis, writer, quota, health |
| Semantic | s12–s15 | loader, engine, ship-pack makarov, quarantine |
| Wire / prove | s17–s18 | real writer compose + T-001; unit/integration/load harness |

CREATIVE CR-STO-01/02 (chunk/compression), CR-STO-03 (quarantine UX), CR-STO-04 (event dual-mode) закрыты до зависимых шагов.

**DoD vs факт:** writer принимает IPC → samples/events; live counts (re-QA: samples>200k, events>4k); semantic/quarantine/quota/health tables; Alembic через 006; full suite **400 passed**; lint tools (ruff/mypy/…) — out of scope (нет в `.venv`).

## Что сработало

1. Greenfield `apps/edge/storage` + `semantic` с чёткими repo boundaries под T-003 injection.
2. CREATIVE до s07/s12/s16 снял schema/UX споры с критического пути.
3. Load harness 586/s в s18 дал throughput contract без подмены live compose.
4. Два цикла QA→BUGFIX→re-QA: package-path/compose, затем ModbusException/compression idempotency/mqtt timeout — без fallback-маскировки.
5. §0.11: `DATABASE_URL`, `SHIPSSENSE_WRITER_ENDPOINT`, map ⊆ emulator — зафиксированы тестами и live SQL.
6. Reviewer gate на re-QA подтвердил AC+/AC−/§0.11 при PASS.

## Проблемы и их разрешение

- **Package path / collection:** pytest без `PYTHONPATH` / layout — BUGFIX 2026-07-29.
- **Compose stub writer + collector restart:** замена на `shipsense/writer:dev`, wiring s17.
- **ModbusException flood:** exception → quality bad; sources map ⊆ emulator stub (3 тега).
- **Compression policy already exists:** `if_not_exists => true` + idempotent migration test.
- **MQTT E2E hang в full suite:** broker fixture timeout 60s → 400 passed terminal.
- **Lint tools missing:** явно out of scope, не blocker PASS.

## Уроки

- Live compose acceptance = healthy services **и** чистые runtime logs, не только SQL counts.
- Migration policies Timescale требуют idempotent create с первого merge в shared DB.
- Dev tag-map должен быть subset emulator profile до compose smoke — иначе exception flood.
- Full suite (вкл. slow) обязателен для Epic QA PASS; non-slow green ≠ PASS.
- Отдельный pipeline-db-e2e epic после storage — правильное разделение: storage contracts vs end-to-end path proof.

## Улучшения процесса

1. В s17 AC явно: «logs free of ModbusException / compression already exists».
2. Bootstrap `.venv` с ruff (или документированный skip) до Epic QA, чтобы не тащить QA-3.
3. Контрактный тест map⊆emulator — шаблон для любых compose source profiles.
4. При ARCHIVE: перенести `v1-p1-storage` plan/decompose/implement/creative/qa/bugfix; reflection остаётся; pipeline reflection уже на месте.
5. Follow-up: T-003 API поверх samples/events/NOTIFY.

## Архитектурные заметки

- Контур: collector IPC → WriterService → SamplesRepo/EventsRepo → Timescale; SemanticEngine/quarantine — side path для map reconcile.
- Event dual-mode (CR-STO-04): frozen core + JSONB envelope — стык MQTT native и reconstructed.
- Compression segmentby `tag_id` / orderby `ts DESC` (CR-STO-01/02) — day-1 retention policy в 006.

## Итог

T-002 / `v1-p1-storage` завершён: s01–s18 done, Epic QA PASS (400 full suite + live DB), blockers нет. Следующий workflow — `BACK ARCHIVE NOW v1-p1-storage`; `code_changed` для REFLECT = no.
