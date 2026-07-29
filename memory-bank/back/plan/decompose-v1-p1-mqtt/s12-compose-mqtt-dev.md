# Шаг s12: docker-compose profile mqtt-dev
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** no
**AC:** AC-MQTT-41

**code_surface:** infra

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Docker Compose profile `mqtt-dev`: mosquitto 2.x service + collector env/sources for mqtt; README fragment for local dev.

## Контекст
- **Consumes:** s01 config example; s09 integration patterns; T-001 s23 compose base
- **Produces:** compose overlay + env example + short README section

## Файлы
- `docker-compose.mqtt-dev.yml` или `docker-compose.yml` profile (Модификация/Создание)
- `infra/mosquitto/mosquitto.conf` (Создание — dev ACL allow subscribe from collector)
- `apps/edge/collector/README.md` (Модификация — mqtt-dev section)
- `.env.example` (Модификация — MQTT_BROKER_HOST, MQTT_USER, …)

## Интерфейсы (lean — без кода)
- n/a — infra/config only

## TDD (нет)
- **Причина:** scaffold / infra / compose wiring без новой бизнес-логики.
- **Верификация:** `docker compose --profile mqtt-dev config` valid; manual smoke: collector connects to mosquitto; document commands in README.

## Подробный процесс выполнения
1. Add mosquitto service port 1883 (dev plain MQTT per R-M7).
2. Mount mqtt sources yaml with panel_aps + panel_geu.
3. Optional emulator mqtt publisher service (depends s08).
4. Document profile activation and env vars (plan §7).

## Чекпоинт верификации
- AC-MQTT-41: profile documented
- compose config validates
- collector container starts with protocol mqtt sources (smoke)
