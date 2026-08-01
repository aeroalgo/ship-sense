# plan-INTEG-v1-portal

**Дата:** 2026-08-01  
**Режим:** INTEG PLAN  
**Scope:** portal  
**Домен/slug:** v1-portal (ShipSense edge crew UI ↔ FastAPI `/api`)  
**Статус:** active  
**Gap ref (опционально):** нет (PLAN независим от GAP; при дрейфе контракта после DECOMPOSE — `INTEG GAP`)

→ [decompose-v1-portal/index.md](decompose-v1-portal/index.md) — **после DECOMPOSE:** единственный трекер status `eNN` (не дублировать `- [ ] e01…` в этом plan)

## Суть

Master-план wire **всего portal экипажа** ShipSense: каждый route App Router, UI-элемент экрана, REST/WS вызов к API и привязка к данным edge (Timescale / events / ship-pack). Движение — **по UI-элементам**, не по слоям «сначала все endpoints / потом весь front».

**As-built вход:**
- BACK: `implement-v1-p1-api` (T-003, s01–s10 done + REFLECT) + `implement-v1-p2-ship` (T-005, s01–s20 implement done; QA suite currently blocked на fixture issues — wire не блокируется документально, но live E2E зависит от green API).
- FRONT: `implement-v1-p1-screens` (T-004, s01–s16 done).
- Код: `apps/api/app/api/v1/**`, `frontend/src/app/**`, `frontend/src/features/**`, `frontend/src/lib/api/**`, `frontend/src/lib/ws/**`, MSW `frontend/src/test/msw/**`.

**Продуктовый контур v1 (productContext):** Login → Обзор (1) → Журнал (5) → Тренды (8) → Вахтенный (6). Мнемосхемы 2–4 и полный каталог отчётов 9 — фаза 2 (BACK API уже частично есть; FRONT UI отсутствует или stub).

**QueryBuilder:** в текущем codebase **нет** `PaginateQueryParams` / `QueryBuilder` / `mapping_filters`. List-фильтры — inline Query на endpoint (`/api/events` cursor, `/api/warnings/history` offset). Canon skill QueryBuilder **применяется** только если в eNN явно вводим унифицированный filter pipeline; иначе сохраняем as-built param mirror front↔back без насильственной миграции на QB.

**`/guides`:** маршрутов `frontend/src/app/**/guides/**` **нет**. Для operational portal это **n/a** (не content-site). В registry зафиксировано явно, чтобы не путать с отсутствующим wire.

---

## Element registry (as-built)

> Источник: routes `frontend/src/app/**` + features/ds + back/front implement indexes. **Не** gap/, contracts/, BACK/FRONT decompose shards как AC.
> После таблицы — секции `## Element eNN` для каждого P0/P1 (+ P2 surfaces с BACK без FRONT).

| route | UI element (component) | data need | API today | BACK implement | FRONT implement | priority |
|-------|------------------------|-----------|-----------|----------------|-----------------|----------|
| `/` | redirect → `/login` | none | — static | — | s01 scaffold | P0 |
| `/login` | `LoginPage` + `LoginTile` roster | roster persons | ✅ live (`GET /api/watch/roster`) + ⚠️ MSW | T-003 s07 | s08 session-tiles | P0 |
| `/login` | session create → cookie | `person_id` → session | ✅ live (`POST /api/session`) + ⚠️ MSW | T-003 s07 | s08 / useSession | P0 |
| `(auth)/*` | `AppShell` + `AppNav` + `SessionChip` | session person + logout | ✅ `DELETE /api/session` | T-003 s07 | s07 shell | P0 |
| `(auth)/*` | `StatusBar` + `useStatusBarAlarms` | recent alarms | ✅ `GET /api/events` + WS events | T-003 s04/s06 | s07 | P0 |
| `(auth)/*` | `FreshnessController` + banners | sources freshness / quarantine | ✅ `GET /api/sources/status` + WS | T-003 s09 | s07 / s15 | P0 |
| `(auth)/*` | `WsManager` / `useWsChannel` | realtime values+events | ✅ `WS /api/stream` | T-003 s06 | s05 ws-manager | P0 |
| `/overview` | `AggregateShipStatus` + tree cards | assets tree | ✅ `GET /api/assets/tree` | T-003 s02 | s09 | P0 |
| `/overview` | `MoSection` / lamps | node status/quality | from tree (+ WS patch) | T-003 s02/s06 | s09 | P0 |
| `/overview` | `DrillDownStubModal` | mnemo phase-2 stub | ❌ UI stub; BACK ✅ mnemo | T-005 s08/s09 | s09 stub | P1 |
| `/journal` | `EventFilters` + infinite list | events page | ✅ `GET /api/events` | T-003 s04 | s10 | P0 |
| `/journal` | `ReconstructionBanner` | header `X-Events-Reconstruction` | ✅ header on events | T-003 s04 | s10 | P0 |
| `/journal` | `SessionEventFilter` | session-sourced events | filter `source=session` on same API | T-003 s07 | s10 | P1 |
| `/journal` | `useEventsRealtime` | live event append | ✅ WS events channel | T-003 s06 | s10 | P0 |
| `/trends` | `TagPicker` | tag leaves from tree | ✅ assets tree | T-003 s02 | s12 | P0 |
| `/trends` | `TrendChartContainer` + `useSeries` | series / aggregate | ✅ `/api/series`, `/api/series/aggregate` | T-003 s03 | s11–s12 | P0 |
| `/trends` | `useSetpoints` overlay | setpoints list | ✅ `GET /api/setpoints` | T-003 s05 / T-005 s11 | s12 | P0 |
| `/trends` | `useEventMarkers` | markers in range | ✅ `GET /api/events` | T-003 s04 | s12 | P1 |
| `/trends` | `useTrendRealtime` | live series patch | ✅ WS values | T-003 s06 | s12 | P0 |
| `/watch` | `useWatchReport` + sections | watch report JSON/HTML | ✅ `GET /api/reports/watch` | T-003 s08 / T-005 s10 | s13 | P0 |
| `/watch` | `WatchVerdict` + `DebounceGroupRow` | summary / debounce groups | from report body | T-005 s04 templates | s13 | P0 |
| `/watch` | `DataQualityPanel` | quarantine / stale intervals | from report.data_quality | T-003/T-005 reports | s13 | P0 |
| `/watch` | `HandoffButton` | deep-links journal | — client routing | — | s14 handoff | P1 |
| `/dev/appearance` | theme/design controls | none | — static | — | s02 tokens | P2 |
| *(future UI)* | Warnings / B13 strip | active warnings | ✅ BACK `/api/warnings*` · FRONT ❌ client | T-005 s06/s07 | — | P1 |
| *(future UI)* | Vessel mode chip | vessel state | ✅ `/api/vessel/state*` · FRONT ❌ | T-005 s11 | — | P1 |
| *(future UI)* | Mnemo screens 2–4 | schema+values+WS | ✅ `/api/mnemo*` · FRONT ❌ (stub only) | T-005 s08/s09 | stub | P1 |
| *(future UI)* | Reports hub 9 | catalog/jobs/versions | ✅ reports* · FRONT partial (`fetchReports` unused) | T-005 s10 | types only | P1 |
| *(ops)* | Admin storage/OTA/audit | ops panels | ✅ `/api/admin/*` · FRONT ❌ | T-005 s14/s16 | — | P2 |
| `/guides`, `/guides/[slug]` | — | — | **n/a** (нет content guides в продукте) | — | — | — |

