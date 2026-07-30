# Шаг s03: L0 IPC frame → samples/events (SQL assert)
**Plan ID:** v1-p1-pipeline-db-e2e
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-PIPE-01, AC-PIPE-02
**code_surface:** test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Доказать: framed IPC через `IpcCanonicalSink` → живой `WriterService` → строки в `samples` и `events` без моков repos. Markers `integration`+`slow`.

## Контекст
- **Consumes:** s01 `start_tcp`; s02 fixtures `writer_endpoint`, `db_session`; `IpcCanonicalSink`; `TelemetrySample` / `Event` / `Quality`.
- **Produces:** `tests/pipeline/test_writer_ipc_db.py`.

## Файлы
- `tests/pipeline/test_writer_ipc_db.py` (Создание)

## Интерфейсы (lean — без кода)
- Тесты используют публичные: `IpcCanonicalSink.connect` / `write_sample` / `write_event` (или эквивалент Event path) / `flush`; SQL через session `text("SELECT …")`.
- Sample: `tag_id="TAI4101"`, `value=82.5`, `quality=GOOD(0)`, fixed UTC `ts`.
- Event: idempotency_key + `event_name` ожидаемый; COUNT≥1 в `events`.
- Poll loop до timeout (не только fixed sleep) — AssertionError с текстом при timeout.
- Не мокать `SamplesRepo.insert_batch` / `EventsRepo.insert_batch`.

## TDD (красная → зелёная)
1. **Тест:**
   - `test_ipc_sample_persists_to_samples` — FR-1/2/3 скелет plan §9.1.
   - `test_ipc_event_persists_to_events` — AC-PIPE-02.
   - Red: без writer/fixture или пустая БД → fail assert.
2. **Реализация:** только тесты + при необходимости мелкий helper poll в модуле (не prod).
3. **Запуск:** `.venv/bin/pytest tests/pipeline/test_writer_ipc_db.py -m "integration and slow" -q` PASS (Docker).

## Подробный процесс выполнения
1. Подключить sink к `writer_endpoint`.
2. Отправить sample/event; `flush`; poll SELECT.
3. Assert `pytest.approx` для float; quality int == 0 на happy-path.
4. NFR: L0 wall < 30s (session container уже поднят).

## Чекпоинт верификации
- AC-PIPE-01 / AC-PIPE-02 green.
- Нет AsyncMock на insert_batch в happy-path.

## Зависимости
- s01, s02 hard.

## Frontend
N/A.

## Следующий шаг
→ s04 (L1 MQTT samples).
