# T-008 | s09 | MQTT integration E2E

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s09-integration-mqtt.md](../../plan/decompose-v1-p1-mqtt/s09-integration-mqtt.md)  
**Дата:** 2026-07-28  
**Уровень:** L2  
**Статус:** done

## Сделано

- Harness s09 (ранее): `test_mqtt_e2e.py`, Mosquitto testcontainer fixture, dual-source scenario.
- QA R-1 fix: `AsyncMqttClient._dispatch_message` нормализует `aiomqtt.Topic` → `str`; принимает `bytes|bytearray` payload.
- Unit regression: `test_aiomqtt_topic_object_is_normalized_to_str`.

## Файлы

- `apps/edge/collector/src/collector/plugins/mqtt/client.py`
- `apps/edge/collector/tests/unit/test_mqtt_client.py`
- `apps/edge/collector/tests/integration/test_mqtt_e2e.py` (без изменений в этом проходе)
- `apps/edge/collector/tests/conftest.py` (harness, ранее)

## TDD

- RED: `test_aiomqtt_topic_object_is_normalized_to_str` → `assert len(received) == 0` (Topic discarded).
- GREEN: normalize topic via `str()`; 5 unit + 2 E2E green.

## Тесты

```text
PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src \
  .venv/bin/pytest -q \
  apps/edge/collector/tests/unit/test_mqtt_client.py \
  apps/edge/collector/tests/unit/test_mqtt_connector.py \
  apps/edge/collector/tests/integration/test_mqtt_e2e.py
→ 12 passed
```

## Integration check

- [x] AC-MQTT-30: Mosquitto → collector → MockSink sample + lifecycle Event
- [x] Dual MQTT sources independent
- [x] R-1 Topic normalization
- [ ] Full suite / T-001 regression → BACK QA
