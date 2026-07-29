# Шаг s12: Screen 8 Trends
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-8-01..06; plan §5.3; deep link contract


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Страница трендов: quick/extended modes, TagPicker, series/setpoints/markers hooks, WS tail in quick, searchParams deep link.

## Контекст
- **Consumes:** s04 series/setpoints, s05 WS, s10 deep link, s11 chart
- **Produces:** features/trends/* page

## Файлы
- `frontend/src/features/trends/TrendsPage.tsx` (Создание)
- `frontend/src/features/trends/useSeries.ts` (Создание)
- `frontend/src/features/trends/useSetpoints.ts` (Создание)
- `frontend/src/features/trends/useEventMarkers.ts` (Создание)
- `frontend/src/features/trends/useTrendRealtime.ts` (Создание)
- `frontend/src/app/(authenticated)/trends/page.tsx` (Модификация)
- `frontend/src/features/trends/TrendsPage.test.tsx` (Создание)

## Интерфейсы (lean — без кода)
- searchParams: tag, from, to, mode=quick|extended
- hooks map §5.3.3–5.3.4
- 413 → StateShell «Сократите период (max 90 дней)»
- quick: WS tail on; extended: off by default

## TDD (красная → зелёная)
1. **Тест:** deep link prefill from query
2. **Тест:** marker click navigates journal intent
3. **Тест:** empty period copy
4. Parent Vitest; PW-04 in s16

## Подробный процесс выполнения
1. Progressive loading UX §5.3.5.
2. Multi-tag overlay via aggregate endpoint when needed.
3. ISA-101 colors from tokens only.

## Чекпоинт верификации
- AC-8-03 deep link
- AC-8-05 gap breaks
- NOT bare Grafana (AC-8-06)
