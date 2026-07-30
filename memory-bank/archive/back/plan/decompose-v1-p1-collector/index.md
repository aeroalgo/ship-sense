# Реестр шагов (Decompose index)
**Plan ID:** v1-p1-collector
**План:** [plan-v1-p1-collector.md](../plan-v1-p1-collector.md)
**Implement index:** [implement-v1-p1-collector/index.md](../../implement/implement-v1-p1-collector/index.md)
**Дата:** 2026-07-26
**Режим:** BACK DECOMPOSE
**Уровень:** L4 (T-001)

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали — в `sNN-*.md`. Интерфейсы — **lean** (без тел/полного кода).

> **Трекер шагов:** только этот index (не дублировать чеклисты sNN в plan).

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность шагов, files/AC/TDD boundaries |

**Per-step канон** (не дублировать пути здесь): каждый `sNN` — `code_surface` + **Impl skills** по карте `back_developer/workflow-decompose.mdc`.

| `code_surface` | Шаги (этот epic) |
|----------------|------------------|
| `model` | s01, s15 |
| `infra` | s02, s23 |
| `service` | s03–s14, s16–s18, s24 (+ anti-patterns) |
| `test` | s19–s22, s25 |

## CREATIVE blockers (до IMPLEMENT зависимых шагов)

| ID | Шаги | Артефакт | Статус |
|----|------|----------|--------|
| CR-COL-04 | s11 | `memory-bank/back/creative/v1-p1-collector/creative-collector-quality-mapping.md` | **done** (2026-07-27) ✅ |
| CR-COL-02 | s08 | `memory-bank/back/creative/v1-p1-collector/creative-collector-modbus-poll-groups.md` | **done** (2026-07-26) ✅ |
| CR-COL-01 | s04 | `memory-bank/back/creative/v1-p1-collector/creative-collector-isolation.md` | **done** (2026-07-26) |
| CR-COL-03 | s15 (+ влияет s16–s18) | [`creative-collector-emulator-fidelity.md`](../../creative/v1-p1-collector/creative-collector-emulator-fidelity.md) | **done (2026-07-27) ✅** |

**Рекомендуемый порядок CREATIVE:** CR-COL-04 → CR-COL-02 → CR-COL-01 → CR-COL-03.

**Параллельно с CREATIVE можно готовить IMPLEMENT:** s01–s03, s05, s05b, s06, s07, s09, s10, s12 (не зависят от creative).

