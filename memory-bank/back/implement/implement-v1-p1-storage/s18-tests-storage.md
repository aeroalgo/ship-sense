# BACK IMPLEMENT s18 — tests storage

## Реализация

- Добавлены targeted contract tests для numeric payloads и reject нечисловых значений в `tests/storage/test_storage_contracts.py`.
- Добавлены integration-style тесты writer count, event/sample correlation и quota degrade без изменения events в `tests/storage/test_storage_integration.py`.
- Добавлен load harness для 586 samples/s + 2 events/s с проверками queue drain, counts и p95 flush в `tests/storage/test_load_586hz.py`.
- `tests/conftest.py` добавляет общую pytest-конфигурацию маркеров.
- `pyproject.toml` включает `tests/storage` в `testpaths` и регистрирует marker `load`.
- Существующие unit-покрытия time_axis, samples_repo, events_repo, writer, quota, health, semantic и quarantine сохранены и проходят.

## Верификация/Тесты

```text
PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_storage_contracts.py tests/storage/test_storage_integration.py tests/storage/test_load_586hz.py -q
9 passed

PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/ -q
63 passed
```

Docker Compose и полный nightly load не запускались: storage integration tests используют mocks; эти проверки остаются parent/CI scope.

## Статус

completed
