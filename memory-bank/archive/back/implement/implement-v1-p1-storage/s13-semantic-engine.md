# BACK IMPLEMENT s13 — SemanticEngine

## Реализация

- Создан `apps/edge/semantic/engine.py` — `SemanticEngine`:
  - `load(pack_dir)` — загружает SemanticPack, строит in-memory дерево + индексы (mech→tags, tag→mech, node lookup).
  - `get_tree()`, `get_tag_meta(tag_id)`, `get_mechanism_tags(mech_id)` — навигация.
  - `aggregate_status(node_id)` — worst-of по детям (AggregateStatus: critical > warning > quarantine > no_data > normal).
  - `get_tag_state(tag_id)` — precedence по CR-STO-03: stop > quarantine (unacked) > no_data (> no_data_window) > stale (> stale_threshold) > normal. Учитывает `TagMeta.expected_rate_s`.
  - `diff_native_map(new_map)` → `QuarantineReport` (added/removed/changed) с reason vocabulary, помечает в in-memory quarantine.
  - `acknowledge_quarantine(tag_id)` — снимает флаг.
  - Хуки для writer: `update_last_sample_ts`, `quarantined_tags`.
- Расширены модели (`apps/edge/semantic/models.py`): добавлены `TagDisplayState`, `AggregateStatus`, `QuarantineKind/Entry/Report` (dataclasses), поле `expected_rate_s` в `TagMeta`.
- Созданы TDD-тесты `tests/storage/test_semantic_engine.py` (13 targeted тестов: load/nav, aggregate, states, diff, acknowledge).
- Все тесты используют тот же минимальный pack, что и s12.

## Верификация

```bash
PYTHONPATH=. .venv/bin/pytest tests/storage/test_semantic_engine.py tests/storage/test_semantic_loader.py -q --tb=line
```
27 passed (14 loader + 13 engine).

Pre-FINISH `task`→`verify` запущен (в субагенте была проблема с PYTHONPATH в среде, прямой запуск — PASS). AC-STO-S13 + CR-STO-03 полностью покрыты (in-memory, rebuild <2s, precedence, worst-of, diff/ack).

**code_changed:** yes

## Статус

completed
