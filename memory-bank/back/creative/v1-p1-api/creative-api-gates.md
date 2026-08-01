# CR-API-01..05 — API creative batch: series, stream, session, cursor, report

**Creative ID:** CR-API-01..05
**Plan:** [plan-v1-p1-api.md](../../plan/plan-v1-p1-api.md)
**Decompose:** [decompose-v1-p1-api/index.md](../../plan/decompose-v1-p1-api/index.md)
**Дата:** 2026-07-30
**Режим:** BACK CREATIVE
**Уровень:** L3–L4
**Статус:** closed; все пять gates разблокированы для BACK IMPLEMENT

## Skills в контексте

| Skill | Применение |
|---|---|
| `brainstorming` | batch override: требования, варианты, фиксация решений без паузы на approval |
| `architecture-patterns` | порты между HTTP/WS adapters, pure domain algorithms и storage/NOTIFY adapters |
| `improve-codebase-architecture` | deletion test: не вводить отдельный orchestration layer без реальной глубины; сохранять locality в feature services |
| `property-based-testing` | cursor round-trip, monotonic ordering, bucket/quality invariants, bounded buffer invariants |

## Общие решения

1. API features разделены по bounded context: `telemetry`, `events`, `stream`, `session`, `reports`.
2. HTTP endpoints отвечают только за parsing, вызов feature service и mapping результата в response; алгоритмы и state transitions не живут в endpoint-функциях.
3. Pure functions (resolution, cursor codec, verdict/grouping, ring operations) не зависят от FastAPI, SQLAlchemy или Postgres и тестируются отдельно.
4. Infrastructure access идёт через узкие порты: queries/read repositories, `LatestValueCache`, `EventWriterPort`, `NotifyListenerPort`. Feature service не импортирует collector write-path.
5. Phase 1 допускает in-memory state только там, где это явно указано ниже. Потеря процесса должна приводить к безопасному re-login/refetch, а не к ложному продолжению состояния.
6. Existing plan defaults are normative unless a more precise rule is stated here. No PDF, AI-generated verdict, IAM/RBAC, telemetry mutation or zero-filled data is introduced by this batch.

---

# CR-API-01 — Downsample algorithm

**Блокирует:** s03 `series-downsample`
**Тип:** Algorithm + Architecture
**AC:** AC-02, AC-03; plan §§6.2–6.3, 9, 16.1–16.2

## Постановка

`GET /api/series` должен давать примерно 1500 точек для окна любой длины, не скрывать spikes и не превращать отсутствие sample в нулевое значение. Quarantine/stale quality должна доходить до каждой точки. Aggregate должен использовать ту же resolution policy и не расходиться с одиночным series path.

## Варианты

### Вариант A — Timescale `time_bucket` + envelope

- Один SQL aggregation path с `avg`, `min`, `max`, `count` и worst-of quality.
- Boolean/string tags используют last value в bucket по `(official_ts, sample_id)`.
- Gaps остаются отсутствующими buckets; post-process только сортирует и сериализует.

**Плюсы:** предсказуемая нагрузка на Timescale, простой explain plan, min/max сохраняют spikes, одинаковый результат для REST и aggregate, легко ограничить число buckets.

**Минусы:** форма линии внутри bucket не сохраняется; min/max требуют дополнительных полей в response.

### Вариант B — LTTB или LTTB hybrid

- Сначала time-bucket предварительно ограничивает объём, затем LTTB выбирает визуально значимые точки.
- Для boolean/string остаётся отдельный last path.

**Плюсы:** иногда лучше визуальная форма графика при жёстком лимите точек.

**Минусы:** два алгоритма и два набора edge cases, хуже объяснимость для API consumers, возможна потеря отдельного spike без обязательного envelope, сложнее повторяемость между SQL и Python.

## Решение

Выбран **вариант A**. LTTB не входит в p1: spike сохраняется как `min`/`max`, а `value` остаётся средним. Это даёт глубокий `DownsampleService` с одной policy и узким query adapter вместо неглубокого набора визуальных эвристик.

### Resolution policy

