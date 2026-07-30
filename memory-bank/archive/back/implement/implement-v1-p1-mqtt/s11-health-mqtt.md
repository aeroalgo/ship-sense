# T-008 | s11 | health-mqtt IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s11-health-mqtt.md](../../plan/decompose-v1-p1-mqtt/s11-health-mqtt.md)  
**Implement index:** [index.md](index.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- `HealthStatus` расширен optional MQTT-полями: `protocol`, `connected`, `subscribed`, `last_msg_ts`, `parse_errors`, `broker_reachable` (s14 keys сохранены).
- `MqttConnector.healthcheck()` заполняет AC-MQTT-40 поля; `subscribed=false` при отсутствии подписки / потере session; `broker_reachable` = client session.
- `HealthAggregator.update_source` валидирует mqtt payload (`protocol=mqtt` → required fields) и прокидывает в snapshot.
- Unit `test_health_mqtt.py`: mock connector → snapshot JSON + parse_errors increment + reconnect subscribed=false.

## Файлы

- `apps/edge/collector/src/collector/domain/models.py`
- `apps/edge/collector/src/collector/plugins/mqtt/connector.py`
- `apps/edge/collector/src/collector/health/aggregator.py`
- `apps/edge/collector/tests/unit/test_health_mqtt.py`

## TDD

- RED: 5 failed — `HealthStatus` без `protocol` / mqtt fields.
- GREEN: 5 mqtt + 8 existing health snapshot = 13; + mqtt connector = 18 passed.

## Тесты

- cmd: `PYTHONPATH=apps/edge/collector/src .venv/bin/pytest -q --confcutdir=apps/edge/collector/tests/unit apps/edge/collector/tests/unit/test_health_mqtt.py apps/edge/collector/tests/unit/test_health_snapshot.py apps/edge/collector/tests/unit/test_mqtt_connector.py`
- итог: **18 passed**

## Integration check

- [x] `MqttConnector.healthcheck` → `HealthStatus` с `protocol=mqtt` + subscribed/last_msg_ts/parse_errors/connected/broker_reachable
- [x] `HealthAggregator.update_source` → snapshot сохраняет mqtt fields
- [x] `SnapshotWriter` JSON: mqtt keys + s14 keys (`collector_state`, `samples_total`)
- [x] existing `test_health_snapshot.py` still pass (modbus-style status без mqtt fields)
- [x] `last_msg_ts` ISO8601 via `model_dump(mode="json")`
