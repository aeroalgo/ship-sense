# Шаг s23: Docker Compose: emulator + collector + writer + deps
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-I3-16, AC-INT-03, AC-HLT-05

**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Docker Compose: emulator + collector + writer + deps — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s14 app, s16–s18 emulator, s05b ipc
- **Produces:** Dockerfiles, compose services, README ports

## Файлы
- `apps/edge/collector/Dockerfile` (Создание)
- `apps/edge/emulator/Dockerfile` (Создание)
- `docker-compose.yml` (Создание/Модификация) — emulator, collector, writer(stub), db, api, web stubs as needed
- `apps/edge/collector/README.md` (Модификация)
- `apps/edge/emulator/README.md` (Создание)

## Интерфейсы (lean — без кода)
- n/a — infra

## TDD (нет)
- **Причина:** scaffold / infra / compose без новой бизнес-логики.
- **Верификация:** smoke: compose up + curl/log check (не pytest business)

## Подробный процесс выполнения
1. Сервисы emulator+collector healthy; порты Modbus/OPC UA в README.
2. SIGTERM collector → exit 0.
3. Logs показывают samples/sec (stub writer ok).

## Чекпоинт верификации
- `docker compose up emulator collector` поднимается
- healthchecks ok
- порты задокументированы
