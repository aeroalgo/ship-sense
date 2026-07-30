# Шаг s08: B2 ModbusTcpConnector + poll scheduler
**Plan ID:** v1-p1-collector
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (done) | **tdd:** yes
**AC:** AC-B2-05, AC-B2-06, AC-B2-10, AC-B1-03, AC-B1-11

- **CREATIVE:** CR-COL-02 → [creative-collector-modbus-poll-groups.md](../../creative/v1-p1-collector/creative-collector-modbus-poll-groups.md) ✅ **closed**

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
B2 ModbusTcpConnector + poll scheduler — один атомарный IMPLEMENT-заход с проверяемым deliverable.

## Контекст
- **Consumes:** s03, s06, s07; CR-COL-02 poll grouping algorithm
- **Produces:** ModbusTcpConnector plugin; poll_scheduler; register in PluginRegistry

## Файлы
- `apps/edge/collector/src/collector/plugins/modbus/poll_scheduler.py` (Создание)
- `apps/edge/collector/src/collector/plugins/modbus/connector.py` (Создание)
- `apps/edge/collector/tests/unit/test_modbus_connector.py` (Создание)

## Интерфейсы (lean — без кода)
- class: `PollScheduler` — build_groups(map, max_gap, max_regs, hz) → list[PollGroup]
- class: `ModbusTcpConnector(BaseSourceConnector)` — connect/read/subscribe(poll emulate)/discover_tags/disconnect
- register: protocol `modbus_tcp`

## TDD (красная → зелёная)
1. **Тест:** `tests/unit/test_modbus_connector.py`
2. **Запуск:** тесты падают (реализации нет).
3. **Реализация:** минимальный код по интерфейсам и процессу ниже.
4. **Запуск:** тесты проходят.

## Подробный процесс выполнения
1. До IMPLEMENT: CR-COL-02 (max_gap, max_regs, heterogeneous hz). ✅ **done**
2. subscribe = internal poll loop @ group hz → on_sample RawSample.
3. diag mode: log raw regs → decoded (flag).
4. discover_tags из локальной карты.

## Чекпоинт верификации
- группы не превышают max_regs
- subscribe эмулирует poll
- PluginRegistry.create(modbus_tcp) работает

## Handoff (CREATIVE → IMPLEMENT)
- **Creative:** [CR-COL-02](../../creative/v1-p1-collector/creative-collector-modbus-poll-groups.md) — алгоритм группировки (max_gap, max_regs, min hz), дизайн ModbusTcpConnector (poll loop per group), diag mode (MODBUS_DEBUG).
- **Рекомендации:**
  - PollScheduler.build_groups: greedy merge + explicit groups support.
  - Connector: один asyncio.Task на группу; supervisor владеет reconnect.
  - Diag: env `MODBUS_DEBUG=1` + config.extra.modbus_diag; logger `collector.modbus.diag`.
  - Error: вся группа → bad quality на exception (Modbus PDU атомарен).
- **Следующий шаг:** BACK IMPLEMENT s08 (TDD red→green).
- **Параллельно:** s10 (opcua connector) может идти независимо.
