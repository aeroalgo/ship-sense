# [v1-p1-mqtt-smoke s06] IMPLEMENT

**Дата:** 2026-07-29
**Уровень:** L1
**Статус:** done
**AC:** AC-MQTT-S05
**Plan:** `memory-bank/back/plan/decompose-v1-p1-mqtt-smoke/s06-smoke-sigterm-drain.md`

## Сделано

- Добавлен режим `sigterm` в MQTT smoke harness (`scripts/smoke-mqtt-stack.sh`).
- Валидация MODE расширена: `single` | `dual` | `events` | `sigterm`.
- Режим `sigterm`:
  1. Stack up (publisher + collector running), 10 s warmup.
  2. Poll health snapshot `panel_aps.subscribed is True` (до 30 s) — гарантирует активную подписку перед SIGTERM.
  3. `docker compose --profile mqtt-dev stop collector-mqtt` — отправляет SIGTERM, ждёт `stop_grace_period: 10s`, затем SIGKILL при превышении.
  4. `docker inspect -f '{{.State.ExitCode}}' shipsense-collector-mqtt` → assert exit 0.
  5. PASS если ExitCode 0; FAIL иначе (+ dump `docker inspect .State` в stderr).
- ExitCode взят из `docker inspect` (source of truth), не из `compose ps --format json` (нестабильное поле ExitCode).

## Файлы

- `scripts/smoke-mqtt-stack.sh` — режим `sigterm` + валидация MODE.

## Тесты (parent only)

- cmd: `bash -n scripts/smoke-mqtt-stack.sh`
- итог: OK
- cmd: `scripts/smoke-mqtt-stack.sh sigterm`
- итог: `PASS: SIGTERM drain — collector-mqtt ExitCode 0 (AC-HLT-05)` — exit 0

## Integration check

- [x] `collector-mqtt` `stop_grace_period: 10s` (docker-compose.yml:165) — drain window
- [x] ExitCode 0 подтверждает graceful drain runtime (T-001 SIGTERM handler) в пределах grace
- [x] cleanup trap покрывает sigterm-ветку (compose down + dump logs on fail)

## Чекпоинт верификации

- AC-MQTT-S05: `docker compose --profile mqtt-dev stop collector-mqtt` → ExitCode 0 — **PASS**

## TDD

- **Причина пропуска:** compose lifecycle проверка (`code_surface: test`, `tdd: no`); drain-логика в runtime (T-001) покрыта unit-тестами родителя.

## Следующий шаг

→ s07 (README §MQTT smoke commands).
