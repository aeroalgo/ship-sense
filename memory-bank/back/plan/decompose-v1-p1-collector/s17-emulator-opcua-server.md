# Шаг s17: I3 OPC UA server adapter
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no — **closed** | **tdd:** yes
**AC:** AC-I3-02, AC-I3-16 (opcua port)

- **Creative:** [CR-COL-03 / creative-collector-emulator-fidelity.md](../../creative/creative-collector-emulator-fidelity.md) — adapter публикует общий profile-driven snapshot и NodeIds из профиля; сервер остаётся read-only.

**Контракт потребления s15:** один `TagGenerator`/snapshot provider, protocol-neutral signal catalog и monitored updates без собственной physics-логики.


**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
I3 OPC UA server adapter — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s15 TagGenerator; CR-COL-03 process topology decision
- **Produces:** OPC UA server with nodes + monitored items

## Файлы
- `apps/edge/emulator/src/emulator/protocols/opcua_server.py` (Создание)
- `apps/edge/emulator/tests/test_opcua_server.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `OpcUaServerAdapter` — start, stop, bind TagGenerator, expose NodeIds

## TDD (красная → зелёная)
1. **Тест:** `apps/edge/emulator/tests/test_opcua_server.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Read-only nodes; browse + monitored items работают для collector B3.

## Чекпоинт верификации
- asyncua client subscribe получает updates
- порт документирован
