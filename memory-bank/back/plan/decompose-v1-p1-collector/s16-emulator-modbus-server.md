# Шаг s16: I3 Modbus TCP server adapter
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** no — **closed** | **tdd:** yes
**AC:** AC-I3-01, AC-I3-16 (modbus port)

- **Creative:** [CR-COL-03 / creative-collector-emulator-fidelity.md](../../creative/creative-collector-emulator-fidelity.md) — adapter использует общий profile-driven snapshot `TagGenerator`; сервер остаётся read-only.

**Контракт потребления s15:** один `TagGenerator`/snapshot provider и protocol-neutral mapping из профиля; transport dirt подключается через adapter hook, не через physics model.


**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
I3 Modbus TCP server adapter — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s15 TagGenerator
- **Produces:** Modbus TCP server serving holding/input from tag model

## Файлы
- `apps/edge/emulator/src/emulator/protocols/modbus_server.py` (Создание)
- `apps/edge/emulator/tests/test_modbus_server.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `ModbusServerAdapter` — start(host,port), stop, bind TagGenerator

## TDD (красная → зелёная)
1. **Тест:** `apps/edge/emulator/tests/test_modbus_server.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. Сервер отдаёт регистры по stub map; тик обновляет values @ ~1 Hz.

## Чекпоинт верификации
- клиент pymodbus читает регистры
- порт документирован