**Legend API today:** ✅ live endpoint exists | ❌ missing on that side | ⚠️ mock fallback (MSW / `NEXT_PUBLIC_API_MOCK=1`) | — static / no API

---

## Element e01 — Home redirect `/`

### §UI
- route: `frontend/src/app/page.tsx`
- component: Next `redirect("/login")`

### §Data need
- нет

### §API today
- — static

### §Contract outline
```
N/A — server redirect only
```

### §BACK / §FRONT wire
- FRONT: сохранить единственный entry redirect; не добавлять mock home.
- BACK: не требуется.

### §Verify
- Playwright: open `/` → land `/login`
- §0.11: нет API pair

---

## Element e02 — Login roster tiles

### §UI
- route: `/login` → `frontend/src/app/login/page.tsx` → `features/session/LoginPage.tsx`
- DS: `components/ds/LoginTile.tsx`

### §Data need
- список вахтенных: `person_id`, `name`, `rank`, `tile_order`, `active`, `default_screen`
- только `active=true`, сортировка по `tile_order`

### §API today
- ✅ `GET /api/watch/roster` (`apps/api/.../session.py` `getWatchRoster`)
- ⚠️ MSW `*/api/watch/roster` → `rosterFixture`
- FRONT client: `lib/api/session.ts` → `fetchRoster`

### §Contract outline
```
GET /api/watch/roster
request: (cookie optional; roster public for login)
response 200:
  { items: [{ person_id, name, rank, tile_order, active, default_screen }] }
DB/source: ship-pack roster / SessionService.roster()
```

### §BACK / §FRONT wire
- BACK: уже live (T-003 s07); роль/permissions snapshot — T-005 B11 creative.
- FRONT: убрать зависимость от MSW в non-mock env; проверить empty roster / inactive tiles.
- Wire: `NEXT_PUBLIC_API_URL` + `credentials: include` уже в `client.ts`.

### §Verify
- §0.11: `fetchRoster` ↔ `@router.get("/watch/roster")`
- vitest: `session.test.tsx` roster path
- pytest: session/roster tests under `apps/api/tests`
- Playwright: tiles visible on `/login`

---

## Element e03 — Session create / logout

### §UI
- `LoginPage` on tile click → `useSession().login`
- `AppShell` `SessionChip` → logout

### §Data need
- create: `{ person_id }` → session cookie `shipsense_session` + `SessionResponse`
- logout: clear cookie; optional session event

### §API today
- ✅ `POST /api/session` → 201 + Set-Cookie
- ✅ `DELETE /api/session` → 204
- ⚠️ MSW both
- FRONT: `createSession`, `deleteSession`; `onUnauthorized` → redirect login

### §Contract outline
```
POST /api/session
body: { person_id: string }
response 201: { session_id, person_id, name, rank, started_at, expires_at, token, default_screen }
side-effect: Set-Cookie shipsense_session=…; HttpOnly; SameSite=Lax; Path=/
errors: 400 VALIDATION_ERROR | 404 NOT_FOUND

DELETE /api/session
response 204
side-effect: clear cookie; access/session audit as implemented
```

### §BACK / §FRONT wire
- FRONT: после login navigate to `default_screen` mapping (overview/journal/trends/watch) — проверить parity с BACK enum.
- BACK: audit writer / session events (T-005 hardening) — UI не показывает audit, но cookie auth обязателен для `(authenticated)` layout.

