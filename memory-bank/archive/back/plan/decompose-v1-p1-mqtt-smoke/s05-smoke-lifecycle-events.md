# Шаг s05: smoke lifecycle event gate (total_events > 0)
**Plan ID:** v1-p1-mqtt-smoke
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-MQTT-S06
**code_surface:** test
**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Расширить `smoke-mqtt-stack.sh` режимом `events`: доказать, что deterministic publisher гонит lifecycle transitions → writer логирует `total_events > 0` за окно 60 s (AC-MQTT-12 regression: ровно один Event на transition, dedup).

## Контекст
- **Consumes:** s03 harness; `MqttPublisherAdapter.build_messages(tick)` — цикл `_ANALOG_STATES`(5)/`_DISCRETE_STATES`(5)/`_EVENT_STATES`(3); s04 родителя semantic mapper (Event dedup, AC-MQTT-12).
- **Produces:** режим `events`.

## Файлы
- `scripts/smoke-mqtt-stack.sh` (Модификация — +`events` mode)

## Compose execution — parent only (HARD)
Как в s03/s04.

## Интерфейсы (lean — без кода)
- `events`:
  1. `up_stack` publisher `--panels aps,geu --interval 1.0`.
  2. Poll writer log до строки `total_events=[1-9]` (regex, > 0) с timeout 60 s (≥ 13 ticks чтобы пройти цикл transitions).
  3. Дополнительно: assert нет дубль-Event на одну transition (regex grep количества Event-строк в окне — loose sanity, точный dedup уже покрыт unit-тестом s04 родителя).
  4. PASS/FAIL + cleanup.

## TDD (нет)
- **Причина:** compose-смоук; dedup-логика покрыта unit-тестами родителя (s04/s05).
- **Верификация (parent):** `scripts/smoke-mqtt-stack.sh events` → exit 0; writer log `total_events > 0`.

## Подробный процесс выполнения
1. Publisher deterministic seed → transitions повторяются; за ~13 s (interval 1.0) гарантированно есть ≥1 event transition.
2. `total_events` grep; regex tolerate leading digits.
3. timeout 60 s даёт запас на collector parse + writer framing.

## Чекпоинт верификации
- AC-MQTT-S06: writer log `total_events > 0` за окно 60 s.

## Зависимости
- Upstream: s03 — hard; родитель s04/s05 (semantic mapper + Event dedup) — hard (done).

## Frontend
N/A.

## Следующий шаг
→ s06 (SIGTERM drain + ExitCode 0).
