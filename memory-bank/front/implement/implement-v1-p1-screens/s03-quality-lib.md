# [T-004 | s03 | quality-lib] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s03-quality-lib.md](../../plan/decompose-v1-p1-screens/s03-quality-lib.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `verification-before-completion`

## Сделано

- `Quality` / `AggregateStatus` = plan §15 + BACK OpenAPI (`good|bad|uncertain|stale|quarantine` + `unknown`)
- `worstOf` — quarantine > stale > bad > uncertain > good; empty → unknown
- `rollupNode` — worst child; unknown children ignored; quarantine → not good
- `DAMAGE_CLASS` константы: raznos → oil → temp → other
- `damageClassOf(eventName)` + `sortEvents`: active-unacked → damage class → ts desc → stable index
- Pure TS, без React/Next imports

## Файлы

- `frontend/src/lib/quality/types.ts`
- `frontend/src/lib/quality/rollup.ts`
- `frontend/src/lib/quality/rollup.test.ts`
- `frontend/src/lib/events/priority.ts`
- `frontend/src/lib/events/priority.test.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/lib/quality/ src/lib/events/`
- итог: 14 passed (8 rollup + 6 priority)
- Scenario E2E: n/a — нет user-visible UI (pure lib)

## Integration check

- [x] Quality enum ↔ BACK `collector.domain.models.Quality` / plan §15
- [x] Rollup worst-of ↔ plan §5.1.4 / BACK API §5.3 ranks
- [x] Damage class table ↔ plan §5.2.4 (разнос → масло → t°)
- [ ] storage keys — n/a
- [ ] env — n/a
- [ ] DB cols — n/a
- [ ] scenario E2E — n/a (lib-only)
