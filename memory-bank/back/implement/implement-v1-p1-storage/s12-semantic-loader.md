# BACK IMPLEMENT s12 — Semantic loader

## Реализация

- Создан `apps/edge/semantic/models.py` — Pydantic v2 модели: `VesselDef`, `SourceDef`, `AssetNode` (дерево vessel→engine_room→system→mechanism), `TagMeta` (+ `TagRange`, `TagSetpoints`, validator `alarm_bit`→`alarm_class`), `NativeMap`, `SemanticPack` (frozen); enums `SignalType`, `AlarmClass`, `AssetNodeKind`.
- Создан `apps/edge/semantic/loader.py` — `load_pack(pack_dir)` + `SemanticPackError`; кастомный `_UniqueKeyLoader` ловит дублирующие YAML-ключи с номером строки (PyYAML `safe_load` молча их сливает).
- Cross-file валидация fail-fast (план §796–802): уникальность тегов между механизмами, orphan tag в tag_map, tag в assets без meta, неизвестный `source_id`, `tag_count_expected ±0`, duplicate `native_id`=error, orphan `native_id`=warning (stub mode).
- Deterministic sha256 checksum по содержимому файлов (сортировка по имени → детерминизм).
- Создан `apps/edge/semantic/__init__.py` — public exports.

## Верификация

`PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_semantic_loader.py -q` — 14 passed.
Regression `tests/storage/` — 33 passed.
`task`→`verify` pre-FINISH gate — PASS (12 AC сверені).

## Статус

completed
