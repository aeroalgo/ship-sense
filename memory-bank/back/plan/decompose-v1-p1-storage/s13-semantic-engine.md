# Шаг s13: SemanticEngine (tree, aggregate, tag state, diff hook)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-STO-03) — **closed** | **tdd:** yes
**Creative:** [CR-STO-03/creative-cr-sto-03-quarantine-ux.md](../../creative/creative-cr-sto-03-quarantine-ux.md)
**AC:** AC-STO-S13 (из плана §214–222, §778–792: in-memory tree, aggregate_status worst-of, get_tag_state, diff_native_map)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `SemanticEngine` — загружает VesselPack от loader, строит in-memory дерево (vessel→rooms→systems→mechanisms→tags), aggregate_status (worst-of-child), get_tag_state (normal|quarantine|no_data|stale), diff_native_map → QuarantineReport, acknowledge.

## Контекст
- **Consumes:** s12 loader/models, s15 quarantine (persist), ship-pack (s14).
- **Produces:** apps/edge/semantic/engine.py.
- **Downstream:** T-003 (HTTP/WS), T-004 UI, writer startup.
- **План:** §781 (API contract), §792 (aggregate), §804 (quarantine states), §216 (rebuild <2s).

## Файлы
- `apps/edge/semantic/engine.py` (Создание)
- `tests/storage/test_semantic_engine.py` (Создание)

## Интерфейсы (lean — без кода)
- class SemanticEngine:
  - def load(self, pack_dir: Path) -> None: ...
  - def get_tree(self) -> AssetNode: ...
  - def get_tag_meta(self, tag_id: str) -> TagMeta: ...
  - def get_mechanism_tags(self, mechanism_id: str) -> list[str]: ...
  - def aggregate_status(self, node_id: str) -> AggregateStatus: ...
  - def get_tag_state(self, tag_id: str) -> TagDisplayState: ...
  - def diff_native_map(self, new_map: NativeMap) -> QuarantineReport: ...
  - def acknowledge_quarantine(self, tag_id: str) -> None: ...
- AggregateStatus: worst critical > warning > quarantine > no_data > normal
- TagDisplayState: normal | quarantine | no_data | stale
- Rebuild <2s на 586 tags.

## TDD
- **Да:** load 586, aggregate worst, state no_data (no sample >30s), diff → quarantine list.
- pytest -k "semantic_engine"

## Подробный процесс выполнения
1. При load: from loader, build nested dict/tree, build tag→path index.
2. aggregate: рекурсивно снизу вверх, worst child.
3. get_tag_state: check quarantine table (s15), или no sample (stale_threshold 30s), или normal.
4. diff: сравнить new native_map vs approved → quarantine flags.
5. acknowledge: update tag_quarantine.acknowledged = true.
6. In-memory только; persist quarantine в s15.

## Верификация
- 586 tags load <2s.
- Mechanism aggregate = worst of children.
- New native without tag → quarantine.
- Блокер: s12, s14, s15.

## Блокеры / CREATIVE
CR-STO-03 (state mapping).
