# BACK IMPLEMENT s15 — Quarantine diff + persist (tag_quarantine)

## Реализация
- Создан `apps/edge/semantic/quarantine.py`:
  - `diff_native_map(approved: NativeMap | None, new_map: NativeMap, *, known_tags: set[str] | None) -> QuarantineReport` — pure, deterministic. Только реальные теги из known_tags попадают в quarantine cache; unknown-tag entries report'ятся (added), но не кэшируются.
  - `apply_quarantine(report, session)` — full-reconcile: upsert added+changed (ON CONFLICT DO UPDATE, reset acknowledged=false при новой причине), delete removed.
  - `acknowledge(tag_id, session)` — UPDATE acknowledged=true.
  - `refresh_quarantine_cache(session, target_set)` — load unacked → caller set (опционально).
- Интеграция в `apps/edge/semantic/engine.py`:
  - `diff_native_map` теперь делегирует в `quarantine.diff_native_map`, обновляет только in-memory cache для реальных тегов.
  - Добавлен `refresh_quarantine_from(tag_ids)` для синхронизации кэша после persist.
  - Сохранена обратная совместимость с s13-тестами.
- Dual-path в `apps/edge/storage/writer.py`:
  - `__init__` принимает `quarantined_tags: Callable[[], frozenset[str]] | None`.
  - В `flush_batches` перед insert: для samples с tag в quarantine set — force `quality=Quality.QUARANTINE` (override только 0–3; bad(5) не трогаем).
- Обновлены экспорты `apps/edge/semantic/__init__.py` (Quarantine* модели + `quarantine` submodule).
- TDD: `tests/storage/test_quarantine.py` (6 targeted тестов: pure diff, apply/ack, dual-path writer quality=4).
- Фиксы совместимости в существующих `test_semantic_engine.py` (unknown tag → report, но не в quarantine cache + state=NO_DATA).

## Верификация
```bash
PYTHONPATH=.:apps/edge/collector/src .venv/bin/pytest tests/storage/test_quarantine.py tests/storage/test_semantic_engine.py -q --tb=line
```
Вывод: `19 passed`.

Дополнительно проверено:
- diff: added (unmapped + to_unknown), changed (remap), removed, no-op на identical.
- apply: upsert + commit.
- acknowledge: update acknowledged.
- writer dual-path: good/uncertain → 4; bad остаётся bad.
- engine.get_tag_state: quarantine precedence для реальных тегов; unknown → NO_DATA.
- Нет регрессий loader/engine (s12/s13).

**code_changed:** yes

## Статус
completed
