# Реестр шагов (Decompose index)
**Plan ID:** v1-p1-pipeline-db-e2e
**План:** [plan-v1-p1-pipeline-db-e2e.md](../plan-v1-p1-pipeline-db-e2e.md)
**Родители:** [decompose-v1-p1-storage](../decompose-v1-p1-storage/index.md) · [decompose-v1-p1-mqtt-smoke](../decompose-v1-p1-mqtt-smoke/index.md) · [plan-v1-p1-edge-runtime-smoke](../plan-v1-p1-edge-runtime-smoke.md)
**Implement index:** [implement-v1-p1-pipeline-db-e2e/index.md](../../implement/implement-v1-p1-pipeline-db-e2e/index.md)
**Дата:** 2026-07-29
**Режим:** BACK DECOMPOSE
**Уровень:** L3 (T-002 gap-close persistence E2E)

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали — в `sNN-*.md`. Интерфейсы — **lean** (без тел/полного кода).
> **Трекер шагов:** только этот index (не дублировать чеклисты sNN в plan).

## Контекст codebase (verified 2026-07-29)
- `WriterService.run_tcp(host, port)` есть; **`start_tcp` нет** — нельзя взять bound port при `port=0` (ADR-PIPE-003 → s01).
- `IpcCanonicalSink`, framing, `SamplesRepo`/`EventsRepo`, alembic 001–006, compose writer/db — готовы (T-002 s01–s18 + BUGFIX).
- MQTT path: `MqttPublisherAdapter`, mosquitto `mqtt-dev`, collector MQTT stack — доказаны до MockSink / samples/sec (не до SQL).
- Modbus path: `ModbusServerAdapter` + connector fixtures — in-memory IntegrationSink, не IPC→DB.
- `tests/pipeline/` — **отсутствует** (создаётся s02+).
- `scripts/smoke-pipeline-db.sh` — **отсутствует** (s07).

## Skills в контексте
| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность, files/AC/TDD boundaries |
| `brainstorming` | ADR L0/L1/L2 уже в plan — без новых CR |

**Per-step канон** (не дублировать пути здесь): каждый `sNN` — `code_surface` + **Impl skills** по карте `back_developer/workflow-decompose.mdc`.

| `code_surface` | Шаги |
|----------------|------|
| `service` | s01 (+ anti-patterns) |
| `infra` | s02 (+ anti-patterns: lifecycle), s07 (+ anti-patterns), s08 |
| `test` | s03, s04, s05, s06 |

## CREATIVE blockers
Нет. Framing/Writer/Timescale/MQTT/compose уже спроектированы. План §12: CREATIVE не нужен. Нерешённых `CR-*` нет.

## Docker / compose — parent only
L0/L1 (testcontainers) и L2 (`docker compose`) — запускает **parent**. Subagent готовит файлы/фикстуры, не поднимает Docker. FRONT N/A; HARD RULE `front-tests-parent-only.mdc` вставлять при spawn.

