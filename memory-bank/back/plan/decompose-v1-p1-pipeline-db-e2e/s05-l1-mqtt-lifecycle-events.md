# Шаг s05: L1 MQTT lifecycle → events в БД
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-PIPE-04
**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Тот же MQTT L1 harness: lifecycle transition (как в `test_mqtt_e2e`) → ≥1 row в `events` с ожидаемым `event_name` (напр. `aps.threshold.exceeded` или канон из e2e).

## Контекст
- **Consumes:** s04 файл/harness `test_mqtt_pipeline_db.py`; event mapping из mqtt channel maps.
- **Produces:** доп. тест(ы) в том же модуле.

## Файлы
- `tests/pipeline/test_mqtt_pipeline_db.py` (Модификация)

## Интерфейсы (lean — без кода)
- Переиспользовать wiring s04 (fixture/helper в модуле или conftest).
- Publish lifecycle/event payload path из mqtt-e2e канона.
- Assert: `SELECT count(*) FROM events WHERE event_name=:n` ≥ 1 (имя зафиксировать по map/e2e).
- Не мокать EventsRepo.

## TDD (красная → зелёная)
1. **Тест:** `test_mqtt_lifecycle_persists_event_to_db` — red.
2. **Реализация:** publish lifecycle + poll events.
3. **Запуск:** targeted pytest этой функции — PASS.

## Подробный процесс выполнения
1. Скопировать сценарий lifecycle из collector mqtt e2e (не mocks sink).
2. Poll `events` с timeout AssertionError.
3. FR-4 закрыт.

## Чекпоинт верификации
- AC-PIPE-04 green.
- Analog s04 регрессия зелёная.

## Зависимости
- s04 hard.

## Frontend
N/A.

## Следующий шаг
→ s06 (Modbus Contour B).
