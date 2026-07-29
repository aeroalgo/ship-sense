# T-008 | s02 | mqtt-client-wrapper IMPLEMENT

**Plan ID:** v1-p1-mqtt  
**Decompose step:** [s02-mqtt-client-wrapper.md](../../plan/decompose-v1-p1-mqtt/s02-mqtt-client-wrapper.md)  
**Дата:** 2026-07-27  
**Уровень:** L2  
**Статус:** done

## Сделано

- Добавлен `AsyncMqttClient` — subscribe-only async wrapper над `aiomqtt`.
- Реализованы idempotent `connect()` и `disconnect()`, `is_connected()` и `subscribe()`.
- Подписка из `MqttSourceConfig.subscribe` выполняется при connect и сохраняется для replay после reconnect.
- Receive loop передаёт connector только raw `topic`, `bytes` payload и timezone-aware UTC `recv_ts`; semantic/JSON parse отсутствует.
- Разрыв stream/ошибка транспорта восстанавливается через общий `RestartPolicy` и `compute_backoff`.
- Некорректные transport messages игнорируются без остановки consumer task; ошибки callback логируются и не роняют receive loop.
- Добавлена typed error surface: `MqttConnectionError`, `MqttSubscribeError`.
- Добавлена зависимость `aiomqtt>=2.3`.

## Файлы

- `apps/edge/collector/src/collector/plugins/mqtt/client.py`
- `apps/edge/collector/src/collector/plugins/mqtt/__init__.py`
- `apps/edge/collector/pyproject.toml`
- `apps/edge/collector/tests/unit/test_mqtt_client.py`

## Тесты

- cmd: `PYTHONPATH=apps/edge/collector/src .venv/bin/python -m compileall -q apps/edge/collector/src/collector/plugins/mqtt apps/edge/collector/tests/unit/test_mqtt_client.py`
- cmd: `PYTHONPATH=apps/edge/collector/src .venv/bin/pytest -q --confcutdir=apps/edge/collector/tests/unit apps/edge/collector/tests/unit/test_mqtt_config.py apps/edge/collector/tests/unit/test_mqtt_client.py`
- итог: `7 passed`
- Примечание: `aiomqtt` не установлен в текущем окружении, поэтому тесты используют async test double; dependency зафиксирована в collector `pyproject.toml`.

## Integration check

- [x] MQTT topic filter из config подписывается автоматически
- [x] reconnect использует shared `compute_backoff` / `RestartPolicy`
- [x] raw topic/payload/recv timestamp передаются callback
- [x] publish API отсутствует
- [x] `aiomqtt` dependency добавлена
- [ ] connector/registry — следующий s06
