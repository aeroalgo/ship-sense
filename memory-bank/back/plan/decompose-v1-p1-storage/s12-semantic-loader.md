# Шаг s12: Semantic loader (YAML + pydantic validate)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-STO-03) — **closed** | **tdd:** yes
**Creative:** [CR-STO-03/creative-cr-sto-03-quarantine-ux.md](../../creative/creative-cr-sto-03-quarantine-ux.md)
**AC:** AC-STO-S12 (из плана §214–222, §795–801: load ship-pack, fail-fast validation, unique tags, no orphans)
**code_surface:** model

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`

## Цель
Реализовать `semantic/loader.py` + `models.py` — Pydantic v2 модели для vessel/assets/tag_map/timezone/native_map_stub; функция load_pack(dir) → validated tree + checksum; fail-fast с точным path/line на ошибках.

## Контекст
- **Consumes:** ship-pack/makarov/*.yaml (s14); план §677–777 (YAML examples).
- **Produces:** apps/edge/semantic/loader.py, models.py.
- **Downstream:** s13 SemanticEngine, s14 (ship-pack), writer/api startup.
- **План:** §781 (API), §794 (validation rules), §216 (fail-fast).

## Файлы
- `apps/edge/semantic/__init__.py` (Создание)
- `apps/edge/semantic/models.py` (Создание: AssetNode, TagMeta, VesselPack, etc.)
- `apps/edge/semantic/loader.py` (Создание: load_pack, validate)
- `tests/storage/test_semantic_loader.py` (Создание; fixtures minimal)

## Интерфейсы (lean — без кода)
- class VesselPack(BaseModel): vessel, engine_rooms, sources, tags...
- def load_pack(pack_dir: Path) -> VesselPack: ...
- Validation: all tags unique, every tag in exactly one mechanism, tag_map matches assets, count_expected ±0 for prod.
- Checksum = sha256 of files.

## TDD
- **Да:** broken ref, duplicate tag, orphan tag, missing count → ValidationError с path/line.
- pytest -k "semantic_loader"

## Подробный процесс выполнения
1. Pydantic модели с Field + validator.
2. loader: read yaml, parse, validate cross-refs, compute checksum.
3. Error messages: "tag_map.yaml:42: duplicate tag TAI4101".
4. Support stub native_map.

## Верификация
- load minimal 5-tag pack → tree ok.
- bad pack → exact error.
- Блокер: s14 (ship-pack files).

## Блокеры / CREATIVE
CR-STO-03 (quarantine later).