### §Verify
- §0.11 POST/DELETE pairs
- Playwright: pick tile → `/overview` (or mapped) with cookie; logout → `/login`
- pytest session endpoint suite

---

## Element e04 — AppShell chrome (nav + session chip + theme)

### §UI
- `features/shell/AppShell.tsx`, `AppNav.tsx`
- DS: `SessionChip`, `ThemeSwitcher`, `DesignSwitcher`
- layout: authenticated group under `frontend/src/app/(authenticated)/`

### §Data need
- session person from client state / cookie presence
- nav routes: `/overview`, `/journal`, `/trends`, `/watch`

### §API today
- session delete only for logout; nav — static

### §Contract outline
```
N/A for nav links
DELETE /api/session — see e03
```

### §BACK / §FRONT wire
- Guard: unauthenticated access to `(authenticated)/*` must redirect `/login` (layout/middleware as implemented in FRONT s07).
- Не смешивать theme/design persistence с API.

### §Verify
- Playwright: nav between four screens; chip shows name
- vitest: `AppShell.test.tsx`, `AppNav.test.tsx`

---

## Element e05 — StatusBar alarms

### §UI
- DS `StatusBar` in `AppShell`
- hook `features/shell/useStatusBarAlarms.ts`

### §Data need
- bootstrap: recent alarm/warning events
- live: WS events channel updates
- click → `/journal?asset_id=&from=`

### §API today
- ✅ REST `GET /api/events` (bootstrap query in hook)
- ✅ WS `/api/stream` subscribe events
- ⚠️ MSW covers REST events only (не WS)

### §Contract outline
```
GET /api/events?severity=alarm&severity=warning&limit=…
response: { items: EventItem[], next_cursor, has_more }
header: X-Events-Reconstruction: edge_only|…

WS /api/stream
client → { action: "subscribe", channels: ["events"], subscription_id }
server → event frames matching lib/ws/types
```

### §BACK / §FRONT wire
- FRONT severity filter must match BACK enum (`info|warning|alarm`).
- Deep-link query keys must match journal filters (`asset_id`, `from`).

### §Verify
- §0.11: `fetchEvents` + WsManager events ↔ endpoints
- vitest: `StatusBar.alarms.test.tsx`
- Playwright: alarm chip → journal filtered

---

## Element e06 — Freshness + quarantine chrome

### §UI
- `FreshnessController`, DS `FreshnessBanner`, `QuarantineBanner`
- quality global (FRONT s15)

### §Data need
- `GET /api/sources/status`: connected, last_poll_ts, tags_quarantine/stale/active, quality_summary
- WS can force stale / last ts

### §API today
- ✅ `GET /api/sources/status` (`health.py`)
- ✅ WS stream side-effects via `useWsChannel`
- ⚠️ MSW sources fixture
- FRONT: `lib/api/sources.ts` `fetchSourcesStatus`

### §Contract outline
```
GET /api/sources/status
response 200: { items: [{ source_id, name, connected, last_poll_ts, error_count_24h, quality_summary, tags_active, tags_quarantine, tags_stale }] }
```

### §BACK / §FRONT wire
- Инвариант продукта: quarantine/stale **не** маскировать «нормой» в UI (уже в banners).
- Overview/Journal также дублируют sources query — дедуп через `queryKeys.sourcesStatus` (React Query).

### §Verify
- §0.11 sources pair
- vitest FreshnessController
- Playwright: banner visible when fixture quarantine > 0

---

## Element e07 — WebSocket fanout shared (`/api/stream`)

### §UI
- infra: `lib/ws/manager.ts`, `hooks/useWsChannel.ts`
- consumers: overview realtime, journal realtime, trends realtime, status bar, freshness

### §Data need
- subscribe values (tags ≤100/chunk), events, resume_cursor, snapshot

### §API today
- ✅ `WS /api/stream` (`stream.py`)
- FRONT env: `NEXT_PUBLIC_WS_URL` (tests use `ws://localhost:8000/api/stream`)
- MSW: **нет** WS mock → live или unit MockWebSocket

### §Contract outline
```
WS /api/stream
subscribe: { action, channels, tags?, subscription_id, snapshot?, resume_cursor? }
unsubscribe: { action: "unsubscribe", subscription_id }
server frames: value updates | event items | error
```

### §BACK / §FRONT wire
- Единый менеджер; не открывать второй сокет на экран.
- Chunking 100 tags — BACK должен принимать chunked subs (as-built).
- Auth cookie on WS handshake — проверить edge gateway/CORS same-origin compose.

### §Verify
- vitest: `lib/ws/manager.test.ts`
- pytest: WS fanout tests from T-003 s06
- §0.11: `NEXT_PUBLIC_WS_URL` path ends with `/api/stream`

---

## Element e08 — Overview assets tree + aggregate status

### §UI
- route `/overview` → `OverviewPage`
- DS: `AggregateShipStatus`, `OverviewGroupCard`, lamps via tree

### §Data need
- hierarchical plant→system→equipment→tag with aggregate status, last_value/quality

### §API today
- ✅ `GET /api/assets/tree` Cache-Control max-age=60
- ⚠️ MSW `assetsTreeFixture`
- FRONT: `useAssetsTree` → `fetchAssetsTree`

