# Шаг s04: smoke dual-panel + health snapshot 2 sources
**Plan ID:** v1-p1-mqtt-smoke
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-MQTT-S04
**code_surface:** test
**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Расширить `smoke-mqtt-stack.sh` режимом `dual`: поднять `emulator-mqtt` с `--panels aps,geu`, через 15 s прочитать health snapshot `collector.json` (volume `collector-mqtt-health`) и проверить 2 source entries (`panel_aps`, `panel_geu`), оба `subscribed: true`, `last_msg_ts` ≠ null.

## Контекст
- **Consumes:** s03 smoke harness; s11 родителя (`HealthAggregator` per-source MQTT fields: `subscribed`, `last_msg_ts`, `parse_errors`); snapshot path `/var/lib/shipsense/health/collector.json`.
- **Produces:** режим `dual` в скрипте.

## Файлы
- `scripts/smoke-mqtt-stack.sh` (Модификация — +`dual` mode + health assertion)

## Compose execution — parent only (HARD)
Как в s03: compose запускает только parent.

## Интерфейсы (lean — без кода)
- `dual`:
  1. `up_stack` (как single, но publisher `--panels aps,geu`).
  2. Sleep 15 s (дать подписке + сообщениям).
  3. `docker compose ... cp` или `run --rm` с `cat /var/lib/shipsense/health/collector.json` → парсить `jq`/python.
  4. Assert: ровно/минимум 2 entries; `panel_aps` и `panel_geu` присутствуют; для каждого `.subscribed == true` и `.last_msg_ts != null`.
  5. PASS/FAIL + cleanup.

## TDD (нет)
- **Причина:** compose-смоук + health assertion; новой бизнес-логики нет (health writer — s11 родителя).
- **Верификация (parent):** `scripts/smoke-mqtt-stack.sh dual` → exit 0; snapshot содержит 2 live sources.

## Подробный процесс выполнения
1. Health snapshot в volume `collector-mqtt-health` — читать через ephemeral контейнер (`docker run --rm -v collector-mqtt-health:/d alpine cat /d/collector.json`) или `docker compose cp`.
2. `jq` если есть в runtime; иначе `python3 -c` парсинг (python есть в collector image).
3. timeout для health-read 30 s после 15 s warmup.

## Чекпоинт верификации
- AC-MQTT-S04: health snapshot JSON after 15 s содержит 2 source entries, `subscribed: true`, `last_msg_ts` ≠ null.

## Зависимости
- Upstream: s03 — hard; s11 родителя (health) — hard (done).

## Frontend
N/A.

## Следующий шаг
→ s05 (lifecycle event gate: total_events > 0).
