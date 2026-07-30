# [v1-p1-mqtt-smoke | s01 | mqtt-publish-entrypoint] IMPLEMENT

**Plan ID:** v1-p1-mqtt-smoke
**Decompose step:** [s01-mqtt-publish-entrypoint.md](../../plan/decompose-v1-p1-mqtt-smoke/s01-mqtt-publish-entrypoint.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-29
**Уровень:** L2 (один service-модуль + targeted pytest)
**Статус:** done

> **Skills A∪B:** tdd, python-testing-patterns, modern-python, python-anti-patterns — Read до кода.

## Сделано

- Создан `emulator.mqtt_publish` — CLI entrypoint (`python -m emulator.mqtt_publish`).
- `argparse` парсер (`build_parser`): `--broker` (mqtt://localhost:1883), `--panels` (csv, default aps,geu, validate ⊆ {aps,geu} → exit 2), `--interval` (>0, default 1.0), `--seed` (default 42), `--iterations` (int|None, None = until signal).
- `async amain(argv=None) -> int` — создаёт один `MqttPublisherAdapter` per panel (через `_make_adapter` indirection для testability), `connect(broker)`, `asyncio.gather(publish_loop, return_exceptions=True)`, `finally: stop()` на всех; SIGTERM/SIGINT → `loop.add_signal_handler` → `adapter.stop()`; exit 0 по завершению, exit 1 при broker/исключении.
- `main()` — thin sync wrapper: guard на `aiomqtt` ImportError (понятное сообщение, exit 1) + `sys.exit(asyncio.run(amain()))`.
- Reuse `MqttPublisherAdapter` — **без** дублирования payload-логики.
- TDD: red (10 тестов, ModuleNotFoundError) → green.

## Файлы

- `apps/edge/emulator/src/emulator/mqtt_publish.py` (create, 170 строк)
- `apps/edge/emulator/tests/test_mqtt_publish_entrypoint.py` (create, 192 строки)

## Тесты

- cmd: `cd apps/edge/emulator && PYTHONPATH=src pytest tests/test_mqtt_publish_entrypoint.py -q`
- итог: 10 passed
- полный emulator suite: `cd apps/edge/emulator && PYTHONPATH=src pytest tests/ -q` → 31 passed
- AC checkpoint: `PYTHONPATH=src python -m emulator.mqtt_publish --help` → exit 0, показывает флаги

## Integration check

- [x] service module reentrant (`amain` тестируемая поверхность; `main` — единственный sync entrypoint)
- [x] нет bare `except` / `except Exception: pass` (gather исключения логируются; CLI boundary `except Exception` логирует + exit 1)
- [x] сигналы обрабатываются через `loop.add_signal_handler` (graceful drain)
- [x] `_make_adapter` — single point для тест-инъекции mock-broker
- N/A storage keys / env vars / DB cols / events (service CLI, no persistence)

## AC-MQTT-S01

`python -m emulator.mqtt_publish --broker <url> --panels aps` публикует ≥1 сообщение — подтверждено pytest mock-broker (`test_amain_publishes_at_least_one_message`: ≥1 publish с topic `shipsense/v1/aps/*` и payload с `@type`).