### §Contract outline
```
GET /api/assets/tree
response 200:
  { root: AssetTreeNode, generated_at }
AssetTreeNode: { id, kind, name, status, worst_tag_id?, children?, tag_id?, unit?, last_value?, last_quality? }
kind: plant|system|equipment|tag
```

### §BACK / §FRONT wire
- FRONT `treeUtils` must tolerate missing optional fields.
- Realtime patch: `useOverviewRealtime` merges WS values into React Query cache — contract tag_id identity.

### §Verify
- §0.11 assets pair
- vitest `OverviewPage.test.tsx`
- pytest `apps/api/tests/api/test_assets_tree.py` (note: currently related to QA-4 vessel pack tags blocker on BACK suite)

---

## Element e09 — Overview MoSection lamps

### §UI
- `features/overview/MoSection.tsx` + DS `Lamp`

### §Data need
- per-node AggregateStatus / Quality from tree (+ live)

### §API today
- data from e08 tree; no separate endpoint

### §Contract outline
```
Derived from AssetsTreeResponse + WS value frames
Quality enum shared: frontend/src/lib/quality/types.ts ↔ BACK quality codes
```

### §BACK / §FRONT wire
- Align quality vocabulary (good/stale/quarantine/… as implemented).
- No extra REST.

### §Verify
- vitest Lamp / OverviewPage status rendering
- §0.11 quality types cross-check (grep enum both sides)

---

## Element e10 — Overview drill-down stub → future mnemo

### §UI
- `DrillDownStubModal` — copy «Мнемосхема: фаза 2»

### §Data need
- future: schema list + values for selected group/system

### §API today
- FRONT: ❌ stub only
- BACK: ✅ `GET /api/mnemo/schemas`, `GET /api/mnemo/schemas/{id}`, `GET /api/mnemo/schemas/{id}/values`, `WS /api/mnemo/{schema_id}`

### §Contract outline
```
GET /api/mnemo/schemas?include_generators=false
GET /api/mnemo/schemas/{schema_id}
GET /api/mnemo/schemas/{schema_id}/values
WS /api/mnemo/{schema_id}
```

### §BACK / §FRONT wire
- P1 wire: заменить stub на экран/панель мнемо (новый route или modal) + `lib/api/mnemo.ts` (сейчас отсутствует).
- До wire: оставить stub, но в DECOMPOSE пометить depends on FRONT creative mnemo.

### §Verify
- after wire: §0.11 mnemo clients ↔ endpoints; Playwright open schema
- until wire: assert stub copy + no false-green API call

---

## Element e11 — Journal filters + infinite list

### §UI
- `/journal` → `JournalPage`
- DS `EventFilters`, `EventRow`
- hooks: `useEventsInfinite`, `journalFilters.ts`, `journalSort.ts`

### §Data need
- cursor pagination; filters: from/to, event_name[], severity[], asset_id, source, ack?, limit

### §API today
- ✅ `GET /api/events`
- ⚠️ MSW (static list; cursor poorly simulated)
- FRONT: `lib/api/events.ts` `fetchEvents`

### §Contract outline
```
GET /api/events
query: from?, to?, event_name[]?, severity[]?, asset_id?, source?, ack?, cursor?, limit=50(1-200)
response: { items: EventItem[], next_cursor, has_more }
header expose: X-Events-Reconstruction
```

### §BACK / §FRONT wire
- URL search params ↔ `EventsQuery` mirror (deep links from StatusBar / Trends / Handoff).
- MSW must support multi-page cursor for E2E или E2E на live API.
- **Не** внедрять QueryBuilder в этом eNN unless contract decision in CREATIVE — as-built inline params.

### §Verify
- §0.11 events
- vitest `JournalPage.test.tsx`
- Playwright: apply severity filter → rows match; load more

---

## Element e12 — Reconstruction banner

### §UI
- `ReconstructionBanner` reads response header from events fetch

### §Data need
- `X-Events-Reconstruction` value (`edge_only` etc.)

### §API today
- ✅ BACK sets header; FRONT constant `EVENTS_RECONSTRUCTION_HEADER`
- ⚠️ MSW sets header

### §Contract outline
```
Response header: X-Events-Reconstruction: <enum>
Access-Control-Expose-Headers must include header for browser JS
```

### §BACK / §FRONT wire
- CORS expose header обязателен для browser (compose API CORS config).
- Banner copy не маскирует partial reconstruction.

### §Verify
- unit: header → banner text
- §0.11 header name string equality front↔back

---

## Element e13 — Journal session event filter

### §UI
- `SessionEventFilter.tsx`

### §Data need
- filter `source=session` (and related session events from B11)

### §API today
- ✅ same `/api/events?source=session`
- FRONT filter util maps UI → query

### §Contract outline
```
GET /api/events?source=session&from=&to=&…
```

### §BACK / §FRONT wire
- Session login/logout must emit events visible here (BACK session service).
- Empty state when no session events.

### §Verify
- Playwright after login/logout → session events appear with filter on
- pytest events source filter

---

## Element e14 — Journal realtime append

### §UI
- `useEventsRealtime.ts`

### §Data need
- WS event frames merged into infinite query pages

### §API today
- ✅ WS events channel (e07)
- no dedicated REST

### §Contract outline
```
WS event payload shape ≡ EventItem fields used by EventRow
```

### §BACK / §FRONT wire
- Dedupe by event `id` when REST page + WS overlap.
- Respect active filters client-side on WS append.

