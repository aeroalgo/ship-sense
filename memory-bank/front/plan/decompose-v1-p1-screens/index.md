# Реестр шагов (Decompose index)
**Plan ID:** v1-p1-screens
**План:** [plan-v1-p1-screens.md](../plan-v1-p1-screens.md)
**Implement index:** [implement-v1-p1-screens/index.md](../../implement/implement-v1-p1-screens/index.md)
**Дата:** 2026-07-26
**Режим:** FRONT DECOMPOSE
**Уровень:** L4 (T-004)

Каждый шаг — атомарная задача под один заход FRONT IMPLEMENT. Детали — в `sNN-*.yaml`. Интерфейсы — **lean** (без тел/полного TSX).

> **Трекер шагов:** только этот index (не дублировать чеклисты sNN в plan).

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность шагов, files/AC/TDD boundaries |
| `frontend-design` | композиция экранов (IMPL screens) |
| `design-taste-frontend` | промышленная эстетика, без SaaS-клише |
| `next-best-practices` | App Router, RSC/client boundaries |
| `frontend-patterns` | feature folders, hooks |
| `frontend-testing` | Vitest/RTL patterns |
| `playwright-best-practices` | E2E PW-01..10 (parent runs) |
| `tdd` | red→green на IMPLEMENT |
| `impeccable` | полировка spacing/типографика (CREATIVE/IMPL polish) |
| `high-end-visual-design` | signature Lamp / AggregateShipStatus |

**Per-step Design stack:** в каждом `sNN` — `visible_ui` + блок Design skills (канон 6 путей). IMPLEMENT читает список **из step**, не из этой таблицы. `visible_ui: no` → s01, s03–s05, s16.

## CREATIVE blockers (до IMPLEMENT зависимых шагов)

| ID | Шаги | Артефакт |
|----|------|----------|
| CR-UI-01 ✅ | s02 | `memory-bank/front/creative/v1-p1-screens/CR-UI-01-tokens.md` + `frontend/src/styles/tokens/**` (5×3 skins) — creative closed; s02 = providers/switchers |
| CR-UI-03 ✅ | s06 | `memory-bank/front/creative/v1-p1-screens/CR-UI-03-alarm-grammar.md` + `frontend/public/ds/lamps/*` + `lamp-grammar-spec.ts` — creative closed; s06 = Lamp/Storybook |
| CR-UI-02 ✅ | s11 | [CR-UI-02-chart-lib.md](../../creative/v1-p1-screens/CR-UI-02-chart-lib.md) + spike `frontend/src/features/trends/spike/` + `chart-lib-spec.ts` + `uplot` — creative closed; s11 = TrendChartContainer |
| CR-UI-04 ✅ | s13 | [CR-UI-04-watch-compression.md](../../creative/v1-p1-screens/CR-UI-04-watch-compression.md) + `frontend/src/lib/watch/watch-compression-spec.ts` — creative closed; s13 = WatchPage |
| CR-UI-05 ✅ | soft: s02/s09 final AC | [CR-UI-05-post-density.md](../../creative/v1-p1-screens/CR-UI-05-post-density.md) + `post-density-spec.ts` + token floor (Q9 waiver; photo AC open) |

**Рекомендуемый порядок CREATIVE:** CR-UI-01 → CR-UI-03 → CR-UI-02 → CR-UI-04 → CR-UI-05 (Q9).

**Параллельно с CREATIVE можно готовить IMPLEMENT:** s01, s03, s04, s05 (не зависят от creative).

**Жёсткий gate:** экраны s09–s13 **не** верстать до закрытия минимума DS0-4 в s06 (Lamp + StateShell + StatusBar primitives + Storybook scaffold).

