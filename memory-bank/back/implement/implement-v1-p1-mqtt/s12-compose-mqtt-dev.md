# T-008 | s12 | compose-mqtt-dev IMPLEMENT
**Plan ID:** v1-p1-mqtt
**Decompose step:** [s12-compose-mqtt-dev.md](../../plan/decompose-v1-p1-mqtt/s12-compose-mqtt-dev.md)
**Дата:** 2026-07-28
**Уровень:** L2
**Статус:** done

## Сделано
- В `docker-compose.yml` добавлен профиль `mqtt-dev` с Mosquitto 2.x (`1883`) и отдельным `collector-mqtt`.
- `collector-mqtt` использует `config/sources.mqtt-dev.yaml` с двумя subscribe-only источниками `panel_aps` и `panel_geu`, картами MQTT channels и health volume.
- Добавлены локальные Mosquitto config/ACL (`infra/mosquitto/mosquitto.conf`, `infra/mosquitto/aclfile`).
- Добавлен `.env.example` с `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, `MQTT_USER`, `MQTT_PASSWORD`.
- В `apps/edge/collector/README.md` документированы запуск, проверка и остановка профиля.

## Файлы
- `docker-compose.yml`
- `apps/edge/collector/config/sources.mqtt-dev.yaml`
- `infra/mosquitto/mosquitto.conf`
- `infra/mosquitto/aclfile`
- `.env.example`
- `apps/edge/collector/README.md`

## Верификация
- `docker compose --profile mqtt-dev config` → exit 0.
- `PYTHONPATH=apps/edge/collector/src .venv/bin/python` загрузил `sources.mqtt-dev.yaml`: 2 `MqttSourceConfig` (`panel_aps`, `panel_geu`).
- `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src .venv/bin/pytest -q --confcutdir=apps/edge/collector/tests/unit apps/edge/collector/tests/unit/test_mqtt_connector.py apps/edge/collector/tests/unit/test_health_mqtt.py` → **10 passed**.
