# [T-008 | v1-p1-mqtt-smoke s05] IMPLEMENT

**Дата:** 2026-07-29
**Уровень:** L1
**Статус:** done
**AC:** AC-MQTT-S06
**Plan:** `memory-bank/back/plan/decompose-v1-p1-mqtt-smoke/s05-smoke-lifecycle-events.md`

## Сделано

- Добавлен режим `events` в MQTT smoke harness (`scripts/smoke-mqtt-stack.sh`).
- Publisher запускается с `--panels aps,geu --interval 1.0` (deterministic seed → lifecycle transitions).
- После 15 s прогрева скрипт poll writer log до строки `total_events=[1-9][0-9]*` с timeout 60 s (≥13 ticks чтобы пройти цикл `_EVENT_STATES` transitions).
- Валидация MODE и PANELS расширена (`single` | `dual` | `events`).
- PASS/FAIL + cleanup через существующий trap (dump compose logs on fail).
- Loose sanity grep per-Event строк (пункт 3 плана) не реализован: collector/writer не эмитят per-transition Event-строки; точный dedup (AC-MQTT-12) покрыт unit-тестами s04 родителя.

## Файлы

- `scripts/smoke-mqtt-stack.sh`

## Writer log format (подтверждено в коде)

`writer_stub/__main__.py:48`: `samples/sec=%.1f total_samples=%d total_events=%d` — cumulative summary каждые 5 s. Regex `total_events=[1-9][0-9]*` толерантен к ведущим цифрам.

## Тесты (parent only)

- cmd: `bash -n scripts/smoke-mqtt-stack.sh`
- итог: OK
- cmd: `docker compose --profile mqtt-dev config`
- итог: exit 0
- Полный compose smoke `events` не запускался: существующий circular import в `collector` (блокер из activeContext s03/s04) блокирует запуск services.

## Integration check

- [x] writer log regex соответствует формату `total_events=%d` (подтверждено в `writer_stub/__main__.py:48`)
- [x] publisher event states deterministic (seed 42, `_EVENT_STATES` цикл из 3 состояний, `mqtt_publisher.py:54`)
- [x] timeout 60 s покрывает ≥13 ticks (interval 1.0) для гарантированного event transition
- [x] cleanup trap покрывает events-ветку (дамп logs + `compose down`)

## TDD

- **Причина пропуска:** compose-smoke (`code_surface: test`); dedup-логика покрыта unit-тестами s04 родителя.
