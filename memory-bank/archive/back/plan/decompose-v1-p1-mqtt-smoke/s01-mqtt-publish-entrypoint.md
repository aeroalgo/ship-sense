# Шаг s01: emulator `mqtt_publish` entrypoint + CLI
**Plan ID:** v1-p1-mqtt-smoke
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-MQTT-S01
**code_surface:** service
**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Модуль `emulator.mqtt_publish` — CLI entrypoint (`python -m emulator.mqtt_publish`), который парсит args, создаёт N `MqttPublisherAdapter` (по `--panels`), подключается к broker, гонит `publish_loop`, корректно останавливается по SIGTERM/SIGINT. Reuse существующего `MqttPublisherAdapter` — **без** новой payload-логики.

## Контекст
- **Consumes:** `emulator.protocols.mqtt_publisher.MqttPublisherAdapter` (panels `aps`/`geu`, `connect(broker_url)`, `publish_loop(iterations=)`, `stop()`); контракт CR-COL-05 (closed).
- **Produces:** reentrant module `emulator.mqtt_publish`; targeted pytest.

## Файлы
- `apps/edge/emulator/src/emulator/mqtt_publish.py` (Создание)
- `apps/edge/emulator/tests/test_mqtt_publish_entrypoint.py` (Создание)

## Интерфейсы (lean — без кода)
- `async def amain(argv: list[str] | None = None) -> int` — парсит `--broker` (default `mqtt://localhost:1883`), `--panels` (csv, default `aps,geu`, validate ⊆ {aps,geu}), `--interval` (float>0, default 1.0), `--seed` (int, default 42), `--iterations` (int|None, default None = until signal); создаёт adapter per panel; `asyncio.gather` их `publish_loop`; обработка `SIGTERM`/`SIGINT` → вызвать `stop()` на всех → exit 0.
- `def main() -> None` — thin sync wrapper: `sys.exit(asyncio.run(amain()))`.
- Если `--panels` содержит неизвестный panel → `ValueError`/argparse error → exit 2.
- При `aiomqtt` ImportError → печатать понятное сообщение, exit 1 (не стек).

## TDD (красная → зелёная)
1. **Тест (targeted pytest):**
   - `test_parse_args_defaults` — дефолты broker/panels/interval/seed/iterations.
   - `test_parse_args_rejects_unknown_panel` — `--panels foo` → exit 2 / argparse error.
   - `test_amain_publishes_at_least_one_message` — инжектить `client_factory` mock-broker (reuse `MqttPublisherAdapter(client_factory=)`); запустить `amain(["--broker", "mqtt://x:1", "--panels", "aps", "--iterations", "1"])` → assert mock получил ≥1 publish с topic `shipsense/v1/aps/*` и payload с `"@type"`.
   - `test_amain_stops_on_sigterm` — симулировать stop (через `--iterations 1` или cancel task) → `amain` возвращает 0, без висящих тасков.
   - Запуск: тесты падают (модуля нет).
2. **Реализация:** `mqtt_publish.py` по интерфейсам выше; reuse adapter без дублирования payload-кода.
3. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. `argparse.ArgumentParser(prog="python -m emulator.mqtt_publish")` — флаги выше; `--panels` split по `,` + strip.
2. Один `MqttPublisherAdapter(panel=p, seed=seed, interval=interval)` на panel; все `await adapter.connect(broker)`.
3. `signal` handler устанавливает общий `asyncio.Event`; `publish_loop` адаптера уже слушает `stop()`. SIGTERM/SIGINT → `for a in adapters: await a.stop()`.
4. `asyncio.gather(*loops, return_exceptions=True)`; исключение из одного adapter не валит остальные.
5. Если `client_factory` не передан → adapter использует `_make_client` (aiomqtt) — production path; тесты инжектят mock.
6. Никакого `if __name__` inline-кода вне `main()`.

## Anti-patterns checklist
- Нет bare `except:` / `except Exception: pass` (python-anti-patterns).
- Исключения из gather логируются, не проглатываются молча.
- `main()` — единственный sync entrypoint; `amain` тестируемая поверхность.

## Чекпоинт верификации
- AC-MQTT-S01: `python -m emulator.mqtt_publish --broker <url> --panels aps` публикует ≥1 сообщение (pytest mock-broker green).
- `cd apps/edge/emulator && pytest tests/test_mqtt_publish_entrypoint.py` — зелёный.
- `cd apps/edge/emulator && python -m emulator.mqtt_publish --help` — exit 0, показывает флаги.

## Зависимости
- Upstream: родитель s08 (`MqttPublisherAdapter`) — hard, уже реализован.

## Frontend
N/A. HARD RULE `front-tests-parent-only.mdc` — не применимо.

## Следующий шаг
→ s02 (compose-сервис `emulator-mqtt` + acl publish).
