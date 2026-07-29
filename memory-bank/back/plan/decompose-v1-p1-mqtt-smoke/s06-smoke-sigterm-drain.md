# Шаг s06: smoke SIGTERM drain + ExitCode 0
**Plan ID:** v1-p1-mqtt-smoke
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-MQTT-S05
**code_surface:** test
**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Расширить `smoke-mqtt-stack.sh` режимом `sigterm`: `docker compose --profile mqtt-dev stop collector-mqtt` → ExitCode 0 (AC-HLT-05 regression для MQTT sources). Доказать graceful drain по SIGTERM.

## Контекст
- **Consumes:** s03 harness; supervisor/runtime (T-001) SIGTERM handling; `collector-mqtt` `stop_grace_period: 10s` (s12 родителя).
- **Produces:** режим `sigterm`.

## Файлы
- `scripts/smoke-mqtt-stack.sh` (Модификация — +`sigterm` mode)

## Compose execution — parent only (HARD)
Как в s03–s05.

## Интерфейсы (lean — без кода)
- `sigterm`:
  1. `up_stack` (publisher + collector running, brief warmup чтобы подписка активна).
  2. `docker compose --profile mqtt-dev stop collector-mqtt` — это шлёт SIGTERM, ждёт `stop_grace_period`, затем SIGKILL если не вышел.
  3. `docker compose --profile mqtt-dev ps -a --format json collector-mqtt` → парсить `Status`/`ExitCode`; assert exit 0.
  4. PASS если ExitCode 0; FAIL иначе (+ dump `docker inspect` State).
  5. cleanup.

## TDD (нет)
- **Причина:** compose lifecycle проверка; drain-логика в runtime (T-001), покрыта там.
- **Верификация (parent):** `scripts/smoke-mqtt-stack.sh sigterm` → exit 0; collector-mqtt ExitCode 0.

## Подробный процесс выполнения
1. `docker compose stop` = SIGTERM → grace → kill. ExitCode берём из `docker inspect --format '{{.State.ExitCode}}'` или `ps -a`.
2. Если ExitCode 137 (SIGKILL после grace) → FAIL (drain не уложился) → сообщить, увеличить grace / чинить runtime (не fallback).
3. Документировать expected в s07.

## Чекпоинт верификации
- AC-MQTT-S05: `docker compose --profile mqtt-dev stop collector-mqtt` → ExitCode 0.

## Зависимости
- Upstream: s03 — hard; T-001 runtime SIGTERM — hard (done).

## Frontend
N/A.

## Следующий шаг
→ s07 (README §MQTT smoke commands).
