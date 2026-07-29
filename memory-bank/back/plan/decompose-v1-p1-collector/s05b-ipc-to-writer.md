# Шаг s05b: IPC framing collector → writer (CanonicalSink client)
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-INT-01, AC-INT-02, стык T-002 §21.1

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
IPC framing collector → writer (CanonicalSink client) — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s05 CanonicalSink; TelemetrySample/Event JSON schema
- **Produces:** IPC client sink (Unix socket / localhost framed); contract docs для writer

## Файлы
- `apps/edge/collector/src/collector/sink/ipc_sink.py` (Создание)
- `apps/edge/collector/tests/unit/test_ipc_sink.py` (Создание)
- `apps/edge/collector/README.md` (Модификация) — framing contract

## Интерфейсы (lean — без кода)
- class: `IpcCanonicalSink(CanonicalSink)` — connect(path|host:port), write_sample, write_event, close
- frame: length-prefixed JSON lines или NDJSON — зафиксировать в README (совместимо с T-002 writer server stub)

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_ipc_sink.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Реализовать клиент IPC по ADR day-1 (collector ‖ writer).
2. В тестах: mock server принимает frames; round-trip sample/event.
3. Потеря связи → явная ошибка/reconnect policy (не silent drop) — политика в README.

## Чекпоинт верификации
- round-trip TelemetrySample через mock writer
- README описывает framing
- compose service `writer` упоминается как peer
