# CR-UI-02 — Chart library (TrendChartContainer)

**Тип:** Architecture + Algorithm + UI-UX  
**Задача:** T-004 / plan `plan-v1-p1-screens.md` §5.3, §7, §10 CR-UI-02  
**Decompose:** [s11-chart-wrapper.md](../plan/decompose-v1-p1-screens/s11-chart-wrapper.md)  
**Deps tokens:** [CR-UI-01-tokens.md](CR-UI-01-tokens.md)  
**Deps alarm shapes:** [CR-UI-03-alarm-grammar.md](CR-UI-03-alarm-grammar.md) (marker silhouettes)  
**Дата:** 2026-07-26  
**Статус:** closed (creative) — IMPLEMENT s11 собирает `TrendChartContainer` + adapter

---

## 0. Design Read

Reading this as: **ship-bridge HMI trend strip (ISA-101 / paper chart under glass)** for watch officers at 2–3 m — dense time-series with gaps, setpoints, event markers; **not** SaaS analytics, **not** bare Grafana chrome.

**Dial overrides (HMI):** VARIANCE 2 · MOTION 1–2 · DENSITY 9 (cockpit chart).

**Skills applied:** `frontend-design` (subject = strip chart / engineering plot), `design-taste-frontend` (regulated/cockpit dials; marketing patterns out of scope), `emil-design-eng` (no decorative chart entrance; zoom feedback ≤300 ms), `impeccable` product register (contrast, reduced-motion, no layout anim on plot), `high-end-visual-design` — **trimmed**: signature = branded plot chrome + gap honesty, not glass/bento, `ui-ux-pro-max` chart domain (line + anomaly markers; canvas ≥1k pts), `frontend-patterns` (adapter leaf + thin React wrapper), `brainstorming` (A/B/C below).

---

## 1. Проблема и scope

### 1.1 Вопрос плана

> uPlot vs ECharts for TrendChartContainer?  
> AC: 90d chart interactive on dev laptop; setpoints + markers demo.

### 1.2 Decision gate (plan §7.1)

Benchmark mental model: **1 tag × 90d @ 1m** ≈ до ~129 600 сырых минут; на UI после API `resolution=auto` — целевой display budget **≤10k points** interactive (plan §7.5). На post hardware: initial render **&lt;500 ms @ 10k**, zoom refetch perceived **&lt;300 ms**, WS tail **&lt;16 ms** frame.

### 1.3 Deliverables этого CREATIVE

| # | Путь | Статус |
|---|------|--------|
| 1 | `memory-bank/front/creative/CR-UI-02-chart-lib.md` (этот файл) | done |
| 2 | `frontend/src/lib/trends/chart-lib-spec.ts` | done |
| 3 | `frontend/src/features/trends/spike/*` (fixture + overlays + bench notes) | done |
| 4 | dep `uplot` в `frontend/package.json` | done |

### 1.4 Out of scope

| Не делаем здесь | Куда |
|-----------------|------|
| React `TrendChartContainer` + Vitest fixture tests | FRONT IMPLEMENT s11 |
| TrendsPage / modes / deep link / Live toggle | FRONT IMPLEMENT s12 |
| API downsample server | BACK (series) |
| Grafana iframe / embed | **запрет** AC-8-06 / ТЗ |
| Финальный type scale постов | CR-UI-05 / Q9 |

---

## 2. Architecture — 3 варианта + recommendation

### Вариант A — uPlot + thin adapter + DS chrome (рекомендуется)

**Стек:**

```
TrendChartContainer (React, DS shell)
  └─ adapters/uplotAdapter.ts
       ├─ series → uPlot data (null = gap)
       ├─ hooks.draw → setpoints + markers
       └─ setScale / select → onRangeChange
```

**Плюсы:**

- Bundle ~45 KB; canvas path; известный профиль для 10k+ pts.
- Явные `null` gaps без «заливания» нулём (AC-8-05).
- Полный контроль chrome: оси/сетка/легенда = CSS tokens CR-UI-01, не тема Grafana/ECharts.
- Markers = draw hooks + SVG shapes CR-UI-03 (shape-first).
- WS append: `u.setData` / partial update укладывается в 16 ms budget при ограниченном tail.