### §Verify
- vitest realtime merge
- compose smoke: emit event → row appears without reload

---

## Element e15 — Trends TagPicker

### §UI
- `/trends` → `TrendsPage` + DS `TagPicker`

### §Data need
- tag leaves from assets tree (id, name, unit)

### §API today
- ✅ `GET /api/assets/tree` (reuse e08 client)

### §Contract outline
```
Derived: flatten kind==="tag" from AssetsTreeResponse
```

### §BACK / §FRONT wire
- Tag id string identity must match series `tag` query param.
- Empty tree → StateShell empty (not spinner forever).

### §Verify
- vitest TagPicker
- Playwright select tag → chart request fires

---

## Element e16 — Trends series / aggregate chart

### §UI
- `TrendChartContainer`, `useSeries`, uPlot adapter

### §Data need
- single: `/api/series?tag&from&to&resolution`
- multi: `/api/series/aggregate?tags[]&from&to&resolution&fn`

### §API today
- ✅ both endpoints
- ⚠️ MSW series fixtures
- FRONT: `lib/api/series.ts`

### §Contract outline
```
GET /api/series?tag=&from=&to=&resolution=auto
→ SeriesResponse { tag_id, name, unit, from, to, resolution, points[] }

GET /api/series/aggregate?tags=&tags=&from=&to=&resolution=&fn=avg|min|max|last
→ SeriesAggregateResponse { from, to, resolution, series: [{ tag_id, unit, points }] }

points: { ts, value|null, quality, min?, max?, samples? }
```

### §BACK / §FRONT wire
- `buildQueryString` array → repeated keys must match FastAPI list parsing.
- Downsample resolution vocabulary front presets ↔ BACK auto.
- Null gaps / quality coloring per product invariant.

### §Verify
- §0.11 series pairs
- vitest TrendsPage / useSeries
- pytest series tests
- Playwright range change → refetch

---

## Element e17 — Trends setpoints overlay

### §UI
- `useSetpoints.ts` + chart overlays

### §Data need
- current setpoints list; optional history segments (client exists, UI may not call history yet)

### §API today
- ✅ `GET /api/setpoints`
- ✅ `GET /api/setpoints/history?tag=` (FRONT `fetchSetpointHistory` **defined but unused** in features)
- ✅ `GET /api/setpoints/changelog` (BACK only; FRONT ❌)
- ⚠️ MSW setpoints + history

### §Contract outline
```
GET /api/setpoints → { items: [{ tag_id, value, unit, label, effective_from }] }
GET /api/setpoints/history?tag= → { tag_id, segments: [{ from_ts, to_ts|null, value }] }
```

### §BACK / §FRONT wire
- P0: wire list overlay for selected tags.
- P1: wire history segments for range shading; changelog for audit UI if needed.
- Remove dead client or consume it (forbid forever-unused).

### §Verify
- §0.11 setpoints; history after UI uses it
- vitest overlay with fixture

---

## Element e18 — Trends event markers + deep-link

### §UI
- `useEventMarkers.ts`, `journalFromMarker.ts`, `trendsParams.ts`

### §Data need
- events in chart from/to window; click → `/journal?...`

### §API today
- ✅ `GET /api/events` with from/to (+ optional asset)

### §Contract outline
```
GET /api/events?from=&to=&asset_id?=&limit=
deep-link: /journal?from=&to=&asset_id=&severity?=
```

### §BACK / §FRONT wire
- Param names identical to journalFilters.
- Marker severity colors ≡ EventRow.

### §Verify
- Playwright click marker → journal URL params
- vitest journalFromMarker

---

## Element e19 — Trends realtime series patch

### §UI
- `useTrendRealtime.ts`

### §Data need
- WS values for selected tags append/patch last point

### §API today
- ✅ WS values channel (e07)

### §Contract outline
```
WS value frame: tag_id, ts, value, quality
```

### §BACK / §FRONT wire
- Only patch tags currently plotted; unsubscribe on tag change.
- Stale quality must paint, not drop silently.

### §Verify
- unit MockWebSocket patch
- §0.11 WS URL

---

## Element e20 — Watch report body

### §UI
- `/watch` → `WatchPage`, `useWatchReport`
- DS `WatchSection`, print styles as applicable

### §Data need
- watch report for period from/to (search params); format json default

### §API today
- ✅ `GET /api/reports/watch?from&to&format&session_id?`
- ⚠️ MSW watch report (+ html branch)
- FRONT: `fetchWatchReport`
- BACK also: generate jobs, catalog, versions (see e24) — Watch page does not poll jobs yet

### §Contract outline
```
GET /api/reports/watch?from=&to=&format=json|html&session_id?&watch_id?
response json: WatchReportResponse {
  generated_at, watchkeeper{}, period{}, data_quality{}, summary{}, highlights[], tags_snapshot[]
}
response html: text/html
```

### §BACK / §FRONT wire
- Period defaults (current watch window) must match BACK schedule semantics when `GET /api/watch/schedule` wired (e25).
- Fallback: if highlights empty, `useWatchReport` also fetches events — document as intentional dual-fetch.

### §Verify
- §0.11 reports/watch
- vitest WatchPage.test
- Playwright load `/watch?from=&to=`

---

## Element e21 — Watch verdict + debounce groups

### §UI
- `WatchVerdict`, `DebounceGroupRow`, `debounce.ts`

