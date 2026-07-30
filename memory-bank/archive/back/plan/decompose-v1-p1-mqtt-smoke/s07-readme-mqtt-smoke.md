# Шаг s07: README §MQTT smoke commands + expected log snippets
**Plan ID:** v1-p1-mqtt-smoke
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-MQTT-S08
**code_surface:** infra
**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Дополнить `apps/edge/collector/README.md` §«Локальный MQTT-dev профиль»: реальные команды smoke (`up`/`logs`/`ps`/`stop` через `emulator-mqtt`), expected writer log snippets (`total_samples`, `samples/sec`, `total_events`), known limits (dev-only ACL readwrite, без TLS/auth, без PSQL writer).

## Контекст
- **Consumes:** s02 compose-сервис `emulator-mqtt`; s03–s06 smoke harness (commands + expected outputs).
- **Produces:** обновлённый README раздел.

## Файлы
- `apps/edge/collector/README.md` (Модификация — расширить §MQTT)

## Текущее состояние (verified 2026-07-29)
README уже содержит §«Локальный MQTT-dev профиль» (s12 родителя): описывает mosquitto + collector subscribe-only, но **без** publisher-сервиса, без expected log snippets, без smoke-команд. Шаг расширяет существующий раздел.

## Интерфейсы (lean — без кода)
- n/a — docs only.

## TDD (нет)
- **Причина:** документация без кода.
- **Верификация:** README содержит: (1) команды smoke из s03–s06; (2) expected `total_samples`/`samples/sec`/`total_events` snippets; (3) known limits.

## Подробный процесс выполнения
1. Расширить существующий §MQTT: subsection «End-to-end smoke (publisher → broker → collector → writer)».
2. Команды:
   - `docker compose --profile mqtt-dev up -d --build`
   - `docker compose --profile mqtt-dev ps`
   - `docker compose --profile mqtt-dev logs -f writer emulator-mqtt`
   - `scripts/smoke-mqtt-stack.sh all`
   - `docker compose --profile mqtt-dev stop collector-mqtt` (graceful)
3. Expected snippets (примеры из s03/s05): `total_samples=[1-9]`, `samples/sec ...`, `total_events=[1-9]`.
4. Known limits: dev-only `aclfile readwrite`, без TLS/auth, без PSQL (writer-stub), publisher deterministic seed.

## Чекпоинт верификации
- AC-MQTT-S08: README §MQTT обновлён: реальные команды smoke + expected log snippets + known limits.

## Зависимости
- Upstream: s02–s06 — soft (команды/сниппеты берутся оттуда).

## Frontend
N/A.

## Следующий шаг
→ FINISH (graphify update) → BACK QA полный suite.