**Минусы:**

- Zoom/brush UI пишем сами (не «из коробки»).
- Setpoint/marker API — наш код в adapter (не markLine).

### Вариант B — Apache ECharts

**Плюсы:** `markLine` / `markPoint`, dataZoom, rich tooltip «из коробки».  
**Минусы:** тяжёлый bundle + default chrome/анимации бьют HMI- densити и AC-8-06 («не Grafana» → всё равно кастом-тема); default connect-nulls нужно жёстко выключать; WS/realtime хуже предсказуем по frame budget; сложнее гарантировать «break line not zero» без дисциплины series-null.

### Вариант C — Dual (uPlot quick + ECharts extended)

**Плюсы:** «лучшее из двух» по фичам.  
**Минусы:** два adapter, два skin, два perf-профиля; FAIL maintainability для фазы 1; s11/s12 раздуваются.

### Recommendation

**Вариант A — uPlot.**  
Обоснование: plan §7.5 + AC-8-04/05/06 приоритетнее rich markLine. Setpoints/markers и так кастом под DS0; ECharts не снимает работу по брендингу, только добавляет вес. Dual — out for p1.

**Зафиксировано:** npm `uplot`; adapter path `frontend/src/features/trends/chart/adapters/uplotAdapter.ts` (создаёт s11).

---

## 3. Algorithm — display rules (канон для s11)

Источник: plan §7.2–7.4. Код-контракт: `chart-lib-spec.ts`.

### 3.1 Series → plot path

| Condition | Render |
|-----------|--------|
| `quality=good`, value≠null, samples&gt;0 | линия на `value`; extended mode — тонкий envelope `min`–`max` |
| `value=null` OR samples=0 | **gap** — `null` в uPlot data; **запрет** interpolate / zero-fill |
| `quality=bad` | gap + optional tick (draw) |
| `quality=quarantine` | dotted segment или hollow point (draw overlay) |
| `quality=stale` на правом краю | freeze + вертикальный dashed live-edge |

### 3.2 Setpoints

- Горизонтальные step-сегменты из `GET /api/setpoints/history` (и/или static bands).
- Цвет: muted `--alarm-warning-fg` / `--alarm-critical-fg` (не neon).
- Подпись у правой оси (label HH/HLL).

### 3.3 Event markers

- Силуэт severity на time axis (reuse CR-UI-03 shapes / ids).
- Hover: `event_name` + `ts`.
- Click: callback → journal deep link (s12) или popover.

### 3.4 Modes

| mode | Поведение |
|------|-----------|
| `quick` | WS tail append OK; densнее update |
| `extended` | без WS tail по умолчанию; envelope min–max; zoom → `onRangeChange` → refetch |

### 3.5 Resolution UX

- Client: `resolution=auto`.
- Legend badge: «агрегация {resolution}» (RU).
- Zoom-in → parent refetch finer window (progressive); chart показывает skeleton overlay (&lt;300 ms perceived).

---

## 4. UI-UX — chrome (не Grafana)

### Вариант UI-A — Bridge strip under glass (рекомендуется)

```
┌─ trend-chart (data-testid) ─────────────────────────────────┐
│ [tag]  unit   │  badge: агрегация 1 мин  │ quality pill     │
├─────────────────────────────────────────────────────────────┤
│ ░ plot canvas (uPlot) — grid hairlines from --border-*      │
│   ── series (token accent)                                  │
│   ··· quarantine                                            │
│   ══ setpoint HH (muted amber)                              │
│   ▲ markers (severity shapes)                                │
├─────────────────────────────────────────────────────────────┤
│ brush / zoom affordance (hairline) · Live off|on (extended) │
└─────────────────────────────────────────────────────────────┘
```

**Tokens only:** `--surface-0/1`, `--text-primary/muted`, `--border-*`, semantic alarm/quality.  
**Запрет:** default ECharts/Grafana dark blue grid, purple accents, neon glows, card-in-card.  
**Signature:** честный gap (разрыв линии = нет данных) + setpoint step + shaped markers.

### Вариант UI-B — Minimal naked canvas

