# Implement index — T-001 v1 p1 collector

**Plan ID:** v1-p1-collector  
**Дата:** 2026-07-26  
**Режим:** BACK IMPLEMENT

**Plan:** [plan-v1-p1-collector.md](../../plan/plan-v1-p1-collector.md)  
**Decompose:** [decompose-v1-p1-collector/index.md](../../plan/decompose-v1-p1-collector/index.md)

## Реестр шагов (decompose ↔ implement)

> Статусы — только в `implement/sNN-*.yaml` (источник истины) и `decompose/index.md` (агрегатор). Этот файл — навигационный портал для INTEG.

| step | decompose | implement |
| :--- | :--- | :--- |
| **s01** | [s01-domain-models.md](../../plan/decompose-v1-p1-collector/s01-domain-models.md) | [s01-domain-models.md](s01-domain-models.md) |
| **s02** | [s02-config-loader.md](../../plan/decompose-v1-p1-collector/s02-config-loader.md) | [s02-config-loader.md](s02-config-loader.md) |
| **s03** | [s03-plugin-registry.md](../../plan/decompose-v1-p1-collector/s03-plugin-registry.md) | [s03-plugin-registry.md](s03-plugin-registry.md) |
| **s04** | [s04-restart-supervisor.md](../../plan/decompose-v1-p1-collector/s04-restart-supervisor.md) | [s04-restart-supervisor.md](s04-restart-supervisor.md) |
| **s05** | [s05-queues-pipeline.md](../../plan/decompose-v1-p1-collector/s05-queues-pipeline.md) | [s05-queues-pipeline.md](s05-queues-pipeline.md) |
| **s05b** | [s05b-ipc-to-writer.md](../../plan/decompose-v1-p1-collector/s05b-ipc-to-writer.md) | [s05b-ipc-to-writer.md](s05b-ipc-to-writer.md) |
| **s06** | [s06-modbus-decoder.md](../../plan/decompose-v1-p1-collector/s06-modbus-decoder.md) | [s06-modbus-decoder.md](s06-modbus-decoder.md) |
| **s07** | [s07-modbus-client.md](../../plan/decompose-v1-p1-collector/s07-modbus-client.md) | [s07-modbus-client.md](s07-modbus-client.md) |
| **s08** | [s08-modbus-connector.md](../../plan/decompose-v1-p1-collector/s08-modbus-connector.md) | [s08-modbus-connector.md](s08-modbus-connector.md) |
| **s09** | [s09-opcua-security.md](../../plan/decompose-v1-p1-collector/s09-opcua-security.md) | [s09-opcua-security.md](s09-opcua-security.md) |
| **s10** | [s10-opcua-connector.md](../../plan/decompose-v1-p1-collector/s10-opcua-connector.md) | [s10-opcua-connector.md](s10-opcua-connector.md) |
| **s11** | [s11-quality-engine.md](../../plan/decompose-v1-p1-collector/s11-quality-engine.md) | [s11-quality-engine.md](s11-quality-engine.md) |
| **s12** | [s12-unit-converter.md](../../plan/decompose-v1-p1-collector/s12-unit-converter.md) | [s12-unit-converter.md](s12-unit-converter.md) |
| **s13** | [s13-normalizer-worker.md](../../plan/decompose-v1-p1-collector/s13-normalizer-worker.md) | [s13-normalizer-worker.md](s13-normalizer-worker.md) |
| **s14** | [s14-health-snapshot.md](../../plan/decompose-v1-p1-collector/s14-health-snapshot.md) | [s14-health-snapshot.md](s14-health-snapshot.md) |
| **s15** | [s15-emulator-tag-model.md](../../plan/decompose-v1-p1-collector/s15-emulator-tag-model.md) | — |
| **s16** | [s16-emulator-modbus-server.md](../../plan/decompose-v1-p1-collector/s16-emulator-modbus-server.md) | — |
| **s17** | [s17-emulator-opcua-server.md](../../plan/decompose-v1-p1-collector/s17-emulator-opcua-server.md) | — |
| **s18** | [s18-emulator-dirt.md](../../plan/decompose-v1-p1-collector/s18-emulator-dirt.md) | — |
| **s19** | [s19-integration-modbus.md](../../plan/decompose-v1-p1-collector/s19-integration-modbus.md) | [s19-integration-modbus.md](s19-integration-modbus.md) |
| **s20** | [s20-integration-opcua.md](../../plan/decompose-v1-p1-collector/s20-integration-opcua.md) | [s20-integration-opcua.md](s20-integration-opcua.md) |
| **s21** | [s21-integration-dual-source.md](../../plan/decompose-v1-p1-collector/s21-integration-dual-source.md) | [s21-integration-dual-source.md](s21-integration-dual-source.md) |
| **s22** | [s22-integration-dirty-t3.md](../../plan/decompose-v1-p1-collector/s22-integration-dirty-t3.md) | — |
| **s23** | [s23-docker-compose.md](../../plan/decompose-v1-p1-collector/s23-docker-compose.md) | [s23-docker-compose.md](s23-docker-compose.md) |
| **s24** | [s24-stub-plugin-demo.md](../../plan/decompose-v1-p1-collector/s24-stub-plugin-demo.md) | [s24-stub-plugin-demo.md](s24-stub-plugin-demo.md) |
| **s25** | [s25-soak-t1-fragment.md](../../plan/decompose-v1-p1-collector/s25-soak-t1-fragment.md) | [s25-soak-t1-fragment.md](s25-soak-t1-fragment.md) |
| **s26** | runtime gaps R-1/R-2/R-3 | [s26-runtime-gaps-r1-r3.md](s26-runtime-gaps-r1-r3.md) |