1. Входное окно — `[from, to)`, timezone нормализуется к UTC; `to <= from` даёт validation error.
2. `resolution=auto`: `span_sec <= target_points` разрешает `raw`; иначе `ceil(span_sec / target_points)` округляется к `1s, 5s, 10s, 30s, 1m, 5m, 15m, 1h, 4h, 1d`.
3. `raw` разрешён только если ожидаемое число samples не превышает `target_points`; при более плотном источнике service повышает resolution, чтобы не отдавать 604800 raw points за неделю.
4. Target = 1500, допустимый ответ для AC — 1200–1800 points. Применяется bounded query/guard, а не `LIMIT` с потерей конца окна.
5. `API_SERIES_MAX_WINDOW_DAYS=90`; превышение даёт envelope `413 WINDOW_TOO_LARGE`. Неизвестный tag — `404 TAG_NOT_FOUND`.

### Bucket semantics

- Numeric: `value=avg(value_double)`, `min`, `max`, `samples`; `quality=worst_of(bucket)`.
- Boolean и string: `value=last_by_official_ts_then_sample_id`; `min/max` omitted or `null`, `samples` and worst quality remain present.
- `quality` ordering is monotonic from best to worst: `good < uncertain < stale < quarantine < bad` (exact enum mapping follows T-002 canonical quality model). A bad sample is never downgraded by a good sample in the same bucket.
- Empty buckets are omitted. No zero-fill, interpolation or fabricated quality.
- Buckets are ordered ascending by bucket timestamp and carry `ts` at bucket start. Boundaries are deterministic and UTC-based.
- Quarantine is returned as `quality=quarantine` in the affected points; the algorithm does not hide or replace it with `good`.

### Aggregate consistency

`fetch_aggregate` calls the same resolution and bucket contract for each tag, then applies only the requested `fn=avg|min|max|last` to the numeric value. `quality`, `samples` and gaps remain per tag. `fn=last` uses the same timestamp tie-breaker as boolean/string aggregation.

## Реализационное руководство

- `DownsampleService.pick_resolution(from_ts, to_ts, target)` — pure and unit-testable.
- `fetch_series` validates window/tag, selects query shape by tag kind, maps rows to `SeriesPoint`.
- `queries_series.py` contains parameterized SQL only; no user-provided SQL fragments or `@` variables.
- Keep `LatestValueCache` out of historical series; it is only for stream snapshots.
- If DB returns no rows for a known tag, return 200 with empty `points`, not fake points.

## Верификация

- Example tests: seven-day 1 Hz fixture returns 1200–1800 points and never `resolution=raw`; every point has `quality`.
- Quarantine fixture contains at least one `quality=quarantine`; no post-processing masks it.
- Gap fixture proves missing intervals are omitted, not zero-filled.
- Boolean fixture proves last value and deterministic tie-break.
- Property-based invariants: points are strictly non-decreasing by `ts`; `min <= value <= max` for numeric buckets; `samples > 0`; quality never improves after worst-of rollup; resolution is stable for equal windows; no valid window raises unexpectedly.

---

# CR-API-02 — WS fanout for six posts

**Блокирует:** s06 `ws-fanout`
**Тип:** Architecture + Algorithm
**AC:** AC-02, AC-04, AC-10; plan §§7–8, 16.4

## Постановка

До шести постов/браузеров должны получать live values/events, делать snapshot и resume, не используя shared `asyncio.Queue` с collector. Slow client не должен уничтожать event history; values допустимо сжимать по tag.

## Варианты

### Вариант A — central FanoutBridge + channel ring buffers + per-connection outbound state

- Один bridge слушает Postgres `NOTIFY shipsense_live` после commit.
- Два channel-specific ring buffers (`values`, `events`) с независимыми cursor.
- Каждый connection получает subscription state и собственную bounded outbound очередь; values coalesce latest per tag, events не coalesce.

**Плюсы:** соответствует process boundary, resume имеет явный источник истины, slow client изолирован, O(connections × subscriptions), тестируемые pure ring/coalesce primitives.

**Минусы:** bridge — single process hot path; при потере NOTIFY нужен fallback poll.

### Вариант B — drop slow clients целиком

- Бounded queue переполняется и соединение закрывается; клиент полностью refetch-ит snapshot.

**Плюсы:** проще backpressure и меньше памяти.

**Минусы:** теряются events, resume становится бесполезным именно для слабых клиентов, UI получает лишние disconnects; не соответствует требованию «events never dropped until buffer full».

### Вариант C — shared queue с collector

**Плюсы:** минимальная задержка в одном runtime.

**Минусы:** collector и API — разные OS processes; контракт не работает в compose и нарушает запрет плана. Отклонён.