Только canvas без legend/badge.  
**Минусы:** AC-8-06 / resolution badge / a11y summary слабее. Reject для продукта; допустим только внутри unit-теста.

### Recommendation UI

**UI-A.** Shell = DS (`StateShell`/local chrome), plot = uPlot leaf.

### Motion

- Нет entrance-анимации серии.
- Zoom/refetch: opacity skeleton 150–250 ms `ease-out`; `prefers-reduced-motion` → instant swap.
- Marker hover: tooltip 125–200 ms; без bounce.

### A11y

- `data-testid="trend-chart"`.
- `aria-label` / sr-summary: tag, range, point count, gap count, setpoint count, marker count.
- Tooltip/marker hit ≥44 CSS px на touch; keyboard: focusable marker list fallback (s12 может усилить).
- Color not only: series style + marker **shape**.

---

## 5. Spike (reference)

Путь: `frontend/src/features/trends/spike/`

| Файл | Назначение |
|------|------------|
| `fixture-90d.ts` | синтетика 90d / gaps / setpoints / markers |
| `gaps.ts` | `SeriesPoint[]` → uPlot `null` gaps (pure) |
| `draw-overlays.ts` | контракт draw setpoints + markers (stub hooks API) |
| `bench-notes.md` | как прогнать perf gate на laptop / post |
| `README.md` | как открыть / что переносится в s11 |

**Spec:** `frontend/src/lib/trends/chart-lib-spec.ts` — `CHART_LIB`, props contract, testids, render rules enum.

**Perf gate (creative closed если):**

1. Fixture ≥10k pts строится &lt;50 ms (CPU transform).
2. Документировано: uPlot setData 10k на dev laptop целевой &lt;500 ms (verify s11 на железе поста).
3. Gaps: consecutive null → visual break (assert в s11 Vitest).

---

## 6. Implementation guide (для s11)

1. `npm` уже: `uplot` — не менять major без нового CREATIVE.
2. Создать `TrendChartContainer.tsx` + `adapters/uplotAdapter.ts`.
3. Props = `TrendChartProps` из `chart-lib-spec.ts` (синхрон с plan §7.1).
4. TDD (decompose s11):
   - null bucket → gap (no zero)
   - setpoints render count
   - integration fixture §9.4 #5
5. Chrome: CSS Modules / tokens; **не** импортировать echarts.
6. Не монтировать TrendsPage (s12).
7. Spike оставить как reference (не удалять).

### Package

```json
"uplot": "^1.6.x"
```

### Adapter signature (lean)

```typescript
createUplotAdapter(el: HTMLElement, opts: {
  series: SeriesPoint[];
  setpoints: SetpointBand[];
  markers: EventMarker[];
  mode: 'quick' | 'extended';
  onRangeChange: (from: string, to: string) => void;
  onMarkerClick?: (id: string) => void;
  tokens: ChartTokenSnapshot;
}): { destroy(): void; setSeries(s: SeriesPoint[]): void };
```

---

## 7. Verification checklist

- [x] ≥2 lib variants + recommended (uPlot)
- [x] ≥2 UI chrome variants + recommended (Bridge strip)
- [x] Display rules gaps/setpoints/markers documented
- [x] Tokens / signature / testid documented
- [x] Spike + `chart-lib-spec.ts` + `uplot` dep
- [x] Decompose s11 rewire → closed + IMPLEMENT
- [x] AC-8-06 path: branded chrome, not Grafana

---

## Handoff

- **Done:** FRONT CREATIVE CR-UI-02 — uPlot выбран; spike + spec + dep; s11 unblocked
- **Files:** `memory-bank/front/creative/CR-UI-02-chart-lib.md`; `frontend/src/lib/trends/chart-lib-spec.ts`; `frontend/src/features/trends/spike/*`; `frontend/package.json` (`uplot`)
- **Next:** `FRONT IMPLEMENT` s11 (`decompose-v1-p1-screens/s11-chart-wrapper.md`) — новый чат; параллельно можно s12 stub без chart
- **Tool / model:** Cursor + fast-editing (s11 TDD); premium если canvas flaky в jsdom
- **New chat:** yes — one chat = one atomic subtask
