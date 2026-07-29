# Шаг s10: Screen 5 Journal
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-5-01..06; plan §5.2; print provenance


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Журнал: фильтры+URL sync, virtual list, sort, WS prepend, print, deep link to trends, Q4 banner, no ack button.

## Контекст
- **Consumes:** s03 priority, s04 events, s05 WS, s06 EventRow/Filters/PrintLayout
- **Produces:** features/journal/*

## Файлы
- `frontend/src/features/journal/JournalPage.tsx` (Создание)
- `frontend/src/features/journal/useEventsInfinite.ts` (Создание)
- `frontend/src/features/journal/useEventsRealtime.ts` (Создание)
- `frontend/src/features/journal/ReconstructionBanner.tsx` (Создание)
- `frontend/src/lib/routing/trendsDeepLink.ts` (Создание)
- `frontend/src/app/(authenticated)/journal/page.tsx` (Модификация)
- `frontend/src/features/journal/JournalPage.test.tsx` (Создание)
- `frontend/src/styles/print-journal.css` (Создание)

## Интерфейсы (lean — без кода)
- hooks: infinite cursor GET /api/events; WS prepend dedupe by id
- filters sync URL query
- `trendsDeepLink(event)` → `/trends?tag&from&to&mode=quick`
- ReconstructionBanner if `X-Events-Reconstruction`
- footnote copy: «Квитируется на панели АПС» — **нет** кнопки квитирования

## TDD (красная → зелёная)
1. **Тест:** filter narrows; URL params
2. **Тест:** deep link window correct
3. **Тест:** no acknowledge control in DOM
4. Parent Vitest; PW-03/04 in s16

## Подробный процесс выполнения
1. `@tanstack/react-virtual` для списка.
2. Print: hide chrome; PrintLayout provenance; monochrome lamps.
3. Q4 incomplete → reconstruction banner path.

## Чекпоинт верификации
- AC-5-05 no ack
- AC-5-03 deep link
- Sort active-unacked top
