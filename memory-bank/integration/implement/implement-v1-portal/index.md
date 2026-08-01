# Implement index (INTEG epic hub)
**Plan ID:** v1-portal
**Дата:** 2026-08-01
**Режим:** INTEG IMPLEMENT

**Plan:** [plan-v1-portal.md](../../plan/plan-v1-portal.md)
**Decompose:** [decompose-v1-portal/index.md](../../plan/decompose-v1-portal/index.md)

Каждый шаг = один заход `INTEG IMPLEMENT`. Имена файлов = decompose: `eNN-<slug>.yaml`.

> **Inventory / GAP CLOSE:** грузить **этот index** → ходить **только по ссылкам** таблицы. **ЗАПРЕЩЕНО** глобить весь flat `integration/implement/*`.
> **Policy:** статусы живут только в `implement/eNN-*.yaml` и `decompose/index.md`. Этот файл — navigation hub, без status-колонки.

## Реестр шагов (decompose ↔ implement)

| step | decompose | implement |
| :--- | :--- | :--- |
| **e01** | [e01-home-redirect.yaml](../../plan/decompose-v1-portal/e01-home-redirect.yaml) | [e01-home-redirect.yaml](e01-home-redirect.yaml) |
| **e02** | [e02-login-roster-tiles.yaml](../../plan/decompose-v1-portal/e02-login-roster-tiles.yaml) | [e02-login-roster-tiles.yaml](e02-login-roster-tiles.yaml) |
| **e03** | [e03-session-create-logout.yaml](../../plan/decompose-v1-portal/e03-session-create-logout.yaml) | [e03-session-create-logout.yaml](e03-session-create-logout.yaml) |
| **e04** | [e04-appshell-chrome.yaml](../../plan/decompose-v1-portal/e04-appshell-chrome.yaml) | [e04-appshell-chrome.yaml](e04-appshell-chrome.yaml) |
| **e05** | [e05-statusbar-alarms.yaml](../../plan/decompose-v1-portal/e05-statusbar-alarms.yaml) | [e05-statusbar-alarms.yaml](e05-statusbar-alarms.yaml) |
| **e06** | [e06-freshness-quarantine.yaml](../../plan/decompose-v1-portal/e06-freshness-quarantine.yaml) | [e06-freshness-quarantine.yaml](e06-freshness-quarantine.yaml) |
| **e07** | [e07-ws-stream-fanout.yaml](../../plan/decompose-v1-portal/e07-ws-stream-fanout.yaml) | [e07-ws-stream-fanout.yaml](e07-ws-stream-fanout.yaml) |
| **e08** | [e08-overview-assets-tree.yaml](../../plan/decompose-v1-portal/e08-overview-assets-tree.yaml) | [e08-overview-assets-tree.yaml](e08-overview-assets-tree.yaml) |
| **e09** | [e09-overview-mosection-lamps.yaml](../../plan/decompose-v1-portal/e09-overview-mosection-lamps.yaml) | [e09-overview-mosection-lamps.yaml](e09-overview-mosection-lamps.yaml) |
| **e10** | [e10-overview-drilldown-stub.yaml](../../plan/decompose-v1-portal/e10-overview-drilldown-stub.yaml) | [e10-overview-drilldown-stub.yaml](e10-overview-drilldown-stub.yaml) |
| **e11** | [e11-journal-filters-list.yaml](../../plan/decompose-v1-portal/e11-journal-filters-list.yaml) | [e11-journal-filters-list.yaml](e11-journal-filters-list.yaml) |
| **e12** | [e12-reconstruction-banner.yaml](../../plan/decompose-v1-portal/e12-reconstruction-banner.yaml) | [e12-reconstruction-banner.yaml](e12-reconstruction-banner.yaml) |
| **e13** | [e13-journal-session-filter.yaml](../../plan/decompose-v1-portal/e13-journal-session-filter.yaml) | [e13-journal-session-filter.yaml](e13-journal-session-filter.yaml) |
| **e14** | [e14-journal-realtime-append.yaml](../../plan/decompose-v1-portal/e14-journal-realtime-append.yaml) | [e14-journal-realtime-append.yaml](e14-journal-realtime-append.yaml) |
| **e15** | [e15-trends-tagpicker.yaml](../../plan/decompose-v1-portal/e15-trends-tagpicker.yaml) | [e15-trends-tagpicker.yaml](e15-trends-tagpicker.yaml) |
| **e16** | [e16-trends-series-chart.yaml](../../plan/decompose-v1-portal/e16-trends-series-chart.yaml) | [e16-trends-series-chart.yaml](e16-trends-series-chart.yaml) |
| **e17** | [e17-trends-setpoints-overlay.yaml](../../plan/decompose-v1-portal/e17-trends-setpoints-overlay.yaml) | [e17-trends-setpoints-overlay.yaml](e17-trends-setpoints-overlay.yaml) |
| **e18** | [e18-trends-event-markers.yaml](../../plan/decompose-v1-portal/e18-trends-event-markers.yaml) | [e18-trends-event-markers.yaml](e18-trends-event-markers.yaml) |
| **e19** | [e19-trends-realtime-patch.yaml](../../plan/decompose-v1-portal/e19-trends-realtime-patch.yaml) | [e19-trends-realtime-patch.yaml](e19-trends-realtime-patch.yaml) |
| **e20** | [e20-watch-report-body.yaml](../../plan/decompose-v1-portal/e20-watch-report-body.yaml) | [e20-watch-report-body.yaml](e20-watch-report-body.yaml) |
| **e21** | [e21-watch-verdict-debounce.yaml](../../plan/decompose-v1-portal/e21-watch-verdict-debounce.yaml) | [e21-watch-verdict-debounce.yaml](e21-watch-verdict-debounce.yaml) |
| **e22** | [e22-watch-dataquality-panel.yaml](../../plan/decompose-v1-portal/e22-watch-dataquality-panel.yaml) | [e22-watch-dataquality-panel.yaml](e22-watch-dataquality-panel.yaml) |
| **e23** | [e23-watch-handoff-buttons.yaml](../../plan/decompose-v1-portal/e23-watch-handoff-buttons.yaml) | [e23-watch-handoff-buttons.yaml](e23-watch-handoff-buttons.yaml) |
| **e24** | [e24-reports-hub.yaml](../../plan/decompose-v1-portal/e24-reports-hub.yaml) | [e24-reports-hub.yaml](e24-reports-hub.yaml) |
| **e25** | [e25-watch-schedule.yaml](../../plan/decompose-v1-portal/e25-watch-schedule.yaml) | [e25-watch-schedule.yaml](e25-watch-schedule.yaml) |
| **e26** | [e26-warnings-surface.yaml](../../plan/decompose-v1-portal/e26-warnings-surface.yaml) | [e26-warnings-surface.yaml](e26-warnings-surface.yaml) |
| **e27** | [e27-vessel-state.yaml](../../plan/decompose-v1-portal/e27-vessel-state.yaml) | [e27-vessel-state.yaml](e27-vessel-state.yaml) |
| **e28** | [e28-admin-ops.yaml](../../plan/decompose-v1-portal/e28-admin-ops.yaml) | [e28-admin-ops.yaml](e28-admin-ops.yaml) |
| **e29** | [e29-dev-appearance.yaml](../../plan/decompose-v1-portal/e29-dev-appearance.yaml) | [e29-dev-appearance.yaml](e29-dev-appearance.yaml) |
| **e30** | [e30-guides-na.yaml](../../plan/decompose-v1-portal/e30-guides-na.yaml) | [e30-guides-na.yaml](e30-guides-na.yaml) |

## Handoff

- **Next:** `INTEG IMPLEMENT e05`
- **load_now:** `integration/plan/decompose-v1-portal/e05-statusbar-alarms.yaml` (не этот index при wire)
- **Progress:** e01–e04 completed
- **Decompose tracker:** [decompose index](../../plan/decompose-v1-portal/index.md)