## Очередь шагов
| step_id | title & files | implement | needs_creative | tdd | ac | next_phase | status |
|:---|:---|:---|:---:|:---:|:---|:---|:---|
| **s01** | [s01-writer-start-tcp.md](s01-writer-start-tcp.md)<br>• `apps/edge/storage/writer.py`<br>• unit `tests/storage/test_writer_start_tcp.py` | [s01](../../implement/implement-v1-p1-pipeline-db-e2e/s01-writer-start-tcp.md) | no | yes | AC-PIPE-06 | BACK IMPLEMENT | completed |
| **s02** | [s02-timescale-testcontainer-fixture.md](s02-timescale-testcontainer-fixture.md)<br>• `tests/pipeline/__init__.py`<br>• `tests/pipeline/conftest.py` | [s02](../../implement/implement-v1-p1-pipeline-db-e2e/s02-timescale-testcontainer-fixture.md) | no | yes | infra ADR-PIPE-002 | BACK IMPLEMENT | completed |
| **s03** | [s03-l0-writer-ipc-db.md](s03-l0-writer-ipc-db.md)<br>• `tests/pipeline/test_writer_ipc_db.py` | [s03](../../implement/implement-v1-p1-pipeline-db-e2e/s03-l0-writer-ipc-db.md) | no | yes | AC-PIPE-01, AC-PIPE-02 | BACK IMPLEMENT | completed |
| **s04** | [s04-l1-mqtt-pipeline-samples.md](s04-l1-mqtt-pipeline-samples.md)<br>• `tests/pipeline/test_mqtt_pipeline_db.py` | [s04](../../implement/implement-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md) | no | yes | AC-PIPE-03 | BACK IMPLEMENT | completed |
| **s05** | [s05-l1-mqtt-lifecycle-events.md](s05-l1-mqtt-lifecycle-events.md)<br>• `tests/pipeline/test_mqtt_pipeline_db.py` (дополнить) | [s05](../../implement/implement-v1-p1-pipeline-db-e2e/s05-l1-mqtt-lifecycle-events.md) | no | yes | AC-PIPE-04 | BACK IMPLEMENT | pending |
| **s06** | [s06-l1-modbus-pipeline-samples.md](s06-l1-modbus-pipeline-samples.md)<br>• `tests/pipeline/test_modbus_pipeline_db.py` | [s06](../../implement/implement-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md) | no | yes | AC-PIPE-05 | BACK IMPLEMENT | pending |
| **s07** | [s07-compose-smoke-pipeline-db.md](s07-compose-smoke-pipeline-db.md)<br>• `scripts/smoke-pipeline-db.sh`<br>• optional `tests/pipeline/test_compose_db_smoke.py`<br>• `docker-compose.yml` (если flaky) | [s07](../../implement/implement-v1-p1-pipeline-db-e2e/s07-compose-smoke-pipeline-db.md) | no | no | AC-PIPE-07, AC-PIPE-08 | BACK IMPLEMENT | pending |
| **s08** | [s08-docs-matrix-markers.md](s08-docs-matrix-markers.md)<br>• `pyproject.toml` testpaths/markers<br>• README matrix | [s08](../../implement/implement-v1-p1-pipeline-db-e2e/s08-docs-matrix-markers.md) | no | no | AC-PIPE-09, AC-PIPE-10 | BACK IMPLEMENT | pending |

## Порядок выполнения
s01 → s02 → s03 → s04 → s05 → s06 → s07 → s08.
s05 зависит от s04 (тот же файл + MQTT harness). s03–s06 зависят от s01+s02. s07 независим от L1 по коду, но логически после L0 green.

## AC coverage
| AC | Шаг |
|----|-----|
| AC-PIPE-01 | s03 |
| AC-PIPE-02 | s03 |
| AC-PIPE-03 | s04 |
| AC-PIPE-04 | s05 |
| AC-PIPE-05 | s06 |
| AC-PIPE-06 | s01 (+ подтверждение в s03) |
| AC-PIPE-07 | s07 |
| AC-PIPE-08 | s07 |
| AC-PIPE-09 | s08 |
| AC-PIPE-10 | s08 |

## Summary-чеклист
- [ ] s01 — WriterService.start_tcp
- [ ] s02 — Timescale testcontainer + alembic fixture
- [ ] s03 — L0 IPC → samples/events
- [ ] s04 — L1 MQTT → samples
- [ ] s05 — L1 MQTT lifecycle → events
- [ ] s06 — L1 Modbus → samples
- [ ] s07 — compose smoke script
- [ ] s08 — docs matrix + markers

## Handoff
- **Next:** BACK IMPLEMENT s02 — Timescale testcontainer fixture
- **load_now:** `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s02-timescale-testcontainer-fixture.md`
- **CREATIVE:** нет → сразу IMPLEMENT (s02)

---

*2026-07-29 — BACK DECOMPOSE v1-p1-pipeline-db-e2e. 8 шагов, AC-PIPE-01..10 covered.*
