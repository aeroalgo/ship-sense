# Шаг s07: Compose L2 smoke — SQL COUNT samples
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-PIPE-07, AC-PIPE-08
**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Скрипт `scripts/smoke-pipeline-db.sh`: поднять compose (default и/или mqtt-dev), poll `SELECT count(*) FROM samples` до >0 за TIMEOUT (default 60s), exit 0/1 fail-loud. Опциональный pytest wrapper. Минимальный compose harden если flaky (`collector-mqtt depends_on db`).

## Контекст
- **Consumes:** healthy compose stack после BUGFIX; `SHIPSSENSE_SMOKE_SOURCES=aps_main`; mqtt-dev profile services.
- **Produces:** bash smoke + optional pytest; возможно точечный `docker-compose.yml`.

## Файлы
- `scripts/smoke-pipeline-db.sh` (Создание)
- `tests/pipeline/test_compose_db_smoke.py` (Создание, optional — skip если compose недоступен)
- `docker-compose.yml` (Модификация — только если доказан flaky migrate race)

## Интерфейсы (lean — без кода)
- CLI: `MODE="${1:-default}"` — `default` | `mqtt`; `TIMEOUT` env.
- default: `docker compose up -d --build db writer emulator collector` → wait healthy → poll psql COUNT.
- mqtt: `docker compose --profile mqtt-dev up -d --build db writer mosquitto collector-mqtt emulator-mqtt` → expect tags `TAI4101` и/или `TGEU4101` (GROUP BY или WHERE).
- Fail: count=0 после timeout → stderr `FAIL: samples still 0 after …`; exit 1.
- Запрещено: exit 0 при пустой таблице; «skip success» если БД недоступна.

## TDD (нет)
- **Причина:** bash compose smoke / infra; не unit бизнес-логики.
- **Верификация:** parent запускает script; exit 0 при живых данных; negative path — timeout exit 1 (можно симулировать коротким TIMEOUT на пустой db).

## Подробный процесс выполнения
1. Написать script по plan §3.6 / §9.3 (`set -euo pipefail`).
2. Poll interval ~2s.
3. Optional pytest subprocess wrapper `@pytest.mark.slow` + skip без docker/compose.
4. Если flaky writer migrate: добавить `depends_on: db: condition: service_healthy` для collector-mqtt — минимальный diff.
5. Не переписывать mqtt-smoke scripts.

## Чекпоинт верификации
- AC-PIPE-07: default mode exit 0, samples>0.
- AC-PIPE-08: mqtt mode видит TAI4101 или TGEU4101.
- FR-6.

## Зависимости
- Compose writer/db healthy (BUGFIX); логически после L0 green.

## Frontend
N/A. Compose — **только parent**.

## Следующий шаг
→ s08 (docs + markers).