## Решение

Выбран **вариант A**.

### Data flow

`writer commit → NOTIFY shipsense_live → FanoutBridge → channel cursor assignment → RingBuffer → ConnectionManager → per-connection delivery`.

Payload NOTIFY содержит только batch/watermark/tag hints. Bridge перечитывает свежие rows из DB через read adapters; payload не считается доверенным полным snapshot. Если NOTIFY listener временно недоступен, bridge выполняет bounded watermark poll с exponential backoff и метрикой деградации. Poll не создаёт второй cursor для уже опубликованного event.

### Buffer and backpressure policy

- `API_WS_BUFFER_SIZE=5000` на каждый channel; FIFO eviction увеличивает `oldest_available`.
- Cursor monotonic int64 **per channel**; правила codec зафиксированы в CR-API-04.
- Values coalesce только в outbound state конкретного slow connection: для одного `tag_id` сохраняется latest unsent frame; quality transition не может быть отброшен, если он новее.
- Events никогда не coalesce. Если connection не успевает принять event backlog, bridge сначала применяет bounded send timeout; затем закрывает только это соединение с code 1013 и логирует причину. Ring history остаётся доступной для reconnect.
- New subscription order: validate → optional snapshot from `LatestValueCache` → replay cursor range → ack → live frames. Snapshot is not inserted into ring and has no cursor.
- `resume_cursor=N` replays only frames with cursor `> N`; stale N below `oldest_available` returns `CURSOR_EXPIRED` with channel and oldest cursor.
- `API_WS_MAX_TAGS=100`; empty channels, missing tags for `values`, invalid resume shape and rate-limit overflow are protocol errors, not server crashes.

### Six-post sizing

Six connections are the acceptance baseline; connection manager must not assume one browser. Broadcast work is proportional to matching subscriptions, not all tags. Optional `X-Post-Id` is logging metadata only and never authorization. Per-IP connection limit remains 10, leaving headroom.

## Реализационное руководство

- `ring_buffer.py`: append/read-after/oldest operations with no FastAPI imports.
- `connection_manager.py`: register/unregister, subscription matching, per-client queues and coalesce map.
- `service.py`: `FanoutBridge` lifecycle, NOTIFY adapter, poll fallback, row-to-frame mapping.
- `protocol.py`/`models.py`: discriminated message validation for hello/subscribe/ack/value/event/ping/pong/error.
- `main.py` lifespan starts/stops bridge; shutdown cancels listener and poll tasks cleanly.
- No imports from collector runtime and no queue object passed across process boundary.

## Верификация

- WS example: hello, subscribe snapshot, ack, monotonic replay, ping/pong and unsubscribe.
- Resume test: after last cursor N, reconnect starts at N+1; an expired cursor emits `CURSOR_EXPIRED`.
- Slow-client test: two values for same tag collapse to latest, two events remain two frames; one slow connection cannot block another.
- NOTIFY test uses fake listener; fallback watermark test proves no duplicate cursor/frame.
- Property-based invariants: ring read-after returns strictly increasing cursors; replay excludes `<= resume`; eviction makes every cursor below oldest expired; coalesce output contains at most one unsent value per tag; event ordering is preserved.
- Six-connection load stub verifies all six remain responsive under bounded value fanout.

---

# CR-API-03 — Session tiles vs auth

**Блокирует:** s07 `session-b11`
**Тип:** Architecture + Algorithm
**AC:** AC-05, screen 6 contract; plan §§6.9–6.11, 12, 16.5

## Постановка

B11 — tile identity for a watchkeeper, not IAM. Need explicit lifecycle, audit events, cookie behavior and bounded timeout without introducing passwords, RBAC or a persistence migration in p1.

## Варианты

### Вариант A — process-local SessionService with one current session per person

- Roster is read-only source of active people.
- POST always accepts an active tile; a new login for the same person supersedes the old session.
- Other people may have concurrent sessions.
- Anonymous read routes remain allowed; session is preferred for reports.

**Плюсы:** matches tile UX, deterministic supersede, no auth subsystem, easy unit tests and explicit restart semantics.

**Минусы:** all sessions disappear on process restart and must be reselected.

### Вариант B — reject duplicate login

**Плюсы:** prevents concurrent same-person use.

**Минусы:** breaks tile retry after a lost browser cookie and contradicts p1 “double login allowed”. Rejected.

