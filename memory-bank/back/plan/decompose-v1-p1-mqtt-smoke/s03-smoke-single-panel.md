# Шаг s03: smoke single-panel (aps → writer samples/sec > 0)
**Plan ID:** v1-p1-mqtt-smoke
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-MQTT-S03
**code_surface:** test
**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Создать `scripts/smoke-mqtt-stack.sh` — compose-driven smoke harness. Первый режим: single-panel — поднять стек `mosquitto` + `writer` + `collector-mqtt` + `emulator-mqtt` (panels=aps), дождаться writer log `total_samples=[1-9]` в окне 30 s → exit 0; иначе exit 1.

## Контекст
- **Consumes:** s01 entrypoint, s02 compose-сервис; `writer` stub (T-001) логирует `total_samples`/`samples/sec`.
- **Produces:** reusable smoke-скрипт (расширяется в s04–s06).

## Файлы
- `scripts/smoke-mqtt-stack.sh` (Создание)

## Compose execution — parent only (HARD)
Скрипт запускает `docker compose` — выполняет **только parent**. Subagent не спавнится для запуска compose; subagent (если нужен) только пишет сам скрипт. `front-tests-parent-only.mdc` — N/A (нет frontend), но compose-exec gate тот же.

## Интерфейсы (lean — без кода)
- `smoke-mqtt-stack.sh [mode]` где `mode ∈ {single|dual|events|sigterm|all}` (default: single). s03 реализует `single`; s04–s06 добавляют остальные.
- `single`:
  1. `docker compose --profile mqtt-dev up -d --build mosquitto writer collector-mqtt`
  2. `EMULATOR_PANELS=aps docker compose --profile mqtt-dev run --rm emulator-mqtt python -m emulator.mqtt_publish --broker mqtt://mosquitto:1883 --panels aps` (или up сервиса с override) — выбрать устойчивый вариант в IMPLEMENT.
  3. Poll `docker compose --profile mqtt-dev logs writer` до строки `total_samples=[1-9]` (regex) с timeout 30 s.
  4. Match → echo PASS, exit 0; timeout → echo FAIL + dump logs, exit 1.
  5. Cleanup: `docker compose --profile mqtt-dev down` (trap EXIT).
- Скрипт `set -euo pipefail`; функции `up_stack`, `poll_log`, `teardown`.

## TDD (нет)
- **Причина:** compose-смоук без новой бизнес-логики; entrypoint покрыт в s01, плагин — в родителе s09.
- **Верификация (parent):** запуск `scripts/smoke-mqtt-stack.sh single` → exit 0; writer log содержит `total_samples=[1-9]`.

## Подробный процесс выполнения
1. Селектор панели в `emulator-mqtt`: либо `--panels aps` через override command, либо `run --rm` с явной командой — выбрать проще поддерживаемое.
2. `poll_log`: `timeout 30 bash -c 'docker compose ... logs -f writer | grep -m1 "total_samples=[1-9]"'`.
3. trap cleanup всегда — не оставлять стек висеть.
4. Вывод: понятный PASS/FAIL + used commands (для README s07).

## Чекпоинт верификации
- AC-MQTT-S03: `docker compose --profile mqtt-dev up` → writer log `total_samples=[1-9]` within 30 s.

## Зависимости
- Upstream: s01, s02 — hard.

## Frontend
N/A.

## Следующий шаг
→ s04 (dual-panel + health snapshot 2 sources).