## Очередь шагов

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **s01** | [s01-scaffold-app.md](s01-scaffold-app.md)<br>• Next.js 15 + Vitest + Playwright + env | [s01](../../implement/implement-v1-p1-screens/s01-scaffold-app.md) | no | yes | FRONT IMPLEMENT | done |
| **s02** | [s02-tokens-themes.md](s02-tokens-themes.md)<br>• Theme/Design providers + switchers (tokens CSS уже от CR-UI-01) | [s02](../../implement/implement-v1-p1-screens/s02-tokens-themes.md) | yes (done) | yes | FRONT IMPLEMENT | done |
| **s03** | [s03-quality-lib.md](s03-quality-lib.md)<br>• worst-of rollup + event priority sort | [s03](../../implement/implement-v1-p1-screens/s03-quality-lib.md) | no | yes | FRONT IMPLEMENT | done |
| **s04** | [s04-api-client.md](s04-api-client.md)<br>• OpenAPI types + REST wrappers + MSW fixtures | [s04](../../implement/implement-v1-p1-screens/s04-api-client.md) | no | yes | FRONT IMPLEMENT | done |
| **s05** | [s05-ws-manager.md](s05-ws-manager.md)<br>• WS subscribe/resume/reconnect + channel mux | [s05](../../implement/implement-v1-p1-screens/s05-ws-manager.md) | no | yes | FRONT IMPLEMENT | done |
| **s06** | [s06-ds-components.md](s06-ds-components.md)<br>• DS0-4: Lamp..PrintLayout + Storybook scaffold | [s06](../../implement/implement-v1-p1-screens/s06-ds-components.md) | yes (done) | yes | FRONT IMPLEMENT | done |
| **s07** | [s07-shell-statusbar.md](s07-shell-statusbar.md)<br>• App shell layout + StatusBar + nav + banners wire | [s07](../../implement/implement-v1-p1-screens/s07-shell-statusbar.md) | no | yes | FRONT IMPLEMENT | done |
| **s08** | [s08-session-tiles.md](s08-session-tiles.md)<br>• /login roster tiles + POST/DELETE session | [s08](../../implement/implement-v1-p1-screens/s08-session-tiles.md) | no | yes | FRONT IMPLEMENT | done |
| **s09** | [s09-screen-overview.md](s09-screen-overview.md)<br>• Screen 1 Overview + tree + WS values + stub drill | [s09](../../implement/implement-v1-p1-screens/s09-screen-overview.md) | no | yes | FRONT IMPLEMENT | done |
| **s10** | [s10-screen-journal.md](s10-screen-journal.md)<br>• Screen 5 filters + virtual list + print + deep link | [s10](../../implement/implement-v1-p1-screens/s10-screen-journal.md) | no | yes | FRONT IMPLEMENT | done |
| **s11** | [s11-chart-wrapper.md](s11-chart-wrapper.md)<br>• TrendChartContainer (uPlot / CR-UI-02) | [s11](../../implement/implement-v1-p1-screens/s11-chart-wrapper.md) | yes (done) | yes | FRONT IMPLEMENT | done |
| **s12** | [s12-screen-trends.md](s12-screen-trends.md)<br>• Screen 8 modes + deep link + markers + setpoints | [s12](../../implement/implement-v1-p1-screens/s12-screen-trends.md) | no | yes | FRONT IMPLEMENT | done |
| **s13** | [s13-screen-watch.md](s13-screen-watch.md)<br>• Screen 6 prototype sections + print | [s13](../../implement/implement-v1-p1-screens/s13-screen-watch.md) | yes (done) | yes | FRONT IMPLEMENT | done |
| **s14** | [s14-handoff-flow.md](s14-handoff-flow.md)<br>• Пересменочный UX 6→5/1 | [s14](../../implement/implement-v1-p1-screens/s14-handoff-flow.md) | no | yes | FRONT IMPLEMENT | done |
| **s15** | [s15-quality-global.md](s15-quality-global.md)<br>• Global stale desaturate + quarantine banners | [s15](../../implement/implement-v1-p1-screens/s15-quality-global.md) | no | yes | FRONT IMPLEMENT | done |
| **s16** | [s16-e2e-suite.md](s16-e2e-suite.md)<br>• Playwright PW-01..PW-10 | [s16](../../implement/implement-v1-p1-screens/s16-e2e-suite.md) | no | yes | FRONT IMPLEMENT | done |

Статусы: `pending` | `active` | `done` | `blocked` | `needs_creative`

## Summary-чеклист

- [x] s01 — Scaffold Next.js 15 + Vitest + Playwright + env
- [x] s02 — Theme/Design providers + switchers (CR-UI-01 tokens уже на диске)
- [x] s03 — Quality rollup + event priority sort
- [x] s04 — OpenAPI types + REST client + MSW
- [x] s05 — WS manager subscribe/resume/reconnect
- [x] s06 — DS0-4 components + Storybook (CR-UI-03 Lamp)
- [x] s07 — App shell + StatusBar + nav
- [x] s08 — Session tiles B11 login/logout
- [x] s09 — Screen 1 Overview
- [x] s10 — Screen 5 Journal
- [x] s11 — TrendChartContainer (CR-UI-02)
- [x] s12 — Screen 8 Trends
- [x] s13 — Screen 6 Watch prototype (CR-UI-04)
- [x] s14 — Handoff flow 6→5/1
- [x] s15 — Global stale/quarantine behavior
- [x] s16 — Playwright PW-01..PW-10

## Handoff

- **Done:** FRONT DECOMPOSE T-004 — 16 шагов; s01–s16 IMPLEMENT done; CR-UI-01/02/03/04/05 closed
- **Files:** `memory-bank/front/plan/decompose-v1-p1-screens/`; creative `CR-UI-01`…`CR-UI-05-post-density.md`
- **Next:** `FRONT REFLECT` T-004 (QA PASS); soft photo Q9 follow-up
- **load_now:** см. `activeContext.md`
- **Tool / model:** Cursor + fast-editing
- **New chat:** yes — one chat = one atomic subtask
