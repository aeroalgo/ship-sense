# Шаг s06: L1 Modbus emulator → samples
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-PIPE-05
**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Contour B: `ModbusServerAdapter` (или integration fixture) → ModbusTcpConnector + Normalizer → `IpcCanonicalSink` → writer → `samples` COUNT≥1 для mapped tag (канон `TAI4101` / native `40101` из fixture map).

## Контекст
- **Consumes:** s01/s02; pattern `test_modbus_emulator.py` / modbus_integration fixtures; tag_map.
- **Produces:** `tests/pipeline/test_modbus_pipeline_db.py`.
- OPC UA — **не** в этом шаге (optional later / QA).

## Файлы
- `tests/pipeline/test_modbus_pipeline_db.py` (Создание)

## Интерфейсы (lean — без кода)
- Live Modbus TCP ephemeral; connector config указывает на него; sink=IPC→writer_endpoint.
- Assert: mapped `tag_id` COUNT≥1 в `samples` (имя из map fixture — задокументировать в тесте).
- Markers `integration`+`slow`.
- Без моков insert_batch.

## TDD (красная → зелёная)
1. **Тест:** `test_modbus_emulator_persists_sample_to_db` — red.
2. **Реализация:** wire Contour B.
3. **Запуск:** `.venv/bin/pytest tests/pipeline/test_modbus_pipeline_db.py -q` PASS.

## Подробный процесс выполнения
1. Reuse emulator Modbus adapter start/stop.
2. Connector+Normalizer+IPC; poll SQL.
3. FR-5.

## Чекпоинт верификации
- AC-PIPE-05 green.
- DoD Contour B закрыт на L1.

## Зависимости
- s01–s02; T-001 modbus fixtures.

## Frontend
N/A.

## Следующий шаг
→ s07 (compose L2 smoke).
