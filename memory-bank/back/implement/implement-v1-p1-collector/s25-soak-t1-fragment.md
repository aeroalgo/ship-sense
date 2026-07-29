# [T-001 | s25 | soak-t1-fragment] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s25-soak-t1-fragment.md](../../plan/decompose-v1-p1-collector/s25-soak-t1-fragment.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-27
**Уровень:** L2 по atomic soak test step
**Статус:** done

## Сделано

- Создан `apps/edge/collector/tests/soak/test_24h_fragment.py`.
- Harness поднимает реальный `ModbusServerAdapter`, `ModbusTcpConnector` и `SourceSupervisor` с коротким polling interval.
- В цикле выполняются connection drops через `connector.disconnect()` + restart emulator; после каждого восстановления проверяется появление samples.
- Добавлены resource leak checks: количество живых asyncio tasks и socket descriptors сравнивается с steady-state и baseline с небольшим допуском.
- Тест помечен `pytest.mark.slow`; маркер зарегистрирован в collector `pyproject.toml`.
- Параметры запускаются через env: `SHIPSENSE_SOAK_DURATION_SEC`, `SHIPSENSE_SOAK_DROP_INTERVAL_SEC`, `SHIPSENSE_SOAK_DROP_DURATION_SEC`.
- В `apps/edge/collector/README.md` добавлен CI runbook для 60s и manual runbook для 24h.

## Файлы

- `apps/edge/collector/tests/soak/test_24h_fragment.py` (создание)
- `apps/edge/collector/pyproject.toml` (модификация: slow marker)
- `apps/edge/collector/README.md` (модификация: soak runbook)

## TDD

- red: первый targeted запуск завершился `IndexError: list index out of range` при запуске emulator с profile, в котором отсутствовал native tag `41000`, обязательный для `stub_aps_main.yaml`.
- fix: добавлен профильный сигнал `STATUS` с native id `41000` и `boolean` типом; harness теперь соответствует используемой карте тегов.
- green: `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src SHIPSENSE_SOAK_DURATION_SEC=2 SHIPSENSE_SOAK_DROP_INTERVAL_SEC=0.5 SHIPSENSE_SOAK_DROP_DURATION_SEC=0.05 .venv/bin/pytest -q apps/edge/collector/tests/soak/test_24h_fragment.py -m slow` → **1 passed in 2.47s**.

Полный collector suite не запускался: это относится к `BACK QA`.
24h manual run не запускался в рамках IMPLEMENT.

## Integration check (§0.11)

- [x] `stub_aps_main.yaml` ↔ profile harness содержит все запрашиваемые native ids `40101`, `40107`, `41000`.
- [x] `SourceSupervisor` ↔ connector lifecycle: supervisor owns start/stop; soak exercises disconnect/recovery without changing production interfaces.
- [x] `ModbusServerAdapter` runtime port ↔ `SourceConfig.endpoint` and `AsyncModbusClient` endpoint.
- [x] `pytest.mark.slow` ↔ registered in `apps/edge/collector/pyproject.toml`.
- [x] README commands use root `PYTHONPATH` and configured env knobs.

## Чекпоинт верификации

- [x] short CI fragment green.
- [x] periodic connection drops exercised (`drops >= 1`).
- [x] samples received before and after each recovery.
- [x] task count bounded during soak and after cleanup.
- [x] socket descriptor count bounded during soak and after cleanup.
- [x] 24h runbook documented; manual 24h execution remains operator action.
