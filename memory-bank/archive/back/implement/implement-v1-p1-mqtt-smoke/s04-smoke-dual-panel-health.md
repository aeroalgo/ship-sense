# [T-008 | v1-p1-mqtt-smoke s04] IMPLEMENT

**Дата:** 2026-07-29
**Уровень:** L1
**Статус:** done

## Сделано

- Добавлен режим `dual` в MQTT smoke harness.
- Publisher запускается с `--panels aps,geu`.
- После 15 секунд прогрева скрипт читает `collector.json` из volume через `collector-mqtt` и проверяет `panel_aps` и `panel_geu`.
- Для обеих source entries проверяются `subscribed == true` и непустой `last_msg_ts`; проверка повторяется до 30 секунд.
- Неуспешный health snapshot приводит к dump compose logs через общий cleanup trap.

## Файлы

- `scripts/smoke-mqtt-stack.sh`

## Тесты

- cmd: `bash -n scripts/smoke-mqtt-stack.sh`
- итог: OK
- cmd: `docker compose --profile mqtt-dev config`
- итог: OK
- Полный compose smoke не запускался: предыдущий s03 зафиксировал существующий circular import в `collector`.

## Integration check

- [x] health snapshot path and volume are consumed through collector container
- [x] source IDs `panel_aps` and `panel_geu` are asserted
- [x] MQTT subscription and message timestamp are asserted