### Вариант C — persistent session table / IAM token

**Плюсы:** survives restart and supports stronger audit.

**Минусы:** expands p1 into auth/security scope, adds migration and token revocation policy. Deferred to p2.

## Решение

Выбран **вариант A**. “Double login allowed” означает, что второй POST не получает 409; он успешно создаёт новую session и атомарно supersedes previous session for that `person_id`. `session_ended(reason=superseded)` is emitted exactly once for the old state.

### Lifecycle invariants

- `API_SESSION_IDLE_SEC=28800` (8h); max duration = 12h, with `expires_at=min(started_at+12h, last_seen_at+idle_timeout)`.
- `touch` updates `last_seen_at` only for a valid current session and never extends the 12h hard cap.
- Background sweeper checks idle/max expiry at a bounded interval and emits `session_ended(reason=timeout)` once. Logout is idempotent and returns 204 even if cookie is absent/unknown.
- Session cookie is opaque UUID, `HttpOnly`, `SameSite=Lax`, `Path=/`; set on POST and deleted on DELETE. No bearer token is required for p1; if response keeps `token` for contract compatibility, it is the same opaque session identifier and is never a credential for IAM.
- Inactive or unknown roster person gives 400 validation error; roster response contains active tiles sorted by `tile_order`.
- `GET` routes work anonymously. `GET /api/reports/watch` uses current session when available and returns `watchkeeper=null` otherwise.
- Each B6 write goes through `EventWriterPort` with idempotency keys `session:{id}:started` and `session:{id}:ended`; no direct collector or APS mutation.
- On restart, memory is empty; stale cookies are treated as no session and do not resurrect identity.

## Реализационное руководство

- `SessionState` remains a small dataclass; `SessionService` owns map by session id and current-by-person index.
- Supersede and new state insertion are one critical-section operation; emit old ended event before/with new started event in deterministic order.
- Store only roster snapshot needed for response (`person_id`, `name`, `rank`, `default_screen`), not the whole YAML object.
- Inject clock and event writer ports so timeout and audit tests do not depend on wall clock or live DB.
- Avoid adding IAM, password, role authorization or session DB in this step.

## Верификация

- POST active tile returns 201, cookie and `session_started` payload.
- POST inactive/unknown tile returns 400 and writes no event.
- Second POST same person succeeds, invalidates old state and writes one supersede/ended event; different person remains independent.
- DELETE is idempotent and writes `session_ended` once for a live session; timeout sweeper does the same with reason `timeout`.
- Property-based lifecycle invariant: every emitted ended event references a started session, each session id has at most one ended event, and no expired session is returned as current.
- Restart/empty store test proves anonymous read behavior and stale cookie safety.

---

# CR-API-04 — Cursor format and resume ordering

**Блокирует:** s04 `events-rest`, s06 `ws-fanout`
**Тип:** Algorithm + Architecture
**AC:** AC-04; plan §§6.4, 7.2, 8, 16.3–16.4

## Постановка

REST events needs an opaque stable keyset cursor; WS needs a reconnect cursor that does not depend on database IDs or wall-clock uniqueness. Ordering must remain stable when events share timestamps.

## Варианты

### Вариант A — per-channel int64 WS cursor + REST base64url JSON `{ts,id}`

**Плюсы:** cheap comparison, independent values/events streams, deterministic REST tie-break, opaque wire representation without claiming cryptographic secrecy.

**Минусы:** cursor state is process-local for WS and resets after restart; REST cursor remains valid against stable event IDs/timestamps.

### Вариант B — ULID as universal cursor

**Плюсы:** globally sortable and can carry time.

**Минусы:** couples storage/event generation to ULID adoption, does not solve separate channel replay state, complicates existing event IDs. Deferred.

### Вариант C — database offset or raw `(ts,id)` in REST

**Плюсы:** implementation short.

**Минусы:** offset duplicates/skips under inserts; raw cursor leaks storage shape and allows ambiguous parsing. Rejected.

## Решение

Выбран **вариант A**.

### REST codec

