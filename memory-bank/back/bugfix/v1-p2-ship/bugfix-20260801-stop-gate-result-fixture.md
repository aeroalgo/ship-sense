# [T-005 | QA-2] BUGFIX — изоляция stop-gate result.yaml

**Дата:** 2026-08-01  
**Эпик:** `v1-p2-ship`  
**Источник:** [qa-20260801-v1-p2-ship.md](../../qa/v1-p2-ship/qa-20260801-v1-p2-ship.md) → QA-2  
**Статус:** completed

## Симптом

При полном pytest suite `tests/storage/test_stop_gate.py::test_stop_gate_allows_after_handoff_fingerprint_change` блокировался stop-gate: `resolve_next()` создавал `loop/runtime/epic/result.yaml` в stub-состоянии `status: pending`, `draft: true`. При изолированном запуске тест мог ложно проходить, если импорт hook-модулей не завершался тем же образом.

## Root cause

Тест импортировал `epic_lib` через `importlib` без собственной настройки пути `.claude/hooks`. Поэтому поведение `resolve_next()` зависело от порядка запуска тестов и от того, добавил ли предыдущий тест `.claude/hooks` в `sys.path`. Тест также не моделировал обязательный переход runner от stub к финализированному `result.yaml` перед FINISH.

## Исправление

- `tests/storage/test_stop_gate.py` добавляет `.claude/hooks` в `sys.path` при загрузке модуля, устраняя зависимость от порядка pytest.
- `test_stop_gate_allows_after_handoff_fingerprint_change` явно записывает финализированный результат (`status: ok`, `draft: false`) после `resolve_next()` и до вызова stop-gate.
- Production hook не изменён; stub больше не скрывает нарушение контракта в тесте.

## Файлы

- `tests/storage/test_stop_gate.py`
- [implement step](../implement/implement-v1-p2-ship/s20-qa2-stop-gate.yaml)

## Тесты

- `.venv/bin/pytest tests/storage/test_stop_gate.py -q --tb=line` → `3 passed`
- `.venv/bin/pytest tests/storage/test_schemas.py -q --tb=line` → `2 passed`
- полный suite остаётся заблокирован независимыми QA-3/QA-4: отсутствует `access_audit` в SQLite fixture и `vessel.yaml` содержит 3 вместо 4 tags.

## Integration check

- [x] `resolve_next()` и stop-gate используют один import/result contract
- [x] финализированный `result.yaml` проверяется явно
- [x] storage metadata contract не изменён
- [x] QA-2 изолирован от QA-3/QA-4

## Следующая проверка

`BACK QA v1-p2-ship` — повторить эпический backend suite после закрытия QA-3 и QA-4.