## Очередь шагов

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **s01** | [s01-domain-models.md](s01-domain-models.md)<br>• Domain models (Quality, RawSample, TelemetrySample, Event, H | [s…](../../implement/implement-v1-p1-collector/s01-domain-models.md) | no | yes | BACK IMPLEMENT | done |
| **s02** | [s02-config-loader.md](s02-config-loader.md)<br>• Config loader + validator CLI + stub maps | [s…](../../implement/implement-v1-p1-collector/s02-config-loader.md) | no | yes | BACK IMPLEMENT | done |
| **s03** | [s03-plugin-registry.md](s03-plugin-registry.md)<br>• SourceConnector protocol + PluginRegistry + BaseSourceConnec | [s…](../../implement/implement-v1-p1-collector/s03-plugin-registry.md) | no | yes | BACK IMPLEMENT | done |
| **s04** | [s04-restart-supervisor.md](s04-restart-supervisor.md)<br>• SourceSupervisor + RestartPolicy + graceful stop | [s…](../../implement/implement-v1-p1-collector/s04-restart-supervisor.md) | yes | yes | BACK IMPLEMENT | done |
| **s05** | [s05-queues-pipeline.md](s05-queues-pipeline.md)<br>• In-proc raw/canonical queues + raw_consumer bridge | [s…](../../implement/implement-v1-p1-collector/s05-queues-pipeline.md) | no | yes | BACK IMPLEMENT | done |
| **s05b** | [s05b-ipc-to-writer.md](s05b-ipc-to-writer.md)<br>• IPC framing collector → writer (CanonicalSink client) | [s05b…](../../implement/implement-v1-p1-collector/s05b-ipc-to-writer.md) | no | yes | BACK IMPLEMENT | done |
| **s06** | [s06-modbus-decoder.md](s06-modbus-decoder.md)<br>• Modbus decoder: float32/int/bitfield/endianness | [s06…](../../implement/implement-v1-p1-collector/s06-modbus-decoder.md) | no | yes | BACK IMPLEMENT | done |
| **s07** | [s07-modbus-client.md](s07-modbus-client.md)<br>• pymodbus async client wrapper (FC03/04 only) | [s…](../../implement/implement-v1-p1-collector/s07-modbus-client.md) | no | yes | BACK IMPLEMENT | done |
| **s08** | [s08-modbus-connector.md](s08-modbus-connector.md)<br>• B2 ModbusTcpConnector + poll scheduler | [s…](../../implement/implement-v1-p1-collector/s08-modbus-connector.md) | yes | yes | BACK IMPLEMENT | done |
| **s09** | [s09-opcua-security.md](s09-opcua-security.md)<br>• OPC UA security: certs, trust store, readonly session helper | [s…](../../implement/implement-v1-p1-collector/s09-opcua-security.md) | no | yes | BACK IMPLEMENT | done |
| **s10** | [s10-opcua-connector.md](s10-opcua-connector.md)<br>• B3 OpcUaConnector: browse, subscription, reconnect | [s…](../../implement/implement-v1-p1-collector/s10-opcua-connector.md) | no | yes | BACK IMPLEMENT | done |
| **s11** | [s11-quality-engine.md](s11-quality-engine.md)<br>• Quality engine YAML rules + stale + OPC/Modbus mapping | [s…](../../implement/implement-v1-p1-collector/s11-quality-engine.md) | no | yes | BACK IMPLEMENT | done |
| **s12** | [s12-unit-converter.md](s12-unit-converter.md)<br>• Unit converter: units.yaml + scale/offset | [s…](../../implement/implement-v1-p1-collector/s12-unit-converter.md) | no | yes | BACK IMPLEMENT | done |
| **s13** | [s13-normalizer-worker.md](s13-normalizer-worker.md)<br>• B4 Normalizer: raw → TelemetrySample + Event detector | [s…](../../implement/implement-v1-p1-collector/s13-normalizer-worker.md) | no | yes | BACK QA | done |
| **s14** | [s14-health-snapshot.md](s14-health-snapshot.md)<br>• HealthAggregator + JSON snapshot writer + metrics | [s14-health-snapshot.md](../../implement/implement-v1-p1-collector/s14-health-snapshot.md) | no | yes | BACK IMPLEMENT | done |
| **s15** | [s15-emulator-tag-model.md](s15-emulator-tag-model.md)<br>• I3 emulator tag model: 586 tags + correlations + seed | [s…](../../implement/implement-v1-p1-collector/s15-emulator-tag-model.md) | yes (done) | yes | BACK IMPLEMENT | done |
| **s16** | [s16-emulator-modbus-server.md](s16-emulator-modbus-server.md)<br>• I3 Modbus TCP server adapter | [s…](../../implement/implement-v1-p1-collector/s16-emulator-modbus-server.md) | no | yes | BACK IMPLEMENT | done |
| **s17** | [s17-emulator-opcua-server.md](s17-emulator-opcua-server.md)<br>• I3 OPC UA server adapter | [s…](../../implement/implement-v1-p1-collector/s17-emulator-opcua-server.md) | no | yes | BACK IMPLEMENT | done |
| **s18** | [s18-emulator-dirt.md](s18-emulator-dirt.md)<br>• I3 ScenarioRunner + all dirt injectors | [s…](../../implement/implement-v1-p1-collector/s18-emulator-dirt.md) | no | yes | BACK IMPLEMENT | done |
| **s19** | [s19-integration-modbus.md](s19-integration-modbus.md)<br>• Integration: collector B2 ↔ emulator Modbus | [s19-integration-modbus.md](../../implement/implement-v1-p1-collector/s19-integration-modbus.md) | no | yes | BACK IMPLEMENT | done |
| **s20** | [s20-integration-opcua.md](s20-integration-opcua.md)<br>• Integration: collector B3 ↔ emulator OPC UA | [s…](../../implement/implement-v1-p1-collector/s20-integration-opcua.md) | no | yes | BACK IMPLEMENT | done |
| **s21** | [s21-integration-dual-source.md](s21-integration-dual-source.md)<br>• Integration: dual source isolation + dual protocol | [s…](../../implement/implement-v1-p1-collector/s21-integration-dual-source.md) | no | yes | BACK IMPLEMENT | done |
| **s22** | [s22-integration-dirty-t3.md](s22-integration-dirty-t3.md)<br>• Integration: all dirt scenarios through B4 | [s…](../../implement/implement-v1-p1-collector/s22-integration-dirty-t3.md) | no | yes | BACK IMPLEMENT | done |
| **s23** | [s23-docker-compose.md](s23-docker-compose.md)<br>• Docker Compose: emulator + collector + writer + deps | [s23…](../../implement/implement-v1-p1-collector/s23-docker-compose.md) | no | no | BACK IMPLEMENT | done |
| **s24** | [s24-stub-plugin-demo.md](s24-stub-plugin-demo.md)<br>• Demo third-party stub plugin (AC-B1-08) | [s…](../../implement/implement-v1-p1-collector/s24-stub-plugin-demo.md) | no | yes | BACK IMPLEMENT | done |
| **s25** | [s25-soak-t1-fragment.md](s25-soak-t1-fragment.md)<br>• Soak T1 fragment: 24h harness + leak checks | [s…](../../implement/implement-v1-p1-collector/s25-soak-t1-fragment.md) | no | yes | BACK IMPLEMENT | done |
| **s26** | runtime gap-close R-1/R-2/R-3<br>• periodic health snapshot, configured source/IPC bootstrap, typed OPC UA writes | [s26-runtime-gaps-r1-r3.md](../../implement/implement-v1-p1-collector/s26-runtime-gaps-r1-r3.md) | no | yes | BACK QA | done |

Статусы: `pending` | `active` | `done` | `blocked` | `needs_creative`

> **Gap-close note:** s26 — отдельный runtime-gap step после QA T-001; он не заменяет исходные s01–s25, а закрывает compose/runtime asymmetry R-1/R-2/R-3.


## Summary-чеклист

- [x] s01 — Domain models (Quality, RawSample, TelemetrySample, Event, Health)
- [x] s02 — Config loader + validator CLI + stub maps
- [x] s03 — SourceConnector protocol + PluginRegistry + BaseSourceConnector
- [x] s04 — SourceSupervisor + RestartPolicy + graceful stop
- [x] s05 — In-proc raw/canonical queues + raw_consumer bridge
- [x] s05b — IPC framing collector → writer (CanonicalSink client)
- [x] s06 — Modbus decoder: float32/int/bitfield/endianness
- [x] s07 — pymodbus async client wrapper (FC03/04 only)
- [x] s08 — B2 ModbusTcpConnector + poll scheduler
- [x] s09 — OPC UA security: certs, trust store, readonly session helpers
- [x] s10 — B3 OpcUaConnector: browse, subscription, reconnect
- [x] s11 — Quality engine YAML rules + stale + OPC/Modbus mapping
- [x] s12 — Unit converter: units.yaml + scale/offset
- [x] s13 — B4 Normalizer: raw → TelemetrySample + Event detector
- [x] s14 — HealthAggregator + JSON snapshot writer + metrics
- [x] s15 — I3 emulator tag model: 586 tags + correlations + seed (implemented 2026-07-27)
- [x] s16 — I3 Modbus TCP server adapter
- [x] s17 — I3 OPC UA server adapter
- [x] s18 — I3 ScenarioRunner + all dirt injectors
- [x] s19 — Integration: collector B2 ↔ emulator Modbus
- [x] s20 — Integration: collector B3 ↔ emulator OPC UA
- [x] s21 — Integration: dual source isolation + dual protocol
- [x] s22 — Integration: all dirt scenarios through B4
- [x] s23 — Docker Compose: emulator + collector + writer + deps (done 2026-07-27; caveat: emulator production-start crash → BACK BUGFIX)
- [x] s24 — Demo third-party stub plugin (AC-B1-08)
- [x] s25 — Soak T1 fragment: 24h harness + leak checks (implemented; short soak green; 24h manual remains operator run)

## Handoff

### H-1. Исходная декомпозиция T-001

- **Done:** BACK DECOMPOSE T-001 — исходные шаги s01–s25 + s05b реализованы; s25 checklist синхронизирован.
- **Canonical directory:** `memory-bank/back/plan/decompose-v1-p1-collector/`.
- **Implement hub:** `memory-bank/back/implement/implement-v1-p1-collector/index.md`.
- **QA artifact:** `memory-bank/back/qa/v1-p1-collector/qa-20260727-v1-p1-collector.md`.
- **Creative blockers:** CR-COL-01, CR-COL-02, CR-COL-03, CR-COL-04 закрыты; новые creative-решения для R-1/R-2/R-3 не требуются.

### H-2. QA finding → runtime gap-close

BACK QA зафиксировал: backend regression **259 passed**, short soak **1 passed**, compose syntax/build passed, но compose smoke был заблокирован тремя runtime-асимметриями:

- **R-1:** snapshot создавался только при `CollectorApp.stop()`, поэтому compose healthcheck не находил `/var/lib/shipsense/health/collector.json` во время работы.
- **R-2:** `SHIPSSENSE_WRITER_ENDPOINT` был только в compose; production entrypoint создавал `NullSink`, noop sources и фактически не передавал telemetry в writer.
- **R-3:** OPC UA ticker передавал значения с Python-типами, отличными от объявленного `ua.VariantType`; full profile выдавал `Write refused`.

### H-3. Выполненный gap-close step s26

- **Step:** [s26-runtime-gaps-r1-r3.md](../../implement/implement-v1-p1-collector/s26-runtime-gaps-r1-r3.md).
- **Status:** done; следующий переход — `BACK QA`.
- **R-1 implementation:** periodic `SnapshotWriter` lifecycle; initial running snapshot, refresh loop, final stopped snapshot.
- **R-2 implementation:** runtime bootstrap читает config/env, фильтрует sources, регистрирует Modbus/OPC UA factories, создаёт `SourceSupervisor`, `Normalizer` и `IpcCanonicalSink`; `PluginRegistry` принимает class/factory.
- **R-3 implementation:** emulator сохраняет declared node variant types и coercion values перед `write_value()`.
- **Regression evidence:** targeted runtime suite **29 passed**; compileall **PASS**.

### H-4. Файлы, затронутые s26

- `apps/edge/collector/src/collector/runtime/__init__.py`
- `apps/edge/collector/src/collector/runtime/endpoints.py`
- `apps/edge/collector/src/collector/runtime/bootstrap.py`
- `apps/edge/collector/src/collector/__main__.py`
- `apps/edge/collector/src/collector/app.py`
- `apps/edge/collector/src/collector/health/snapshot_writer.py`
- `apps/edge/collector/src/collector/core/supervisor.py`
- `apps/edge/collector/src/collector/plugins/registry.py`
- `apps/edge/emulator/src/emulator/protocols/opcua_server.py`
- `apps/edge/collector/tests/unit/test_runtime_gaps.py`

### H-5. Обязательный следующий шаг: BACK QA

Запустить в новом QA-чате:

1. Полный collector + emulator pytest regression.
2. Короткий soak и compileall.
3. `docker compose config --quiet`.
4. `docker compose build emulator collector writer`.
5. `docker compose up -d emulator writer collector`.
6. Дождаться `healthy` для всех трёх сервисов.
7. Проверить snapshot JSON: `collector_state=running`, sources ≥ 1.
8. Проверить writer frames / `total_samples > 0`.
9. Проверить отсутствие `Write refused` в emulator logs.
10. Проверить `docker compose stop collector` и exit code 0.

**QA evidence required:** command, exit status, pass/fail count, relevant log snippets, compose status и список оставшихся blockers. До этого T-001 не закрывать как compose-smoke green.

- **load_now:** `memory-bank/back/qa/v1-p1-collector/qa-20260727-v1-p1-collector.md`; затем s26 implement artifact и изменённые runtime-файлы.
- **Tool / model:** Claude Code + premium-coding.
- **New chat:** yes — IMPLEMENT → QA transition.

### H-6. Обновление activeContext после QA

После успешного `BACK QA` обновить `memory-bank/activeContext.md`:

- перенести R-1/R-2/R-3 из blockers в done;
- добавить фактические compose evidence и counts;
- установить следующий шаг T-001 или следующий task согласно QA verdict;
- сохранить ссылку на новый QA artifact.

Если QA выявит новые runtime blockers, добавить новый append-only gap/bugfix shard, не переписывая историю s26.

---

## Следующий режим

→ `BACK QA` в новом чате по s26/R-1/R-2/R-3.

→ После QA pass: `BACK REFLECT` → `BACK ARCHIVE NOW`.

→ При compose/runtime failure: новый append-only `BACK BUGFIX` или gap-close shard с отдельным handoff.

**Источник истины по статусу:** implement s26 artifact + этот decompose index; index implement используется только для навигации.

---

## Финальный handoff

- **Done:** исходные s01–s25 + s05b и runtime gap-close s26 выполнены.
- **Not yet done:** compose smoke acceptance T-001; это обязанность `BACK QA`.
- **Current next:** `BACK QA`.
- **Artifacts:** decompose index, s26 implement artifact, QA artifact.
- **Code graph:** обновлён после s26 через `.venv/bin/graphify update .`.
- **New chat:** yes.

---

## Handoff checklist

- [x] Исходные decompose steps s01–s25 + s05b зафиксированы.
- [x] Creative blockers закрыты.
- [x] QA blockers R-1/R-2/R-3 описаны.
- [x] s26 implement artifact добавлен.
- [x] Targeted tests: 29 passed.
- [x] Compileall: passed.
- [x] Graphify update выполнен.
- [x] Full BACK QA выполнен. ([qa-20260730](../../qa/v1-p1-collector/qa-20260730-v1-p1-collector.md) PASS)
- [x] Compose smoke green.
- [x] Writer frames подтверждены (SQL samples TAI410*).
- [x] `Write refused` отсутствует.
- [x] T-001 QA PASS; REFLECT done → next ARCHIVE NOW.
