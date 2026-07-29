# Шаг s09: Screen 1 Overview
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** soft CR-UI-05 — **closed** | **tdd:** yes
**AC:** AC-1-01..06; plan §5.1; gate DS0-4 closed (s06); CR-UI-05 OverviewGroupCard floor

**Creative:** [CR-UI-05-post-density.md](../../creative/CR-UI-05-post-density.md) (`--overview-group-min-*`, type floor)


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Экран Обзор: AggregateShipStatus + группы нос/корма + WS values + quarantine/stale states + drill stub T-006.

## Контекст
- **Consumes:** s03 rollup, s04–s07, s06 DS cards; [CR-UI-05-post-density.md](../../creative/CR-UI-05-post-density.md) density floor
- **Produces:** features/overview/*

## Файлы
- `frontend/src/features/overview/OverviewPage.tsx` (Создание)
- `frontend/src/features/overview/useAssetsTree.ts` (Создание)
- `frontend/src/features/overview/useOverviewRealtime.ts` (Создание)
- `frontend/src/features/overview/DrillDownStubModal.tsx` (Создание)
- `frontend/src/app/(authenticated)/overview/page.tsx` (Модификация)
- `frontend/src/features/overview/OverviewPage.test.tsx` (Создание)

## Интерфейсы (lean — без кода)
- hooks: `useAssetsTree`, `useOverviewRealtime` — tag flatten ≤100
- page tree: AggregateShipStatus → MoSection → OverviewGroupCard[]
- drill: stub modal «Мнемосхема — фаза 2»
- states: loading/empty/error/partial/stale per §5.1.5

## TDD (красная → зелёная)
1. **Тест:** quarantine child → group Lamp not good
2. **Тест:** drill opens stub not 404
3. **Тест:** empty honest copy с first_sample_ts
4. Parent Vitest; PW-02/07 later s16

## Подробный процесс выполнения
1. Только ds/* для UI блоков (G-DS0-4-01).
2. Client rollup mirrors worstOf; assert vs fixture.
3. ISA-101: норма без цветного «свечения».

## Чекпоинт верификации
- AC-1-03 quarantine
- AC-1-04 stub
- StatusBar visible (shell)
