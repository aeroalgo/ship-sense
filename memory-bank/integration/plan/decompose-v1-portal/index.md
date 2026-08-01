# Реестр шагов (INTEG DECOMPOSE — element-first)
**Plan ID:** v1-portal
**План:** [plan-v1-portal.md](../plan-v1-portal.md)
**Implement index:** [implement-v1-portal/index.md](../../implement/implement-v1-portal/index.md)
**Дата:** 2026-08-01
**Режим:** INTEG DECOMPOSE
**Scope:** portal

Каждый шаг = **один UI-элемент или раздел страницы**. Контракт API — **lean** в `eNN-*.yaml` §Contract (keys/path/shape словами, без готового кода). Не читать `integration/gap/`, `integration/contracts/`.

**Трекер status eNN:** только `decompose/index.md` + `implement/eNN-*.yaml`. `implement-v1-portal/index.md` — navigation hub без status. В `plan-INTEG-*.md` не дублировать чеклист статусов.

Шаблон шага: [epic-step.yaml](epic-step.yaml)  
Шаблон implement hub: [.cursor/templates/implement/index.md](../../../implement/index.md)

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | структура шагов / атомарность |
| `query-builder` | list/filter endpoints в элементе |

## Очередь элементов

| step_id | title & element | implement | route | API | tdd | next_phase | status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **e01** | [e01-home-redirect.yaml](e01-home-redirect.yaml)<br>• redirect `/` → `/login` | [e01…](../../implement/implement-v1-portal/e01-home-redirect.yaml) | `/` | none | no | INTEG IMPLEMENT | completed |
| **e02** | [e02-login-roster-tiles.yaml](e02-login-roster-tiles.yaml)<br>• `LoginTile` roster from `/api/watch/roster` | [e02…](../../implement/implement-v1-portal/e02-login-roster-tiles.yaml) | `/login` | GET /api/watch/roster | yes | INTEG IMPLEMENT | completed |
| **e03** | [e03-session-create-logout.yaml](e03-session-create-logout.yaml)<br>• POST/DELETE `/api/session` + cookie | [e03…](../../implement/implement-v1-portal/e03-session-create-logout.yaml) | `/login` | POST/DELETE /api/session | yes | INTEG IMPLEMENT | completed |
| **e04** | [e04-appshell-chrome.yaml](e04-appshell-chrome.yaml)<br>• `AppShell` + `AppNav` + `SessionChip` | [e04…](../../implement/implement-v1-portal/e04-appshell-chrome.yaml) | `(auth)/*` | DELETE /api/session | no | INTEG IMPLEMENT | completed |
| **e05** | [e05-statusbar-alarms.yaml](e05-statusbar-alarms.yaml)<br>• `StatusBar` alarms + WS | [e05…](../../implement/implement-v1-portal/e05-statusbar-alarms.yaml) | `(auth)/*` | GET /api/events + WS | yes | INTEG IMPLEMENT | completed |
| **e06** | [e06-freshness-quarantine.yaml](e06-freshness-quarantine.yaml)<br>• `FreshnessController` + banners | [e06…](../../implement/implement-v1-portal/e06-freshness-quarantine.yaml) | `(auth)/*` | GET /api/sources/status | yes | INTEG IMPLEMENT | pending |
| **e07** | [e07-ws-stream-fanout.yaml](e07-ws-stream-fanout.yaml)<br>• `WsManager` / `useWsChannel` | [e07…](../../implement/implement-v1-portal/e07-ws-stream-fanout.yaml) | `(auth)/*` | WS /api/stream | yes | INTEG IMPLEMENT | pending |
| **e08** | [e08-overview-assets-tree.yaml](e08-overview-assets-tree.yaml)<br>• `AggregateShipStatus` + tree cards | [e08…](../../implement/implement-v1-portal/e08-overview-assets-tree.yaml) | `/overview` | GET /api/assets/tree | yes | INTEG IMPLEMENT | pending |
| **e09** | [e09-overview-mosection-lamps.yaml](e09-overview-mosection-lamps.yaml)<br>• `MoSection` lamps from tree | [e09…](../../implement/implement-v1-portal/e09-overview-mosection-lamps.yaml) | `/overview` | derived from tree | no | INTEG IMPLEMENT | pending |
| **e10** | [e10-overview-drilldown-stub.yaml](e10-overview-drilldown-stub.yaml)<br>• `DrillDownStubModal` (mnemo P1) | [e10…](../../implement/implement-v1-portal/e10-overview-drilldown-stub.yaml) | `/overview` | GET /api/mnemo/* (BACK only) | no | INTEG IMPLEMENT | pending |
| **e11** | [e11-journal-filters-list.yaml](e11-journal-filters-list.yaml)<br>• `EventFilters` + infinite list | [e11…](../../implement/implement-v1-portal/e11-journal-filters-list.yaml) | `/journal` | GET /api/events | yes | INTEG IMPLEMENT | pending |
| **e12** | [e12-reconstruction-banner.yaml](e12-reconstruction-banner.yaml)<br>• `ReconstructionBanner` from header | [e12…](../../implement/implement-v1-portal/e12-reconstruction-banner.yaml) | `/journal` | header on events | no | INTEG IMPLEMENT | pending |
| **e13** | [e13-journal-session-filter.yaml](e13-journal-session-filter.yaml)<br>• `SessionEventFilter` source=session | [e13…](../../implement/implement-v1-portal/e13-journal-session-filter.yaml) | `/journal` | GET /api/events?source=session | no | INTEG IMPLEMENT | pending |
| **e14** | [e14-journal-realtime-append.yaml](e14-journal-realtime-append.yaml)<br>• `useEventsRealtime` WS append | [e14…](../../implement/implement-v1-portal/e14-journal-realtime-append.yaml) | `/journal` | WS events (e07) | no | INTEG IMPLEMENT | pending |
| **e15** | [e15-trends-tagpicker.yaml](e15-trends-tagpicker.yaml)<br>• `TagPicker` from tree | [e15…](../../implement/implement-v1-portal/e15-trends-tagpicker.yaml) | `/trends` | GET /api/assets/tree | yes | INTEG IMPLEMENT | pending |
| **e16** | [e16-trends-series-chart.yaml](e16-trends-series-chart.yaml)<br>• `TrendChartContainer` + series | [e16…](../../implement/implement-v1-portal/e16-trends-series-chart.yaml) | `/trends` | GET /api/series + aggregate | yes | INTEG IMPLEMENT | pending |
| **e17** | [e17-trends-setpoints-overlay.yaml](e17-trends-setpoints-overlay.yaml)<br>• `useSetpoints` overlay | [e17…](../../implement/implement-v1-portal/e17-trends-setpoints-overlay.yaml) | `/trends` | GET /api/setpoints | yes | INTEG IMPLEMENT | pending |
| **e18** | [e18-trends-event-markers.yaml](e18-trends-event-markers.yaml)<br>• `useEventMarkers` + deep-link | [e18…](../../implement/implement-v1-portal/e18-trends-event-markers.yaml) | `/trends` | GET /api/events | no | INTEG IMPLEMENT | pending |
| **e19** | [e19-trends-realtime-patch.yaml](e19-trends-realtime-patch.yaml)<br>• `useTrendRealtime` WS patch | [e19…](../../implement/implement-v1-portal/e19-trends-realtime-patch.yaml) | `/trends` | WS values (e07) | no | INTEG IMPLEMENT | pending |
| **e20** | [e20-watch-report-body.yaml](e20-watch-report-body.yaml)<br>• `useWatchReport` + sections | [e20…](../../implement/implement-v1-portal/e20-watch-report-body.yaml) | `/watch` | GET /api/reports/watch | yes | INTEG IMPLEMENT | pending |
| **e21** | [e21-watch-verdict-debounce.yaml](e21-watch-verdict-debounce.yaml)<br>• `WatchVerdict` + `DebounceGroupRow` | [e21…](../../implement/implement-v1-portal/e21-watch-verdict-debounce.yaml) | `/watch` | from report body | no | INTEG IMPLEMENT | pending |
| **e22** | [e22-watch-dataquality-panel.yaml](e22-watch-dataquality-panel.yaml)<br>• `DataQualityPanel` | [e22…](../../implement/implement-v1-portal/e22-watch-dataquality-panel.yaml) | `/watch` | from report body | no | INTEG IMPLEMENT | pending |
| **e23** | [e23-watch-handoff-buttons.yaml](e23-watch-handoff-buttons.yaml)<br>• `HandoffButton` to journal | [e23…](../../implement/implement-v1-portal/e23-watch-handoff-buttons.yaml) | `/watch` | client routing only | no | INTEG IMPLEMENT | pending |
| **e24** | [e24-reports-hub.yaml](e24-reports-hub.yaml)<br>• Reports hub (P1, phase 2) | [e24…](../../implement/implement-v1-portal/e24-reports-hub.yaml) | future | GET /api/reports/* (partial) | no | INTEG IMPLEMENT | pending |
| **e25** | [e25-watch-schedule.yaml](e25-watch-schedule.yaml)<br>• Watch schedule defaults (P1) | [e25…](../../implement/implement-v1-portal/e25-watch-schedule.yaml) | future | GET /api/watch/schedule | no | INTEG IMPLEMENT | pending |
| **e26** | [e26-warnings-surface.yaml](e26-warnings-surface.yaml)<br>• Warnings / B13 strip (P1) | [e26…](../../implement/implement-v1-portal/e26-warnings-surface.yaml) | future | GET /api/warnings* | no | INTEG IMPLEMENT | pending |
| **e27** | [e27-vessel-state.yaml](e27-vessel-state.yaml)<br>• Vessel mode chip (P1) | [e27…](../../implement/implement-v1-portal/e27-vessel-state.yaml) | future | GET /api/vessel/state | no | INTEG IMPLEMENT | pending |
| **e28** | [e28-admin-ops.yaml](e28-admin-ops.yaml)<br>• Admin storage/OTA/audit (P2) | [e28…](../../implement/implement-v1-portal/e28-admin-ops.yaml) | future | GET /api/admin/* | no | INTEG IMPLEMENT | pending |
| **e29** | [e29-dev-appearance.yaml](e29-dev-appearance.yaml)<br>• `/dev/appearance` theme controls | [e29…](../../implement/implement-v1-portal/e29-dev-appearance.yaml) | `/dev/appearance` | none | no | INTEG IMPLEMENT | pending |
| **e30** | [e30-guides-na.yaml](e30-guides-na.yaml)<br>• Guides (explicit n/a) | [e30…](../../implement/implement-v1-portal/e30-guides-na.yaml) | n/a | n/a | no | INTEG IMPLEMENT | pending |

Статусы: `pending` | `active` | `done` | `blocked`

## Summary-чеклист

- [x] e01 — Home redirect `/`
- [x] e02 — Login roster tiles
- [x] e03 — Session create / logout
- [x] e04 — AppShell chrome
- [x] e05 — StatusBar alarms
- [ ] e06 — Freshness + quarantine
- [ ] e07 — WS stream fanout
- [ ] e08 — Overview assets tree
- [ ] e09 — Overview MoSection lamps
- [ ] e10 — Overview drill-down stub
- [ ] e11 — Journal filters + list
- [ ] e12 — Reconstruction banner
- [ ] e13 — Journal session filter
- [ ] e14 — Journal realtime append
- [ ] e15 — Trends TagPicker
- [ ] e16 — Trends series chart
- [ ] e17 — Trends setpoints overlay
- [ ] e18 — Trends event markers
- [ ] e19 — Trends realtime patch
- [ ] e20 — Watch report body
- [ ] e21 — Watch verdict + debounce
- [ ] e22 — Watch DataQualityPanel
- [ ] e23 — Watch handoff buttons
- [ ] e24 — Reports hub (P1)
- [ ] e25 — Watch schedule (P1)
- [ ] e26 — Warnings surface (P1)
- [ ] e27 — Vessel state (P1)
- [ ] e28 — Admin ops (P2)
- [ ] e29 — Dev appearance
- [ ] e30 — Guides (n/a)

## Handoff

- **Next:** `INTEG IMPLEMENT e06` — Freshness + quarantine
- **load_now:** `integration/plan/decompose-v1-portal/e06-freshness-quarantine.yaml`
- **Progress:** e01–e05 completed · e06–e30 pending
- **Implement hub:** [implement-v1-portal/index.md](../../implement/implement-v1-portal/index.md)
