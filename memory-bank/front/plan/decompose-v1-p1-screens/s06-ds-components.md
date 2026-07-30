# Шаг s06: DS0-4 components + Storybook scaffold
**Plan ID:** v1-p1-screens
**Next Phase:** FRONT IMPLEMENT
**needs_creative:** yes (CR-UI-03 / DS0-1) — **closed** | **tdd:** yes
**AC:** G-DS0-4-01..05; G-DS0-1-06; plan §3.4 component table
**Creative:** [CR-UI-03-alarm-grammar.md](../../creative/v1-p1-screens/CR-UI-03-alarm-grammar.md) · SVG [`frontend/public/ds/lamps/`](../../../../frontend/public/ds/lamps/) · spec [`lamp-grammar-spec.ts`](../../../../frontend/src/lib/ds/lamp-grammar-spec.ts)


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Библиотека `components/ds/*` фазы 1 + SVG lamps + Storybook; gate до вёрстки экранов.

## Контекст
- **Consumes:** s01–s03, s02 tokens; [CR-UI-03-alarm-grammar.md](../../creative/v1-p1-screens/CR-UI-03-alarm-grammar.md) + DS0-1 SVG в `frontend/public/ds/lamps/`; `lamp-grammar-spec.ts`
- **Produces:** все компоненты §3.4 (кроме TrendChartContainer → s11)

## Файлы
- `frontend/public/ds/lamps/*.svg` (уже от CR-UI-03) — wire в `<Lamp />`
- `frontend/src/components/ds/Lamp.tsx` (Создание)
- `frontend/src/components/ds/StatusBar.tsx` (Создание)
- `frontend/src/components/ds/AggregateShipStatus.tsx` (Создание)
- `frontend/src/components/ds/OverviewGroupCard.tsx` (Создание)
- `frontend/src/components/ds/EventRow.tsx` (Создание)
- `frontend/src/components/ds/EventFilters.tsx` (Создание)
- `frontend/src/components/ds/TagPicker.tsx` (Создание)
- `frontend/src/components/ds/WatchVerdict.tsx` (Создание)
- `frontend/src/components/ds/WatchSection.tsx` (Создание)
- `frontend/src/components/ds/LoginTile.tsx` (Создание)
- `frontend/src/components/ds/StateShell.tsx` (Создание)
- `frontend/src/components/ds/FreshnessBanner.tsx` (Создание)
- `frontend/src/components/ds/QuarantineBanner.tsx` (Создание)
- `frontend/src/components/ds/PrintLayout.tsx` (Создание)
- `frontend/src/components/ds/SessionChip.tsx` (Создание)
- `frontend/src/components/ds/index.ts` (Создание)
- `frontend/src/components/ds/Lamp.test.tsx` (Создание)
- `frontend/src/components/ds/StateShell.test.tsx` (Создание)
- Storybook config + stories per component (Создание)

## Интерфейсы (lean — без кода)
- `Lamp` — props: severity, lifecycle, quality, size; testid `lamp`
- `StatusBar` — alarms[], onAlarmClick, compact; `status-bar`
- `AggregateShipStatus` — status, label; `ship-status`
- `OverviewGroupCard` — name, status, alarmCount, onClick; `overview-group`
- `EventRow` — event, onTrendClick; `event-row`
- `EventFilters` — filters, onChange; `journal-filters`
- `TagPicker` — tags[], onAdd; `tag-picker`
- `WatchVerdict` — text, tone; `watch-verdict`
- `WatchSection` — title, items, collapsible; `watch-section`
- `LoginTile` — person, rank, active; `login-tile`
- `StateShell` — variant loading|empty|error|partial|stale; `state-shell`
- `FreshnessBanner` / `QuarantineBanner` / `PrintLayout` / `SessionChip` — props как §3.4
- **не включать** `TrendChartContainer` (s11)

## TDD (красная → зелёная)
1. **Тест:** Lamp — каждая комбинация severity×quality даёт уникальный data-state; quarantine ≠ good class
2. **Тест:** StateShell — 5 variants render testid
3. Stories: loading/empty/error/partial/stale per G-DS0-4-02
4. Parent Vitest green

## Подробный процесс выполнения
1. CR-UI-03 уже закрыт — читать creative §3–9 + `lamp-grammar-spec.ts`; grayscale: `/ds/lamps/grayscale-proof.html`.
2. Lamp только через SVG + tokens, без hardcoded hex.
3. data-testid prefixes строго §3.4.
4. Storybook local catalog (G-DS0-4-04).
5. После шага — **разрешены** screen shells s07+.

## Чекпоинт верификации
- Grayscale: формы различимы (creative evidence)
- Экран 1 сможет собраться только из ds/* (G-DS0-4-01)
- Нет слова «AI» в copy
