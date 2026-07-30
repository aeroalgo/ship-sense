# Шаг s05: L1 MQTT lifecycle → events в БД
**Plan ID:** v1-p1-pipeline-db-e2e
**Status:** done
**AC:** AC-PIPE-04
**code_changed:** yes
**graphify:** требуется из корня реpo: `.venv/bin/graphify update .` (после FINISH)

## Кратко
TDD red→green: `test_mqtt_lifecycle_persists_event_to_db` (AC-PIPE-04).  
Lifecycle transition (normal → exceeded_unacked) → `MqttConnector` (on_event) → `IpcCanonicalSink` → `WriterService.start_tcp` + `writer_loop` → `events` с `event_name='aps.threshold.exceeded'`, COUNT≥1.  
Reuse s04 wiring (fixtures, channel_map, normalizer, supervisor). Poll bounded loop + AssertionError на timeout. Не мокать EventsRepo.  
AC-PIPE-03 (samples) регрессия зелёная.

## Артефакт
- `tests/pipeline/test_mqtt_pipeline_db.py` (добавлен тест `test_mqtt_lifecycle_persists_event_to_db`)
- `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s05-l1-mqtt-lifecycle-events.md` (этот файл)

## Верификация
```bash
.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py -q
# → оба теста PASSED (AC-PIPE-03 + AC-PIPE-04)
```
- AC-PIPE-04 green: `event_name='aps.threshold.exceeded'` COUNT≥1
- AC-PIPE-03 регрессия зелёная (TAI4101 samples)
- compose/runtime entrypoint и публичный API writer не затронуты
- Нет AsyncMock на insert_batch

## Детали реализации
1. **RED:** Создали `test_mqtt_lifecycle_persists_event_to_db` — pytest collection error (тест не существовал).
2. **GREEN:** Скопировали wiring из `test_mqtt_emulator_persists_analog_to_db` (s04):
   - `MqttConnector(..., on_event=sink.write_event)` — передаём callback для lifecycle events
   - `Normalizer` (без event_detector — lifecycle события идут через mapper/tracker)
   - `RawConsumer` + `SourceSupervisor`
   - `IpcCanonicalSink` → `WriterService.start_tcp` (ephemeral port)
3. **Lifecycle trigger:** publish normal → sleep → publish `aps_state=exceeded_unacked` (новый source_ts) → `MqttLifecycleTracker` создаёт `Event(event_name="aps.threshold.exceeded")` → `on_event` → IPC → `WriterService` → `EventsRepo.insert_batch` → БД.
4. **Assert:** poll `SELECT COUNT(*) FROM events WHERE event_name='aps.threshold.exceeded'` ≥ 1.
5. **Regression:** s04 тест остаётся без изменений — обе функции в одном файле.

## Scope
- Только тест (code_surface=test по shard).
- Не трогаем `writer.py`, `run_tcp`, `__main__`, compose, runtime entrypoint.
- Не добавляем новых ENV/конфигов/маршрутов.

## Следующий шаг
→ s06 (Modbus Contour B) — см. `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md`

## Handoff
- **Предыдущий:** [s04-l1-mqtt-pipeline-samples.md](memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s04-l1-mqtt-pipeline-samples.md) — done
- **Следующий:** [s06-l1-modbus-pipeline-samples.md](memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e/s06-l1-modbus-pipeline-samples.md)
- **Кратко:** AC-PIPE-04 зелёный. L1 MQTT lifecycle (exceeded) → `events` с `event_name='aps.threshold.exceeded'`, COUNT≥1. TDD red→green. `MqttConnector(on_event=sink.write_event)` + `IpcCanonicalSink` + `WriterService` → DB. Poll bounded. s04 регрессия зелёная. code_changed=yes.
- **Артефакт:** `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/s05-l1-mqtt-lifecycle-events.md`
- **Верификация:** `.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py -q` → оба теста PASSED. AC-PIPE-04 green; compose/runtime entrypoint и публичный API writer не затронуты.
- **code_changed:** yes
- **graphify:** требуется из корня репо: `.venv/bin/graphify update .` (после FINISH)
- **New chat:** yes (context economy, epic mode — один шаг за сессию)
