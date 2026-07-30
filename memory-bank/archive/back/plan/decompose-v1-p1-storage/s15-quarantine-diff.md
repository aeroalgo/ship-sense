# Шаг s15: Quarantine diff + persist (tag_quarantine)
**Plan ID:** v1-p1-storage
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-STO-03) — **closed** | **tdd:** yes
**Creative:** [CR-STO-03/creative-cr-sto-03-quarantine-ux.md](../../creative/v1-p1-storage/creative-cr-sto-03-quarantine-ux.md)
**AC:** AC-STO-S15 (из плана §219–222, §802–812: diff native → quarantine, state, acknowledge, persist)
**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Реализовать `semantic/quarantine.py` — diff новой native_map vs approved pack → список на карантин; persist в tag_quarantine; update get_tag_state в engine; acknowledge flow. Dual с quality=4 на samples (CR-STO-03).

## Контекст
- **Consumes:** s13 engine, s12 loader, s04 tag_quarantine table, s14 native_stub.
- **Produces:** apps/edge/semantic/quarantine.py.
- **Downstream:** s13 (вызов), T-004 UI, writer (quality quarantine при записи).
- **План:** §803 (table), §804 (states), §219 (diff), §788 (API).

## Файлы
- `apps/edge/semantic/quarantine.py` (Создание)
- `tests/storage/test_quarantine.py` (Создание)

## Интерфейсы (lean — без кода)
- def diff_native_map(approved: VesselPack, new_map: NativeMap) -> QuarantineReport: ...
- async def apply_quarantine(diff: QuarantineReport, session) -> None: ...  # insert/update tag_quarantine
- async def acknowledge(tag_id: str, session) -> None: ...
- QuarantineReport: added, removed, changed; list of TagQuarantineEntry.
- TagDisplayState enum.

## TDD
- **Да:** diff new native without tag → quarantine list; apply persist; acknowledge flips flag; state no_data if stale sample.
- pytest -k "quarantine"

## Подробный процесс выполнения
1. diff: сравнить native_id → tag_id mappings.
2. Для unknown native_id → reason="new native without tag", native_id_hint.
3. persist: INSERT ON CONFLICT UPDATE since/acknowledged=false.
4. Engine get_tag_state: check quarantine table first (если unacked → quarantine), затем stale/no sample, normal.
5. При записи sample в writer: если tag quarantined → quality=4.
6. Acknowledge: set acknowledged=true (UI action).

## Верификация
- New native → quarantine row, state=quarantine.
- Acknowledge → state меняется после reload.
- Sample written while quarantined → quality=4.
- Блокер: s04, s13, s14.

## Блокеры / CREATIVE
CR-STO-03 (mapping to quality flag).
