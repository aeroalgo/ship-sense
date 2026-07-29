# Spike CR-UI-02 — uPlot

Reference for FRONT IMPLEMENT s11. Not wired to TrendsPage.

## Decision

- Lib: **uPlot** (`CHART_LIB` in `src/lib/trends/chart-lib-spec.ts`)
- Gaps: `seriesToUplotAligned` → `null` (never `0`)
- Overlays: `draw-overlays.ts` (setpoints + severity shapes)

## Files

| File | Role |
|------|------|
| `fixture-90d.ts` | 90d synthetic series + gaps + setpoints + markers |
| `gaps.ts` | SeriesPoint → uPlot aligned + AC-8-05 assert |
| `draw-overlays.ts` | canvas overlay contract for s11 adapter hooks |
| `bench-notes.md` | perf gate procedure |

## Smoke (Node)

```bash
cd frontend
npx tsx -e "
import { buildSpikeFixture, downsampleForDisplay } from './src/features/trends/spike/fixture-90d.ts';
import { seriesToUplotAligned, assertNoZeroFilledGaps } from './src/features/trends/spike/gaps.ts';
const f = buildSpikeFixture({ days: 90, stepMinutes: 10 });
const display = downsampleForDisplay(f.series, 10000);
const aligned = seriesToUplotAligned(display);
assertNoZeroFilledGaps(display, aligned.ys);
console.log({ raw: f.meta.pointCount, display: display.length, gaps: aligned.gapIndexes.length });
"
```

## s11 port

1. Move/adapt `gaps.ts` + overlay draw into `features/trends/chart/adapters/uplotAdapter.ts`
2. Wrap with `TrendChartContainer` + DS chrome (testid `trend-chart`)
3. Vitest: null bucket gap; setpoint count; keep this folder as reference
