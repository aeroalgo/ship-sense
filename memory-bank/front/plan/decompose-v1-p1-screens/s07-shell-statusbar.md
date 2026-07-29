# Шаг s07: App shell + StatusBar + nav
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-1-05 StatusBar sticky; plan §4.2–4.3; routes table


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Authenticated layout: sticky StatusBar, nav (Обзор|Журнал|Тренды|Вахтенный), slot banners, QueryClient provider.

## Контекст
- **Consumes:** s02, s04–s06
- **Produces:** routing tree + shell wire StatusBar←WS/REST

## Файлы
- `frontend/src/app/(authenticated)/layout.tsx` (Создание)
- `frontend/src/app/(authenticated)/overview/page.tsx` (Создание) — placeholder
- `frontend/src/app/(authenticated)/journal/page.tsx` (Создание) — placeholder
- `frontend/src/app/(authenticated)/trends/page.tsx` (Создание) — placeholder
- `frontend/src/app/(authenticated)/watch/page.tsx` (Создание) — placeholder
- `frontend/src/features/shell/AppNav.tsx` (Создание)
- `frontend/src/features/shell/useStatusBarAlarms.ts` (Создание)
- `frontend/src/app/layout.tsx` (Модификация) — providers
- `frontend/src/features/shell/AppNav.test.tsx` (Создание)

## Интерфейсы (lean — без кода)
- layout: StatusBar sticky + AppNav touch≥48 + children
- hook: `useStatusBarAlarms` — REST bootstrap GET /api/events + WS events
- nav click → routes §4.2; alarm chip → `/journal?…`
- SessionChip slot (wire full in s08)

## TDD (красная → зелёная)
1. **Тест:** AppNav — 4 links testids; active route class
2. **Тест:** StatusBar click handler receives alarm id (RTL)
3. Red → implement → green

## Подробный процесс выполнения
1. Routes exactly §4.2; root redirect login/overview.
2. StatusBar всегда видна без скролла контента.
3. Placeholders экранов — StateShell loading до feature steps.

## Чекпоинт верификации
- Nav touch targets ≥48px
- StatusBar data-testid=`status-bar`
- Нет write/ack UI