- Logical key is `(event.ts, event.id)` sorted ascending. Query after cursor uses strict tuple comparison: `ts > cursor.ts OR (ts = cursor.ts AND id > cursor.id)`.
- Wire value is canonical base64url without padding over UTF-8 JSON `{"ts":"<UTC ISO8601>","id":"<event id>"}`. JSON keys are sorted and separators compact; decoder accepts no alternate semantic shapes.
- Cursor is opaque, not encrypted. Invalid base64, malformed JSON, non-UTC timestamp, missing fields or extra fields produce `400 INVALID_CURSOR` envelope; no stack trace.
- `next_cursor` is the last returned item; `has_more` is determined by fetching `limit+1`, never by guessing from page length. `limit` is clamped/validated to default 50, max 200.
- Event id is the stable final tie-break and must be unique in the events read model. No mutation endpoint for ack exists in p1.

### WS cursor

- `values` and `events` each have independent int64 counters owned by FanoutBridge and starting at 1 after process start.
- Cursor is assigned exactly once when a frame enters its channel ring. A DB row replayed by NOTIFY fallback is deduplicated before assignment.
- Subscribe accepts `resume_cursor` per channel. Replay emits only `cursor > N`; `N < oldest_available - 1` yields `CURSOR_EXPIRED` with `oldest_available` and refetch hint.
- Snapshot frames are explicitly outside cursor sequence; ack reports replay counts. Client must set its last cursor from replay/live frames, not snapshot.
- Cursor counters reset on API restart; hello exposes buffer capacities, while reconnect after restart must use fresh snapshot/refetch rather than assume old counter continuity.

## Реализационное руководство

- Keep REST `CursorCodec` independent from WS `RingBuffer`; same concept of ordering does not mean shared mutable state.
- SQL query receives decoded typed `datetime` and id as bound parameters.
- Use base64url helpers from stdlib; reject padding/alternate JSON if canonical contract is required, and never log full user cursor.
- Error code is stable (`INVALID_CURSOR`/`CURSOR_EXPIRED`), details contain channel/oldest only where applicable.

## Верификация

- Five-page seeded events test has no duplicate or skipped IDs, including equal timestamps.
- Round-trip property: `decode(encode(ts,id)) == (ts,id)` for valid UTC values; canonical encoding is idempotent.
- Ordering property: every page after cursor contains only keys strictly greater than cursor; malformed values never reach SQL.
- WS property: cursors increase by one for appended frames within a channel; replay after N starts at N+1 unless evicted; channels never compare each other’s cursor.

---

# CR-API-05 — Reports watch stub / screen 6

**Блокирует:** s08 `reports-watch`
**Тип:** Architecture + Algorithm + UI/UX
**AC:** AC-07 screen 6; plan §§6.7–6.8, 16.5, 18

## Постановка

Screen 6 needs a deterministic watch report while full B12 generation is out of scope. The API must expose alarms, protections, quality caveats and a small KPI snapshot in JSON and printable HTML without implying AI or silently ignoring quarantine.

## Варианты

### Вариант A — rule-based report service + shared JSON model + minimal HTML renderer

- Query events/series/read-only semantic state.
- Build one `WatchReportResponse`; HTML renders the same validated model.
- Verdict and highlights are deterministic rules.

**Плюсы:** JSON/HTML parity, reproducible tests, no generation state, no AI dependency, small surface for phase 1.

**Минусы:** wording is intentionally basic; richer narrative deferred to B12.

### Вариант B — template-only event dump

**Плюсы:** fastest implementation.

**Минусы:** no stable verdict/KPI contract, duplicates business logic in HTML, poor quarantine communication. Rejected.

### Вариант C — LLM/narrative report generation

**Плюсы:** natural-language summary.

**Минусы:** non-deterministic, unavailable/offline edge dependency, unacceptable for alarm audit and explicitly out of scope. Rejected.

## Решение

Выбран **вариант A**.

### Input and quality rules

- Required `from`/`to` are normalized UTC and use the same bounded window policy as history; `format=json|html`, default `json`.
- `data_quality.quarantine_tags` is the sorted unique tag set referenced by quarantined samples/events in the window. `stale_intervals` are merged overlapping/adjacent intervals; no invented normal values.
- `banner` is present whenever quarantine tags or stale intervals are non-empty: `Часть периода под сверкой — см. quarantine_tags`. Empty quality state uses `banner=null` or omitted only if schema marks it optional.
- `events_count` counts all selected events; `alarms_count` counts severity=`alarm`; `protections_count` counts canonical protection event names (`protection.*`, `trip.*`) from the events adapter. Nullable Q4 severity is not promoted to alarm by guessing.

### Verdict rules

Apply rules in this order:

