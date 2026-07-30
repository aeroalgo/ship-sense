# BACK REFLECT — T-001 / v1-p1-collector

**Дата:** 2026-07-30  
**Уровень:** L4  
**Статус:** completed  
**Основание:** [Epic QA PASS (re-QA)](../../archive/back/qa/v1-p1-collector/qa-20260730-v1-p1-collector.md) · fail→fix путь: [QA-20260727](../../archive/back/qa/v1-p1-collector/qa-20260727-v1-p1-collector.md) → [s26](../../archive/back/implement/implement-v1-p1-collector/s26-runtime-gaps-r1-r3.md)  
**Scope:** s01–s26 (+ s05b), I3/B1–B4, compose smoke; gap-close R-1/R-2/R-3

## Сравнение с планом и decompose

План L4 требовал read-only конвейер: эмулятор I3 (Modbus+OPC UA) → plugin framework B1 → B2/B3 → B4 normalizer → canonical stream + health; Docker Compose обмен; dirt T3; soak fragment T1. Writer/DB — контракт стыка, не полный T-002.

Decompose закрыт целиком:

- **s01–s14** — domain, config, plugins, supervisor, queues, IPC sink, Modbus/OPC UA, quality/units/normalizer, health.
- **s15–s18** — emulator tag model (~586), Modbus/OPC UA servers, dirt ScenarioRunner.
- **s19–s22** — integration Modbus/OPC UA/dual/dirt.
- **s23–s25** — compose, stub plugin, soak harness (короткий green; 24h — operator).
- **s26** — runtime gap-close после первого QA fail (не в исходном s01–s25).

CREATIVE CR-COL-01..04 закрыты до зависимых шагов. BUGFIX Modbus SimData overlap разблокировал full-profile emulator.

**DoD плана vs факт:**

| DoD / AC-класс | Итог |
|----------------|------|
| I3 оба протокола + ~586 stub | да (pytest + emulator); day-1 compose smoke — 3 тега @1 Hz (`SHIPSSENSE_SMOKE_SOURCES=aps_main`) по edge-runtime-smoke |
| B1 N≥2 / isolation | да (s21 + suite) |
| B2/B3 plugins → RawSample | да |
| B4 quality + dual ts + units | да |
| Health snapshot наружу | да после R-1 (periodic SnapshotWriter) |
| Dirt T3 YAML | да (s18/s22) |
| Soak 24h | фрагмент/short green; полный 24h не гонялся |
| Compose emulator↔collector(+writer) | да после s26 re-QA (SQL samples live) |

Ограничения не скрыты: R-4 (ruff не в venv), O-1 (Modbus health counters=0 при live), полный 586@1Hz compose smoke ослаблен day-1, 24h soak — manual.

## Что сработало

1. CREATIVE до IMPLEMENT (poll groups, isolation, quality map, emulator fidelity) снял архитектурные споры с критического пути кода.
2. TDD на connector/emulator/integration поймал overlap SimData, datatype OPC UA и noop production entrypoint раньше, чем «всё зелёное в unit» закрыло эпик.
3. Первый Epic QA **fail** с явными R-1/R-2/R-3 оказался полезнее ложного pass: gap-close s26 + re-QA дали live SQL evidence, а не только in-proc queues.
4. Разделение pytest regression (333) и compose smoke (healthy + SQL + SIGTERM 0) зафиксировало §0.11 env/health/IPC counterparts.
5. PluginRegistry class|factory + bootstrap из YAML/env сделали production path симметричным тестам без NullSink по умолчанию.
6. Fail-loud: compose unhealthy / Write refused / empty health path — диагностируемы без fallback.

## Проблемы и их разрешение

- **SimData overlap (full tags_stub):** один SimData на сигнал → crash; merge в register image на блок (BUGFIX 2026-07-27).
- **R-1:** snapshot только на stop → compose healthcheck fail; periodic SnapshotWriter lifecycle.
- **R-2:** compose `SHIPSSENSE_WRITER_ENDPOINT` без consumer → NullSink/noop; runtime bootstrap + IpcCanonicalSink.
- **R-3:** OPC UA Python types ≠ declared VariantType → Write refused; coerce по declared type.
- **Порты 5020/4840/9009:** pytest hang если compose up; канон — `docker compose stop` перед suite (зафиксировано в QA).
- **AC-INT-03 ~586:** day-1 ослаблен осознанно в edge-runtime-smoke; не маскировать как полный throughput smoke.

## Уроки

- Production entrypoint и compose env обязаны входить в AC compose smoke с первого QA, иначе unit/integration green ≠ edge stack.
- Healthcheck path — контракт runtime↔compose: файл/HTTP должен существовать **во время** `running`, не только на shutdown.
- Emulator full profile ≠ mini integration profile: overlap/datatype проявляются только на 586-карте.
- Gap-close лучше отдельным sNN + re-QA, чем тихим патчем без evidence.
- Low issues (ruff, health counters) держать out_of_scope Fix plan, чтобы не блокировать ARCHIVE при PASS.

## Улучшения процесса (L4 / cross-cutting)

1. В PLAN/DECOMPOSE явно ставить шаг «production bootstrap + compose env counterparts» до Epic QA, не после fail.
2. Добавить в QA checklist: free ports / `compose stop` перед collector+emulator suite.
3. Завести optional follow-up TASK: Modbus health counters (O-1) + ruff в `.venv` (R-4).
4. Отдельный scheduled/operator run: 24h soak + полный 586 smoke profile — не смешивать с day-1 PASS.
5. При ARCHIVE: перенести `plan|decompose|implement|creative|qa|bugfix` под `v1-p1-collector`; `plan-v1-p1-edge-runtime-smoke.md` — решить: в составе T-001 archive или отдельный живой gap-doc (сейчас ссылка из tasks/QA).

## Архитектурные заметки

- Канонический контур: `SourceSupervisor` → raw queue → `Normalizer` → `IpcCanonicalSink` → writer:9009 → Timescale `samples` — доказан live SQL (TAI410*).
- Isolation источников (CR-COL-01) и poll groups (CR-COL-02) остались опорой B1/B2 под нагрузкой dual-source.
- Quality mapping (CR-COL-04) связал OPC StatusCode / Modbus errors с единым quality без ad-hoc в connectors.
- Граница T-001/T-002 соблюдена: collector производит canonical+IPC; persistence — writer/storage.

## Итог

T-001 / `v1-p1-collector` завершён: s01–s26 done, Epic QA PASS (333 pytest + compose smoke), blockers нет. Следующий workflow — `BACK ARCHIVE NOW`; `code_changed` для REFLECT = no.
