# Implement index — v1-p1-pipeline-db-e2e

**Plan ID:** v1-p1-pipeline-db-e2e  
**Дата:** 2026-07-30  
**Режим:** BACK IMPLEMENT

**Plan:** [plan-v1-p1-pipeline-db-e2e.md](../../plan/plan-v1-p1-pipeline-db-e2e.md)  
**Decompose:** [decompose-v1-p1-pipeline-db-e2e/index.md](../../plan/decompose-v1-p1-pipeline-db-e2e/index.md)

Каждый шаг = один заход IMPLEMENT. Имена файлов совпадают с decompose: `sNN-<slug>.md`.

| step | decompose | implement |
| :--- | :--- | :--- |
| **s01** | [s01-writer-start-tcp.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s01-writer-start-tcp.md) | [s01-writer-start-tcp.md](s01-writer-start-tcp.md) |
| **s02** | [s02-timescale-testcontainer-fixture.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s02-timescale-testcontainer-fixture.md) | [s02-timescale-testcontainer-fixture.md](s02-timescale-testcontainer-fixture.md) |
| **s03** | [s03-l0-writer-ipc-db.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s03-l0-writer-ipc-db.md) | [s03-l0-writer-ipc-db.md](s03-l0-writer-ipc-db.md) |
| **s04** | [s04-l1-mqtt-pipeline-samples.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md) | — |
| **s05** | [s05-l1-mqtt-lifecycle-events.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s05-l1-mqtt-lifecycle-events.md) | — |
| **s06** | [s06-l1-modbus-pipeline-samples.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md) | [s06-l1-modbus-pipeline-samples.md](s06-l1-modbus-pipeline-samples.md) |
| **s07** | [s07-compose-smoke-pipeline-db.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s07-compose-smoke-pipeline-db.md) | [s07-compose-smoke-pipeline-db.md](s07-compose-smoke-pipeline-db.md) |
| **s08** | [s08-docs-matrix-markers.md](../../plan/decompose-v1-p1-pipeline-db-e2e/s08-docs-matrix-markers.md) | [s08-docs-matrix-markers.md](s08-docs-matrix-markers.md) |

## QA

- (будет после epic complete) — BACK QA v1-p1-pipeline-db-e2e
