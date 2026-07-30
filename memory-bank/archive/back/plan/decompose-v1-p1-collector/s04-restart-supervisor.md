# Шаг s04: SourceSupervisor + RestartPolicy + graceful stop
**Plan ID:** v1-p1-collector
**Next Phase:** BACK CREATIVE
**needs_creative:** yes | **tdd:** yes
**AC:** AC-B1-04, AC-B1-05, AC-B1-06, AC-B1-12, AC-HLT-04

- **CREATIVE:** CR-COL-01 → creative-collector-isolation.md

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
SourceSupervisor + RestartPolicy + graceful stop — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s03 SourceConnector; creative CR-COL-01 (Task vs process isolation)
- **Produces:** SourceSupervisor, RestartPolicy, backoff util; per-source Task lifecycle

## Файлы
- `apps/edge/collector/src/collector/core/restart_policy.py` (Создание)
- `apps/edge/collector/src/collector/core/supervisor.py` (Создание)
- `apps/edge/collector/src/collector/util/backoff.py` (Создание)
- `apps/edge/collector/tests/unit/test_supervisor.py` (Создание)

## Интерфейсы (lean — без кода)
- model: `RestartPolicy` — initial_backoff_sec, max_backoff_sec, max_attempts?, jitter?
- class: `SourceSupervisor` — start/stop; _run connect→subscribe→reconnect loop; put RawSample → raw_queue
- fn: `compute_backoff(attempt, policy) → float`

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_supervisor.py` — dual fake isolation, restart, cancel
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. До IMPLEMENT: закрыть CR-COL-01 (default: supervised asyncio.Task per source).
2. Supervisor: один Task на source; exception → backoff reconnect; cancel → disconnect.
3. Изоляция: падение fake source A не останавливает task B (unit с двумя fake connectors).
4. Метрики reconnect_count / last_ok_ts через connector healthcheck.

## Чекпоинт верификации
- Два fake source: kill A → B продолжает put в queue
- stop() отменяет task и disconnect
- backoff растёт до max