### §Data need
- `summary.verdict`, alarms_count, debounce groups from highlights / template output (B12)

### §API today
- fields inside WatchReportResponse (BACK templates T-005 s04)

### §Contract outline
```
summary: { events_count, alarms_count, protections_count, verdict }
highlights: opaque list consumed by debounce grouping helpers
```

### §BACK / §FRONT wire
- FRONT debounce helpers must match BACK template debounce policy (creative-report-forms) — document mapping in eNN §Contract at DECOMPOSE.
- No separate endpoint.

### §Verify
- unit debounce.test.ts
- fixture-driven WatchPage render

---

## Element e22 — Watch DataQualityPanel

### §UI
- `DataQualityPanel.tsx`

### §Data need
- `data_quality.quarantine_tags`, `stale_intervals`, `banner`

### §API today
- subset of watch report

### §Contract outline
```
data_quality: {
  quarantine_tags: string[],
  stale_intervals: [{ from, to }],
  banner: string
}
```

### §BACK / §FRONT wire
- Banner text from BACK is source of truth; FRONT does not invent «OK» when quarantine non-empty.

### §Verify
- vitest panel with quarantine fixture
- Playwright visible banner text

---

## Element e23 — Watch handoff buttons

### §UI
- `HandoffButton.tsx` + `lib/routing/handoff`

### §Data need
- client-only links to journal presets (active alarms / active now)

### §API today
- — static routing (no API)

### §Contract outline
```
GET navigation only:
  /journal?<preset query from HANDOFF_* constants>
```

### §BACK / §FRONT wire
- Preset query must be valid EventsQuery (e11).
- Optional P1: bind to `GET /api/watch/schedule` for «current watch» timestamps instead of relative client now.

### §Verify
- vitest HandoffButton.test
- Playwright click → journal filters applied

---

## Element e24 — Reports hub (фаза 2 UI; BACK already rich)

### §UI
- **нет route** `/reports` сегодня; product screen 9 phase 2
- FRONT has `fetchReports()` → `GET /api/reports` but **no feature consumer**

### §Data need
- catalog of report types; async generate; job poll; versioned HTML

### §API today
- ✅ `GET /api/reports/catalog` — canonical catalog
- ✅ `GET /api/reports` — list runs (also legacy empty-filter catalog branch for non-DB)
- ✅ `POST /api/reports/generate`, `POST /api/reports/watch/generate` → 202 job
- ✅ `GET /api/reports/jobs/{job_id}`
- ✅ `GET /api/reports/{id}`, `/versions/{v}`, `/versions/{v}/html`
- FRONT: only list+watch get; **missing** generate/job/version clients
- Drift risk: front `fetchReports` hits `/api/reports` expecting `ReportsListResponse`, while live DB path returns **run list** shape

### §Contract outline
```
GET /api/reports/catalog → ReportsListResponse items[{type,title,formats,description}]
GET /api/reports?type&from&to&limit → ReportRunListResponse { items, has_more }
POST /api/reports/generate body { type, period } → 202 ReportJob
GET /api/reports/jobs/{job_id} → ReportJob
GET /api/reports/{report_id}/versions/{version}/html → text/html
```

### §BACK / §FRONT wire
- Fix client: catalog → `/api/reports/catalog`; runs → `/api/reports` with filters.
- New UI route or section under Watch for «полный B12» when product ready.
- MSW: add catalog + jobs handlers when UI lands.

### §Verify
- §0.11 all report paths used by UI
- contract test catalog vs runs shapes
- Playwright generate→poll→render HTML (after UI)

---

## Element e25 — Watch schedule

### §UI
- none yet (period pickers use search params / local now)

### §Data need
- current watch window boundaries for default `/watch` period

### §API today
- ✅ `GET /api/watch/schedule` (`watch_schedule.py`)
- FRONT ❌ no client

### §Contract outline
```
GET /api/watch/schedule
response: dict schedule fields (as-built service) — pin exact schema in DECOMPOSE eNN from OpenAPI/service
auth: session cookie
```

### §BACK / §FRONT wire
- Add `lib/api/watch.ts` + query key; WatchPage defaults from schedule when params absent.

### §Verify
- §0.11 schedule pair after client
- Playwright `/watch` without params uses server window

---

## Element e26 — Warnings / B13 surface

### §UI
- none (product: drift warnings — arithmetic B13, no «AI» copy)

### §Data need
- active warnings + history

### §API today
- ✅ `GET /api/warnings`, `GET /api/warnings/history`
- FRONT ❌

### §Contract outline
```
GET /api/warnings?active&tag_id&asset_id&since
GET /api/warnings/history?tag_id&asset_id&since&limit&offset → has_more, next_offset
```

### §BACK / §FRONT wire
- Placement candidates: Overview strip, Trends overlay, dedicated panel — decide in INTEG CREATIVE if multi-option.
- Types + client + MSW + UI element.

### §Verify
- pytest warnings API
- Playwright warning visible when fixture active

---

## Element e27 — Vessel state

### §UI
- none (ops/mode chip future)

### §Data need
- mode ANCHORAGE/STEAMING/…; override with TTL (permissioned)

### §API today
- ✅ `GET /api/vessel/state`, `POST /api/vessel/state/override`
- FRONT ❌

### §Contract outline
```
GET /api/vessel/state → VesselStateResponse
POST /api/vessel/state/override body { mode, ttl_minutes } → VesselStateResponse
```

