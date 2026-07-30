# Шаг s11: TrendChartContainer (CR-UI-02)
**Plan ID:** v1-p1-screens
**Next Phase:** done (IMPLEMENT)
**needs_creative:** yes (CR-UI-02) — **closed** | **tdd:** yes
**Implement:** [s11-chart-wrapper.md](../../implement/implement-v1-p1-screens/s11-chart-wrapper.md)
**AC:** plan §7; AC-8-01/04/05 partial; G chart not bare Grafana
**Creative:** [CR-UI-02-chart-lib.md](../../creative/v1-p1-screens/CR-UI-02-chart-lib.md) · spike [`frontend/src/features/trends/spike/`](../../../../frontend/src/features/trends/spike/) · spec [`chart-lib-spec.ts`](../../../../frontend/src/lib/trends/chart-lib-spec.ts) · dep `uplot`


**visible_ui:** yes
**Design skills (REQUIRED Read до UI-кода):**
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

## Цель
Обёртка графика: series gaps, setpoint lines, event markers; библиотека **uPlot** (CR-UI-02 closed).

## Контекст
- **Consumes:** s02 tokens, s06 DS chrome; [CR-UI-02-chart-lib.md](../../creative/v1-p1-screens/CR-UI-02-chart-lib.md) + spike + `chart-lib-spec.ts` + `uplot`
- **Produces:** `TrendChartContainer` + fixture tests

## Файлы
- `frontend/src/components/ds/TrendChartContainer.tsx` (Создание)
- `frontend/src/features/trends/chart/adapters/uplotAdapter.ts` (Создание) — thin adapter
- `frontend/src/components/ds/TrendChartContainer.test.tsx` (Создание)
- `frontend/src/features/trends/spike/` (reference — уже от creative)
- `frontend/src/lib/trends/chart-lib-spec.ts` (уже от creative)

## Интерфейсы (lean — без кода)
- component: `TrendChartContainer` — props: series, setpoints, markers, mode; testid `trend-chart`
- rules: null/bad → **break line** (не zero); setpoints horizontal; markers clickable
- perf: resolution=auto; 7d interactive budget §7.5; lib fixed = uPlot

## TDD (красная → зелёная)
1. **Тест:** fixture series with null bucket → gap (no interpolated zero)
2. **Тест:** setpoints render count
3. Integration fixture §9.4 #5
4. Parent Vitest green

## Подробный процесс выполнения
1. ~~Закрыть CR-UI-02 (benchmark spike).~~ done
2. Port spike `gaps`/`draw-overlays` → `uplotAdapter`; branded chrome DS0 colors — не дефолт Grafana theme.
3. Не подключать полный TrendsPage (s12).

## Чекпоинт верификации
- data-testid=`trend-chart`
- Creative md + `uplot` in package.json
- Gaps AC-8-05; setpoints AC-8-01 partial
