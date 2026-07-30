# FRONT BUGFIX — trends chart UI (stroke / label / TagPicker)

**Date:** 2026-07-27  
**Slug:** `trends-chart-ui`  
**Screen:** `/trends` (T-004 s12)  
**Status:** done

## Symptom

1. Линия тренда чёрная — сливается с тёмным фоном графика.
2. Подпись графика (`tagLabel`) не совпадает с выбранными тегами в TagPicker.
3. Выбранные теги (chips) стоят над `<select>` и сдвигают выбор тега вниз при добавлении.

## Root cause

| # | Cause |
|---|--------|
| 1 | `DEFAULT_CHART_TOKENS.seriesStroke = "var(--accent, …)"` передаётся в uPlot/canvas. Canvas **не** резолвит CSS custom properties → invalid stroke → чёрный `#000`. |
| 2 | `tagLabel={series.data?.name ?? parsed.tags[0]}` — имя из API series (или tag_id), а не display-name выбранных тегов из каталога AssetTree. |
| 3 | `TagPicker`: блок selected chips **перед** `<select>` → рост chips сдвигает select вниз. |

## Fix

1. `resolveChartTokens(el)` + `isCanvasSafeColor` → concrete color в uPlot; fallback `#6b9fd4` (palette accent family). `data-series-stroke` на chart.
2. `tagLabel` = join имён `catalog` по `parsed.tags`.
3. **Separate containers:** `TagPicker` = только `<select>` в header; `SelectedTags` (`data-testid="selected-tags"`) = отдельный ряд под header на `TrendsPage`. Chips не в одном flex-столбце с select → select не смещается.

## Skills (design stack — visible UI)

- frontend-design · design-taste-frontend · emil-design-eng · impeccable · high-end-visual-design · ui-ux-pro-max — Read
- tdd · playwright-best-practices · playwright-generate-test · verification-before-completion · requesting-code-review — Read

## Regression evidence

- Vitest: TagPicker + resolveChartTokens + TrendsPage tagLabel + TrendChartContainer — **10 passed**
- Playwright: `frontend/e2e/specs/trends/chart-ui-fix.spec.ts` — **1 passed**

## Changed files

- `frontend/src/features/trends/chart/adapters/resolveChartTokens.ts` (+test)
- `frontend/src/features/trends/chart/adapters/uplotAdapter.ts`
- `frontend/src/components/ds/TrendChartContainer.tsx`
- `frontend/src/components/ds/TagPicker.tsx` (+test)
- `frontend/src/features/trends/TrendsPage.tsx` (+test case)
- `frontend/e2e/specs/trends/chart-ui-fix.spec.ts`

## Handoff

- **Done:** stroke resolve + tagLabel from catalog + `SelectedTags` вне `TagPicker`
- **Scenario:** `frontend/e2e/specs/trends/chart-ui-fix.spec.ts`
- **code_changed:** yes
- **Next:** `FRONT QA` (новый чат) — targeted smoke trends; или `FRONT REFLECT` T-004
- **Tool:** Cursor + fast-editing