### §BACK / §FRONT wire
- OTA gate depends on vessel mode (admin) — crew UI may be read-only chip first.
- Permission matrix B11 for override.

### §Verify
- §0.11 after client
- role-denied override → clear error (no silent fail)

---

## Element e28 — Admin ops (storage / OTA / audit)

### §UI
- none in crew portal; possible `/admin` later

### §Data need
- storage health, OTA status/approve/trigger, access audit list

### §API today
- ✅ `GET /api/admin/storage`
- ✅ `GET/POST /api/admin/ota/status|approve|trigger`
- ✅ `GET /api/admin/access/audit?limit&offset`
- FRONT ❌

### §Contract outline
```
GET /api/admin/storage
GET /api/admin/ota/status
POST /api/admin/ota/approve
POST /api/admin/ota/trigger
GET /api/admin/access/audit?limit&offset
authz: Permission.* fail-closed
```

### §BACK / §FRONT wire
- Out of P0 crew journeys; P2 section portal or separate ops app.
- If in scope: new routes under authenticated admin role only.

### §Verify
- pytest admin authz
- no accidental public fetch from crew screens

---

## Element e29 — Dev appearance (non-prod)

### §UI
- `/dev/appearance` → `AppearanceControls`

### §Data need
- none

### §API today
- —

### §Contract outline
```
N/A
```

### §BACK / §FRONT wire
- Exclude from production nav; no API mock required.

### §Verify
- page renders theme controls

---

## Element e30 — Guides (explicit n/a)

### §UI
- routes `/guides`, `/guides/[slug]` — **absent**

### §Data need
- n/a for ShipSense operational portal

### §API today
- —

### §Contract outline
```
N/A — product has no content guides surface in v1
```

### §BACK / §FRONT wire
- Do not invent mock guides to satisfy content-site templates.
- If later docs portal appears — new INTEG PLAN section.

### §Verify
- registry documents absence; Glob confirms no `guides/page.tsx`

---

## API inventory

| Method | Path | DB / source | Consumer element(s) | Status |
|--------|------|-------------|---------------------|--------|
| GET | `/api/watch/roster` | roster pack / session svc | e02 | ✅ wired front |
| POST | `/api/session` | session + cookie + events | e03 | ✅ |
| DELETE | `/api/session` | session clear | e03/e04 | ✅ |
| GET | `/api/assets/tree` | assets semantic + latest | e08,e09,e15 | ✅ |
| GET | `/api/series` | Timescale downsample | e16 | ✅ |
| GET | `/api/series/aggregate` | Timescale | e16 | ✅ |
| GET | `/api/events` | events store | e05,e11–e14,e18,e20 fallback | ✅ |
| GET | `/api/setpoints` | ship-pack / APS | e17 | ✅ |
| GET | `/api/setpoints/history` | history | e17 (client unused) | ⚠️ front dead |
| GET | `/api/setpoints/changelog` | changelog | — | ❌ front |
| GET | `/api/sources/status` | health aggregator | e06, overview, journal | ✅ |
| GET | `/api/health` | health | — (ops) | ❌ front |
| GET | `/api/reports/watch` | reports svc | e20–e22 | ✅ |
| GET | `/api/reports` | runs list / legacy catalog | e24 drift | ⚠️ |
| GET | `/api/reports/catalog` | types | e24 | ❌ front |
| POST | `/api/reports/generate` | jobs | e24 | ❌ front |
| POST | `/api/reports/watch/generate` | jobs | e24 | ❌ front |
| GET | `/api/reports/jobs/{id}` | job store | e24 | ❌ front |
| GET | `/api/reports/{id}` (+ versions/html) | report runs | e24 | ❌ front |
| GET | `/api/watch/schedule` | schedule svc | e25 | ❌ front |
| GET | `/api/warnings` | B13 | e26 | ❌ front |
| GET | `/api/warnings/history` | B13 | e26 | ❌ front |
| GET | `/api/vessel/state` | vessel svc | e27 | ❌ front |
| POST | `/api/vessel/state/override` | vessel svc | e27 | ❌ front |
| GET | `/api/mnemo/schemas` (+ id, values) | mnemo registry | e10 | ❌ front |
| WS | `/api/mnemo/{schema_id}` | mnemo stream | e10 | ❌ front |
| WS | `/api/stream` | ring buffer fanout | e05,e07,e14,e19 | ✅ |
| GET | `/api/admin/storage` | raid/backup | e28 | ❌ front |
| GET/POST | `/api/admin/ota/*` | OTA coordinator | e28 | ❌ front |
| GET | `/api/admin/access/audit` | access_audit | e28 | ❌ front |

Prefix канон: `settings.API_V1_STR = "/api"` (`apps/api/app/core/settings.py`). Front paths always `/api/...` via `NEXT_PUBLIC_API_URL` host join.

---

## User journeys (E2E)

| ID | Persona | Path | Elements touched |
|----|---------|------|------------------|
| J1 | Вахтенный (guest→session) | `/` → `/login` → tile → `/overview` | e01,e02,e03,e04,e08,e09 |
| J2 | Вахтенный | Overview → alarm StatusBar → Journal filtered | e05,e06,e11,e12 |
| J3 | Механик | Journal filters + infinite + realtime | e11,e13,e14 |
| J4 | Механик | Trends: pick tags → series → setpoints → marker→journal | e15–e19 |
| J5 | Стармех | Watch report period → verdict → DQ → handoff journal | e20–e23 |
| J6 | Стармех (фаза 2) | Mnemo drill from overview | e10 (+ mnemo API) |
| J7 | Стармех (фаза 2) | Reports hub generate/poll/html | e24 |
| J8 | Ops (фаза 2) | Admin storage/OTA/audit | e28 |
| J9 | Dev | `/dev/appearance` theme | e29 |

