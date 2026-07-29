# [T-004 | s14 | handoff-flow] IMPLEMENT

**Plan ID:** v1-p1-screens
**Decompose step:** [s14-handoff-flow.md](../../plan/decompose-v1-p1-screens/s14-handoff-flow.md)
**Implement index:** [index.md](index.md)
**Дата:** 2026-07-26  
**Уровень:** L4  
**Статус:** done

## Skills

- `tdd`
- `frontend-testing`
- `playwright-best-practices`
- `playwright-generate-test`
- `next-best-practices`
- `vercel-react-best-practices`
- `vercel-composition-patterns`
- `frontend-patterns`
- `frontend-design` *(visible UI — HARD)*
- `design-taste-frontend` *(visible UI — HARD)*
- `emil-design-eng` *(visible UI — HARD)*
- `impeccable` *(visible UI — HARD)*
- `high-end-visual-design` *(visible UI — HARD)*
- `ui-ux-pro-max` *(visible UI — HARD)*
- `verification-before-completion`

**Design read:** ship-bridge HMI handoff CTA strip (ISA-101) — console chrome CTAs; not SaaS digest.

## Сделано

- `lib/routing/handoff.ts` — href канон §6.3 / CR-UI-04 + flags `active=1` / `session=1`
- `HandoffButton` — «К активным тревогам» + «Что активно сейчас» (`data-testid=handoff-active-now`)
- WatchPage wired через HandoffButton (anonymous OK)
- Journal: chip «Активные» + `SessionEventFilter` (смены / session_started|ended)
- PW-10 scenario: `e2e/specs/watch/handoff-flow.spec.ts`

## Файлы

- `frontend/src/lib/routing/handoff.ts`
- `frontend/src/lib/routing/handoff.test.ts`
- `frontend/src/features/watch/HandoffButton.tsx`
- `frontend/src/features/watch/HandoffButton.test.tsx`
- `frontend/src/features/watch/WatchPage.tsx`
- `frontend/src/features/journal/SessionEventFilter.tsx`
- `frontend/src/features/journal/journalFilters.ts`
- `frontend/src/features/journal/JournalPage.tsx`
- `frontend/src/features/journal/useEventsInfinite.ts`
- `frontend/src/features/journal/useEventsRealtime.ts`
- `frontend/e2e/specs/watch/handoff-flow.spec.ts`

## Тесты

- cmd: `cd frontend && npm test -- src/lib/routing/handoff.test.ts src/features/watch/HandoffButton.test.tsx src/features/watch/WatchPage.test.tsx src/features/journal/JournalPage.test.tsx`
- итог: 13 passed
- Scenario E2E: `npx playwright test e2e/specs/watch/handoff-flow.spec.ts` — 2 passed

## Integration check

- [x] handoff hrefs ↔ `/overview` + `/journal?severity=alarm&active=1`
- [x] `active=1` / `session=1` ↔ journalFilters + JournalPage
- [x] `handoff-active-now` ↔ PW-10
- [x] session audit event_name ∈ {session_started, session_ended} + source=edge
- [ ] Full PW suite polish → s16
