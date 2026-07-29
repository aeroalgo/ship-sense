# Шаг s14: Handoff flow 6→5/1
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** no | **tdd:** yes
**AC:** AC-6-05; plan §6.3–6.4; PW-10


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Пересменочный UX: с Watch «Что активно сейчас» → overview/journal; session events visible in journal filters.

## Контекст
- **Consumes:** s08 session, s09–s10, s13 watch
- **Produces:** handoff CTAs + routing helpers + journal session filter chip

## Файлы
- `frontend/src/features/watch/HandoffButton.tsx` (Создание)
- `frontend/src/lib/routing/handoff.ts` (Создание)
- `frontend/src/features/journal/SessionEventFilter.tsx` (Создание) — опц.
- `frontend/src/features/watch/HandoffButton.test.tsx` (Создание)
- Modify WatchPage / JournalPage as needed

## Интерфейсы (lean — без кода)
- `HandoffButton` → `/overview` или `/journal?active=1`
- requires session for full watchkeeper name; anonymous still navigates
- session_started/ended appear as journal event types when API provides

## TDD (красная → зелёная)
1. **Тест:** handoff targets correct routes
2. **Тест:** logged-out still allows «active now» navigation
3. Parent Vitest; PW-10 in s16

## Подробный процесс выполнения
1. Implement §6.3 flow exactly.
2. Не дублировать business logic watch report.

## Чекпоинт верификации
- Documented flow works in UI
- PW-10 covered in s16 checklist