---

## Rollout (by UI element, not by layer)

> Порядок — стратегия. **Не** ставить `- [ ]` / `done` здесь. Статус → `decompose/index.md` после DECOMPOSE.

**Фаза 0 — Live crew funnel (убрать false-green mock на P0)**  
1. e02 roster + e03 session cookie against live API  
2. e07 WS stream + e05 StatusBar + e06 freshness  
3. e08/e09 overview tree+lamps realtime  
4. e11/e12/e14 journal list+header+WS  
5. e15/e16/e17/e19 trends series+setpoints+WS  
6. e20/e21/e22 watch report surfaces  

**Фаза 1 — Contract hygiene & deep-links**  
7. e18 markers + e23 handoff query parity  
8. e13 session events  
9. e17 history consumption or delete dead client  
10. e24 catalog path fix (`/reports/catalog`) even before full hub UI  

**Фаза 2 — BACK p2 surfaces → FRONT**  
11. e25 watch schedule defaults  
12. e26 warnings strip  
13. e27 vessel chip (read-only first)  
14. e10 mnemo replace stub  
15. e24 reports hub UI (generate/jobs/html)  

**Фаза 3 — Ops / non-crew**  
16. e28 admin panels (role-gated)  
17. e29 keep dev-only  

**Explicit non-goals in this plan:** collector/writer infra, OTA RAUC internals, RAID restore scripts — already BACK; INTEG only if UI consumes admin API.

---

## Test matrix

| Journey | BACK pytest | FRONT vitest | Wire / E2E |
|---------|-------------|--------------|------------|
| J1 | `tests/api` session/roster | `session.test.tsx` | Playwright login→overview |
| J2 | events + stream | StatusBar.alarms / Freshness | Playwright alarm→journal |
| J3 | events cursor filters | JournalPage.test | Playwright filters+load more |
| J4 | series + setpoints + assets | TrendsPage / useSeries | Playwright tag→chart |
| J5 | reports watch | WatchPage.test | Playwright watch period |
| J6 | mnemo endpoints | (new) | Playwright open schema |
| J7 | reports generate/jobs | (new) | Playwright job poll |
| J8 | admin_* authz | (new) | Playwright deny crew role |
| Mock gate | — | msw handlers | `NEXT_PUBLIC_API_MOCK=0` for wire E2E |

**Scenario rule (INTEG core):** user-visible flow → scenario test до FINISH eNN; vitest alone недостаточно для «пользователь нажал X».

**pytest runner:** cwd repo root, `.venv/bin/pytest …` only.

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| `NEXT_PUBLIC_API_MOCK=1` left on | false-green portal | Phase 0 E2E with mock=0; gate in compose web env |
| BACK QA T-005 blocked (vessel pack tags / fixtures) | live assets/series flaky | Track BACK BUGFIX QA-4; INTEG e08/e16 verify after green |
| `/api/reports` shape drift vs `fetchReports` | runtime type break when hub lands | e24 fix catalog path first |
| Dead clients (`fetchSetpointHistory`, `fetchReports`) | §0.11 false sense of wire | consume or remove in e17/e24 |
| No MSW for warnings/mnemo/vessel/admin/WS | unit gaps | add handlers when eNN lands; WS keep MockWebSocket |
| Mixed pagination (cursor vs offset) | filter-utils confusion | document per-endpoint; don't force QB globally |
| CORS not exposing `X-Events-Reconstruction` | banner always empty in browser | verify API CORS expose headers in e12 |
| Mnemo stub forever | product screen 2–4 slip | e10 P1 explicit after FRONT creative |
| Admin API callable without UI authz review | accidental expose | e28 role gate + no fetch from crew layouts |
| QueryBuilder skill mismatch | wasted rewrite | use only if eNN introduces unified filters |

---

## §0.11 integration checklist (portal)

Для каждого eNN IMPLEMENT перед FINISH:
1. Grep FRONT path string ↔ BACK `@router` path (включая prefix `/api`).
2. Query/body field names mirror (arrays repeated keys).
3. Error envelope `{ error: { code, message } }` ↔ `ApiError` parser.
4. Cookie `credentials: include` on mutating session routes.
5. WS URL path `/api/stream` (and later `/api/mnemo/{id}`).
6. MSW handler updated **or** mock flag off in scenario.
7. No orphan client function without consumer (или удаление в том же eNN).

---

## Handoff

- **Done:** Master-план portal wire `plan-v1-portal.md` — registry + e01–e30 detail, API inventory, journeys J1–J9, element-first rollout, test matrix, risks.
- **Files:** `memory-bank/integration/plan/plan-v1-portal.md`
- **Next:** `INTEG DECOMPOSE` → element-first `eNN-*.yaml` (+ inline §Contract) начиная с Фазы 0 (e02/e03…)
- **New chat:** yes
- **code_changed:** no
- **Depends note:** параллельно может идти `BACK BUGFIX` QA-4 (vessel pack tags); не блокирует DECOMPOSE docs, блокирует live E2E soft.
