# BACK IMPLEMENT v1-p1-mqtt-smoke s03

Статус: done (2026-07-29)

## Изменение

Создан `scripts/smoke-mqtt-stack.sh`.

- Режим по умолчанию и единственный реализованный режим: `single`.
- Поднимает `mosquitto`, `writer`, `collector-mqtt` с профилем `mqtt-dev`.
- Запускает `emulator.mqtt_publish` только для панели `aps`.
- Ожидает в логах writer `total_samples=[1-9]` до 30 секунд.
- При успехе печатает `PASS` и завершает compose-стек; при ошибке печатает логи и возвращает ненулевой код.

## Проверка

- `bash -n scripts/smoke-mqtt-stack.sh` — OK.
- `docker compose --profile mqtt-dev config` — OK.
- Полный smoke запуск заблокирован существующей ошибкой импорта в `collector` (`BaseSourceConnector` из partially initialized module), не вызванной этим изменением.
