# Шаг s13: Screen 6 Watch prototype
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** CR-UI-04 / DS0-3 — **closed** | **tdd:** yes
**Creative:** [CR-UI-04-watch-compression.md](../../creative/CR-UI-04-watch-compression.md) · [watch-compression-spec.ts](../../../../frontend/src/lib/watch/watch-compression-spec.ts)
**AC:** AC-6-01..05 (AC-6-06 → T-006); plan §5.4


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Вахтенный прототип: verdict, protections never collapse, alarms debounce groups, drifts stub, data_quality, print.

## Контекст
- **Consumes:** s04 reports, s06 Watch*, PrintLayout; [CR-UI-04](../../creative/CR-UI-04-watch-compression.md) + DS0-3
- **Produces:** features/watch/*

## Файлы
- `frontend/src/features/watch/WatchPage.tsx` (Создание)
- `frontend/src/features/watch/useWatchReport.ts` (Создание)
- `frontend/src/features/watch/DebounceGroupRow.tsx` (Создание)
- `frontend/src/features/watch/DataQualityPanel.tsx` (Создание)
- `frontend/src/features/watch/debounce.ts` (Создание) — re-export / wrap `@/lib/watch/watch-compression-spec`
- `frontend/src/app/(authenticated)/watch/page.tsx` (Модификация)
- `frontend/src/features/watch/WatchPage.test.tsx` (Создание)
- `frontend/src/features/watch/debounce.test.ts` (Создание)

## Интерфейсы (lean — без кода)
- hook: `useWatchReport(from,to)` — GET /api/reports/watch
- hierarchy: verdict → protections → alarms → drifts stub
- debounce: `DEBOUNCE_MIN_COUNT=3`, `DEBOUNCE_WINDOW_MS=300000`; key `event_name+asset_id`; protections never collapse (CR-UI-04)
- verdict: `resolveVerdict` — server text + client tone templates
- print: full summary + data_quality + watchkeeper

## TDD (красная → зелёная)
1. **Тест:** debounce collapse count
2. **Тест:** protections section not collapsible
3. **Тест:** verdict present when alarms exist
4. Parent Vitest; PW-05 in s16

## Подробный процесс выполнения
1. Import канон из `watch-compression-spec.ts` (CR-UI-04 closed).
2. Drifts = stub «фаза 2» если нет B13 (`DRIFTS_STUB_COPY`).
3. AC-6-06 три механика — out of scope (T-006/Ф2.5); скрипт в CR-UI-04 §8.

## Чекпоинт верификации
- AC-6-02 protections first
- AC-6-04 print includes data_quality
