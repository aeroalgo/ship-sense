# [T-005 | QA-4] BUGFIX — обязательные tags в test vessel pack

**Дата:** 2026-08-01  
**Эпик:** `v1-p2-ship`  
**Источник:** [qa-20260801-v1-p2-ship.md](../../qa/v1-p2-ship/qa-20260801-v1-p2-ship.md) → QA-4  
**Статус:** completed

## Симптом

`apps/api/tests/api/test_assets_tree.py` и оба semantic setup-теста в `apps/api/tests/api/test_series.py` не могли загрузить `apps/api/fixtures/ship-pack-min`: loader сообщал `source 'test': expected 4 tags, got 3`.

## Root cause

`vessel.yaml` уже объявлял для source `test` обязательный `tag_count_expected: 4`, а `tag_map.yaml` и `assets.yaml` описывали только три тега. Четвёртым доменным тегом должен быть `SKT001`: он уже указан как `vessel_state.rpm_tag` в `vessel.yaml`. Фикстура была внутренне неполной, поэтому fail-closed cross-file validation останавливал загрузку до вызова assets/series API. Это не исправление через ослабление валидации: согласованы все связанные fixture-файлы.

## Исправление

- `tag_map.yaml` получил `SKT001` с `unit: rpm`, `source_id: test`, `signal_type: analog`.
- `assets.yaml` связал `SKT001` с существующим mechanism node, чтобы tag map и asset tree оставались взаимно полными.
- `test_assets_tree.py` обновил ожидаемый набор листьев до четырёх тегов.

## Файлы

- `apps/api/fixtures/ship-pack-min/tag_map.yaml`
- `apps/api/fixtures/ship-pack-min/assets.yaml`
- `apps/api/tests/api/test_assets_tree.py`

## Тесты

- cmd: `.venv/bin/pytest apps/api/tests/api/test_assets_tree.py apps/api/tests/api/test_series.py -q --tb=line`
- итог: `3 passed`
- cmd: `.venv/bin/pytest apps/api/tests/api/test_session.py -q --tb=line`
- итог: `2 passed`
- cmd: `.venv/bin/pytest -q --tb=line`
- итог: `580 passed, 12 deselected, 3 warnings`

## Integration check

- [x] `tag_map.yaml` metadata и `assets.yaml` references содержат одинаковые четыре тега
- [x] `SKT001` согласован с `vessel_state.rpm_tag` и `vessel_state.rpm_unit`
- [x] `source_id: test` учитывается в `tag_count_expected: 4`
- [x] fail-closed semantic loader не ослаблен
- [x] assets/series/session targeted paths green