1. Any protection/trip event → `Критический режим: зафиксированы срабатывания защит (N)`.
2. Else any alarm event → `Были тревоги: N`.
3. Else warning events → `Есть предупреждения: N`.
4. Else no warning/alarm/protection → `Тревог и срабатываний защит не зафиксировано`.
5. If `data_quality` is non-empty, append a short quality suffix (`Данные частично под сверкой`) and keep the structured banner as the authoritative UI flag. Verdict never claims “normal” when the interval has unresolved quarantine.

Rules are pure, localized strings are centralized constants, and counts remain structured fields for consumers.

### Debounce/grouping and highlights

- Group alarms/protections into one highlight when they share normalized `(event_name, asset_id, kks)` and their timestamps are within 60 seconds of the current group end. This reduces repeated edge events without changing `alarms_count`.
- Each group retains first/last timestamp, max severity, count and representative event id. No group crosses a different asset or KKS.
- Sort highlights by severity rank (protection > alarm > warning), then latest timestamp descending, then stable group key. Return at most five (`top 5`); counts in summary remain complete.
- A highlight contains safe display fields only: event name, asset, KKS, first/last timestamps, count, severity and representative id. Raw params remain structured/escaped, never interpreted as HTML.

### KPI tags and watchkeeper

- Return at most three `tags_snapshot` entries (`KPI_TAG_LIMIT=3`). Select tags referenced by protection/alarm highlights first, then tags with the highest sample count; tie-break by stable `tag_id`.
- Each entry has `tag_id`, name, avg/min/max and `quality_worst`; a quarantined tag remains quarantined in the snapshot.
- `watchkeeper` is built from the current session when a valid `session_id`/cookie exists; otherwise it is `null` (anonymous report is allowed). No roster mutation occurs.

### HTML scope

- Jinja template renders the already validated response; it does not query DB or recalculate verdict.
- Set `Content-Type: text/html; charset=utf-8`, include minimal print CSS, title, period, verdict, data-quality banner, highlights and KPI table.
- Escape all event/user/asset strings; no untrusted raw HTML and no PDF conversion. JSON and HTML must share the same generated model and `generated_at` value within one request.
- OpenAPI description states “prototype screen 6; full B12 phase 2”; it does not mention AI or imply report generation persistence.

## Реализационное руководство

- `ReportsService.list_types()` returns one `watch` type with `json` and `html` formats.
- `build_watch(from, to, session_id, format)` orchestrates read ports, pure verdict/grouping/KPI functions and response mapping.
- Keep report service read-only. Any future export/job state belongs to B12, not this endpoint.
- Test fixture should include alarms, protection, duplicate events within debounce window, quarantine sample, stale interval and no-session request.

## Верификация

- List stub has exact `watch` type and formats.
- JSON response validates `period`, `data_quality`, `summary.verdict`, `highlights` and `tags_snapshot`.
- HTML response has correct content type, escaped fixture strings and quarantine banner; it does not expose a PDF route.
- Rule tests cover protection precedence, alarm/warning/no-alarm branches, debounce boundary (59/60/61 seconds), top-five cap, deterministic KPI tie-break and anonymous watchkeeper.
- Property-based invariants: grouping never merges different asset/KKS; highlight count ≤5; KPI count ≤3; every quarantine/stale input is represented in data_quality; HTML rendering does not change structured verdict/counts.

---

## Batch closure checklist

- [x] CR-API-01: one deterministic time-bucket/envelope algorithm; bool/string last; gaps omitted; quarantine visible.
- [x] CR-API-02: NOTIFY bridge, poll fallback, per-channel buffers, value coalesce, event preservation and six-post limits.
- [x] CR-API-03: tile identity lifecycle, idle/max TTL, supersede, anonymous mode, cookie and append-only B6 audit.
- [x] CR-API-04: per-channel int64 WS cursor and opaque REST `{ts,id}` keyset cursor with strict ordering.
- [x] CR-API-05: deterministic report verdict, debounce grouping, top-five highlights, three KPI tags and shared HTML renderer.
- [x] All alternatives include pros/cons and a selected recommendation.
- [x] All recommendations preserve I1 read-only scope outside session audit, process boundaries and existing plan paths.
- [x] Downstream decompose shards and index rewired to this artifact; `needs_creative` closed.

**Next phase:** `BACK IMPLEMENT` @s03 (series/downsample).