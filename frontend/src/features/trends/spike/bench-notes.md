# Bench notes — CR-UI-02 / uPlot

## Gate (plan §7.5)

| Metric | Target |
|--------|--------|
| Initial chart render | &lt;500 ms @ 10k points |
| Zoom refetch | &lt;300 ms perceived |
| WS tail update | &lt;16 ms frame |

## Laptop smoke (creative)

1. Build fixture 90d @ 10 min → downsample to ≤10k (`downsampleForDisplay`).
2. `seriesToUplotAligned` + `assertNoZeroFilledGaps`.
3. On s11: mount uPlot with aligned data; measure `performance.now()` around first `new uPlot(...)`.
4. On post hardware: repeat; if &gt;500 ms — reduce softCap / increase API bucket, do not switch lib without new CREATIVE.

## Setpoints / markers demo

Spike provides 4 setpoint bands (HH/H/L/LL) + 3 markers. s11 hooks `drawSetpointBands` / `drawEventMarkers` inside uPlot `hooks.draw`.

## Forbidden

- Zero-fill gaps
- Default Grafana/ECharts theme chrome
- Import `echarts` in s11
