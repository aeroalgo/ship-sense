# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-11 API versioning и integration contract

**Creative ID:** CR-P2-11  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [s20-integration-hard.yaml](../../plan/decompose-v1-p2-ship/s20-integration-hard.yaml)  
**Зависимый шаг:** [s20-integration-hard.yaml](../../plan/decompose-v1-p2-ship/s20-integration-hard.yaml)  
**Дата:** 2026-08-01  
**Режим:** BACK CREATIVE  
**Уровень:** L4  
**Типы решений:** Architecture + Algorithm  
**Статус:** closed

## Skills gate

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/architecture-patterns/SKILL.md`
- `.agents/skills/improve-codebase-architecture/SKILL.md`
- `.agents/skills/python-design-patterns/SKILL.md`
- `.agents/skills/websocket-engineer/SKILL.md`
- `.agents/skills/async-python-patterns/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture` — удержать глубокий контрактный seam между FastAPI transport, доменными envelope/schema и emulator/integration clients; не превращать тестовый E2E в копию реализации.
- `python-design-patterns` — применить KISS/SRP: один явный compatibility policy вместо generic version registry и скрытых fallback-веток.
- `websocket-engineer` — определить version/capability negotiation, reconnect cursor и bounded connection behavior для T10.
- `async-python-patterns` — зафиксировать cancellation, reconnect и независимые async flows без общего mutable state между шестью WS-клиентами.

## Контекст и цель

s20 закрывает последний технический шов v1-p2: emulator должен пройти через B12/B13/API/WS, T7 должен подтвердить rebrowse quarantine, T10 — шесть одновременных WS connections с reconnect cursor, а OpenAPI и exclusion greps должны доказать, что surface соответствует ship-pack без скрытого forwarder/ML/AI пути.

План уже задаёт ключевое решение: phase 2 остаётся additive на текущем `/api` surface; `/api/v2` резервируется только для breaking change. CR-P2-11 превращает это правило в проверяемый контракт:

1. текущий `/api` не получает префикс `/v1` и не меняется ради косметической «версии»;
2. additive endpoint/schema расширяется в том же namespace с сохранением старых operation IDs и envelope semantics;
3. breaking change не маскируется optional-полями или content negotiation, а получает отдельный `/api/v2` router и explicit migration note;
4. HTTP и WS используют один transport compatibility vocabulary, но не один слепой serializer;
5. emulator tests проверяют публичные контракты и observable outcomes, а не внутренние классы.

## Invariants и non-goals

### Обязательные инварианты

- `/api` — canonical v1-compatible public surface для текущего корабельного клиента.
- В phase 2 разрешены только additive изменения: новые paths, optional response fields, новые enum values только если existing clients fail-open по контракту, и новые WS channels/messages с неизвестными типами, которые клиент может игнорировать.
- Нельзя переименовывать существующий path, operationId, обязательное поле, error code или semantic meaning quality values в рамках `/api`.
- `/api/v2` не создаётся в s20: резервирование документируется, но пустой router и speculative registry не добавляются.
- OpenAPI — источник проверяемого HTTP surface; WS contract описывается отдельно в contract note и тестируется runtime-сценариями.
- Reconnect cursor является opaque per-channel integer cursor; клиент не вычисляет его арифметически и не смешивает cursors разных channels.
- При истёкшем cursor сервер сообщает stable `CURSOR_EXPIRED`/`oldest_available` и не выдаёт неполный replay как будто он полный.
- Ошибки конфигурации и неизвестные mnemo schemas fail closed: недопустимый канал не расширяет подписку молча.
- Тесты не требуют внешнего forwarder, sklearn, AI/ML inference или network dependency; emulator data остаётся deterministic.

### Не входит в CR

- Реализация новых endpoint handlers, schema classes или emulator fixtures — это BACK IMPLEMENT s20.
- Создание реального `/api/v2` surface до появления breaking requirement.
- Полная semantic versioning платформа, plugin registry, client SDK generator или schema registry service.
- Изменение доменных правил quarantine, stale, hysteresis, B12 formulas или B13 EWMA.

---

## Component A — HTTP namespace и правило совместимости

🎨🎨🎨 ENTERING CREATIVE PHASE: ARCHITECTURE  
**Decompose step:** [s20-integration-hard.yaml](../../plan/decompose-v1-p2-ship/s20-integration-hard.yaml)  
**Компонент:** HTTP API namespace/version policy  
**Требования и ограничения:** существующий app монтирует router под `settings.API_V1_STR == /api`; plan прямо требует phase-2 additive `/api` и reserve `/api/v2` only if breaking.

### Вариант A1 — сохранить `/api` как canonical additive namespace (рекомендуется)

**Решение:** новые s20 assertions и additive endpoints остаются под `/api`; operation IDs стабильны; breaking policy описывается в contract note, но v2 router не создаётся.

**Плюсы:**

- совпадает с уже работающим `FastAPI(... openapi_url="/api/openapi.json")` и текущим frontend/client contract;
- минимальный diff и отсутствие двойного registration surface;
- OpenAPI проверяет полный фактический surface, а не несуществующий v2 placeholder;
- rollback прост: новые additive tests и contract note можно удалить независимо.

**Минусы:**

- namespace не сообщает номер major в URL;
- при первом breaking change потребуется отдельная миграционная работа.

### Вариант A2 — немедленно переименовать `/api` в `/api/v1`

**Плюсы:**

- URL явно содержит major;
- будущая v2 routing policy выглядит привычнее.

**Минусы:**

- breaking change сама по себе, хотя phase 2 не содержит breaking requirement;
- ломает существующие paths, OpenAPI URL, tests и клиентов;
- порождает alias/redirect ambiguity и дублирует security/rate-limit surface;
- противоречит plan §11.10.

### Вариант A3 — content negotiation через `Accept`/`X-API-Version`

**Плюсы:**

- один path может обслуживать несколько representations;
- URL остаётся стабильным.

**Минусы:**

- OpenAPI path не выражает behavioral split полностью;
- proxy/cache/audit и websocket clients сложнее диагностировать;
- version branching становится implicit и легко пропустить в emulator tests;
- для ship-v1 это лишняя абстракция без второго representation.

**Рекомендуемый подход:** A1. В contract note явно написать: «`/api` — additive compatibility surface; `/api/v2` появляется только вместе с documented breaking decision и migration matrix». Не добавлять v2 router, alias или header switch в s20.

**Руководство по реализации:**

- оставить `settings.API_V1_STR` как `/api`;
- OpenAPI tests должны утверждать ожидаемые `/api/...` paths и отсутствие неожиданных `/api/v2/...` paths;
- новый endpoint добавляется через существующий `api_router`, с уникальным stable operation ID и tag;
- в s20 contract assertions проверяют, что mutation surface не расширен случайно;
- любой future v2 должен быть отдельным explicit router, а не условием внутри v1 handler.

**Верификация:** `test_openapi_p2_surface.py` проверяет additive list, stable IDs/tags, no v2 placeholder и no mutation leaks.

🎨🎨🎨 EXITING CREATIVE PHASE

## Component B — HTTP envelope, errors и additive schema evolution

🎨🎨🎨 ENTERING CREATIVE PHASE: ARCHITECTURE  
**Компонент:** response/error compatibility seam  
**Требования и ограничения:** существующие FastAPI handlers уже возвращают typed response models; OpenAPI должен отражать quarantine quality и запретить AI/ИИ wording.

### Вариант B1 — typed response models + stable error codes (рекомендуется)

**Решение:** каждый новый HTTP contract использует response model; error branch сохраняет machine-readable `code`, `message` и request context; новые поля optional, старые обязательные поля не меняются.

**Плюсы:**

- OpenAPI автоматически становится executable contract;
- stable code отделяет policy branching от human-readable text;
- T7 может проверять `quality=quarantine`/stale без парсинга сообщений;
- response models дают локальную test surface без запуска всей системы.

**Минусы:**

- при добавлении поля нужно поддерживать модель и fixture;
- stable codes требуют небольшого registry/списка в contract note.

### Вариант B2 — свободные `dict` envelopes и text-only errors

**Плюсы:** быстро добавлять поля и почти нет schema boilerplate.

**Минусы:**

- OpenAPI становится слабым и легко рассыпается при refactor;
- T7/T10 tests начинают зависеть от message strings;
- missing/quarantine/null ambiguity возвращается в client layer;
- error text может случайно содержать запрещённую продуктовую лексику.

### Вариант B3 — глобальный envelope `{data, error, meta}` для всей API

**Плюсы:** единообразный transport shape и единая pagination metadata.

**Минусы:**

- это breaking change для уже существующих typed responses;
- несоразмерно scope s20;
- смешивает domain response и transport metadata, усложняя stream/error parity.

**Рекомендуемый подход:** B1. Для additive evolution придерживаться правил:

- новые response properties — optional или имеют безопасное default значение;
- новые error codes — additive, старый HTTP status сохраняется;
- `quarantine` — отдельное enum value/quality state, не отсутствие записи;
- `null` используется только когда contract допускает неизвестное/невалидное значение, а `quality` объясняет причину;
- сообщения не являются API для ветвления и не содержат `AI`, `ИИ`, `sklearn`, `forwarder`.

**Руководство по реализации:** s20 добавляет schema-focused assertions, которые читают `components.schemas`, enum и examples, а не только список paths. Contract note перечисляет обязательные stable fields и допустимую additive evolution.

**Верификация:** OpenAPI test на schemas, stable error code assertions в T7, exclusion grep по OpenAPI descriptions и API messages.

🎨🎨🎨 EXITING CREATIVE PHASE

## Component C — WebSocket protocol/version negotiation

🎨🎨🎨 ENTERING CREATIVE PHASE: ARCHITECTURE  
**Компонент:** `/api/stream` WS protocol contract для T10 и reconnect cursor  
**Требования и ограничения:** текущий stream отправляет hello, ack, replay frames, cursor-expired frame; шесть клиентов должны подключаться независимо и корректно переподключаться.

### Вариант C1 — fixed protocol v1 + capability fields (рекомендуется)

**Решение:** WS endpoint остаётся `/api/stream`; hello содержит protocol marker и server buffer metadata; subscribe message использует существующие channels/tags/resume_cursor; неизвестные additive fields игнорируются, неизвестные обязательные actions получают stable error.

**Плюсы:**

- не ломает текущий browser/emulator protocol;
- capability metadata позволяет client-side guard без path duplication;
- reconnect semantics явно тестируются на одном endpoint;
- не требует отдельного websocket router или proxy mapping.

**Минусы:**

- major version не виден в URL;
- compatibility logic должна оставаться небольшой и явно ограниченной.

### Вариант C2 — отдельные `/api/ws/v1` и `/api/ws/v2`

**Плюсы:** major split виден в URL и deployment logs;
- breaking protocol можно развивать без conditional parser.

**Минусы:**

- текущий `/api/stream` уже является shipped surface;
- добавляет второй connection path и удваивает T10 matrix;
- не оправдан, пока нет breaking frame requirement.

### Вариант C3 — `Sec-WebSocket-Protocol` negotiation

**Плюсы:** стандартный handshake механизм;
- прокси и clients могут явно выбрать protocol token.

**Минусы:**

- сложнее для существующего FastAPI test client/emulator;
- negotiation failure происходит до JSON error envelope;
- capabilities и cursor semantics всё равно нужно документировать отдельно;
- для additive phase 2 создаёт больше states, чем покрывает.

**Рекомендуемый подход:** C1. Зафиксировать protocol token/marker как data contract, но не делать handshake-level major negotiation. `/api/v2` reserve относится к breaking HTTP/WS surface и не активируется в s20.

**Руководство по реализации:**

- hello: stable `type`, `protocol`, `buffer_size`, `server_ts`;
- subscribe: `subscription_id`, unique `channels`, optional `tags`, per-channel `resume_cursor`;
- ack: subscription ID, channels, replay counts и oldest available cursor;
- cursor expired: stable code, channel и oldest available; client решает full resync, сервер не притворяется, что replay complete;
- disconnect всегда очищает connection registry; reconnect не наследует subscriptions silently;
- T10 запускает шесть независимых clients, каждый с собственным cursor map и cancellation path.

**Верификация:** deterministic six-client test с reconnect, replay и cursor-expired branch; проверка no shared mutable cursor state.

🎨🎨🎨 EXITING CREATIVE PHASE

## Component D — Emulator/integration harness seam

🎨🎨🎨 ENTERING CREATIVE PHASE: ARCHITECTURE + ALGORITHM  
**Компонент:** deterministic emulator → API/engine/WS test boundary  
**Требования и ограничения:** s20 должен покрыть happy path warnings/reports, T7 rebrowse quarantine, T10 six posts, OpenAPI и exclusion greps без production forwarder или внешних сервисов.

### Вариант D1 — contract-first fixtures и black-box client (рекомендуется)

**Решение:** emulator seed/fixture создаёт наблюдаемые input events; HTTP client и WS clients проходят через публичные app routes; assertions проверяют response/event contracts и state transitions.

**Плюсы:**

- ловит wiring errors между routers, dependencies, engines и stream bridge;
- не закрепляет private implementation names;
- один fixture может использоваться в e2e, T7 и T10 с отдельными scenario phases;
- failure output указывает на transport/domain seam.

**Минусы:**

- setup тяжелее unit test;
- потребуется bounded cleanup между scenarios.

### Вариант D2 — прямой вызов service/engine и отдельные mocked transport tests

**Плюсы:** быстрее и проще диагностировать pure logic;
- меньше async connection orchestration.

**Минусы:** не доказывает включение router/dependency/stream integration;
- не покрывает OpenAPI route registration или reconnect behavior;
- создаёт ложное ощущение E2E green.

### Вариант D3 — внешний compose emulator с реальными network containers

**Плюсы:** ближе к deploy topology;
- можно дополнительно проверить network names и health checks.

**Минусы:** flaky DB/Redis/network dependencies;
- медленнее и не нужен для deterministic s20 acceptance;
- complicates local reproduction и скрывает domain failures behind infra noise.

**Рекомендуемый подход:** D1 как acceptance surface; pure service tests остаются supporting evidence, но не заменяют E2E. Emulator должен быть in-process или bounded test transport, с explicit fixture reset и no internet.

**Руководство по реализации:** разделить сценарии:

1. baseline report/warnings: seed fresh signals → generate/read API → assert stable envelope;
2. T7: browse tag → rename/remove tag → assert quarantine/stale/banner contract → restore/rebrowse and assert deterministic recovery;
3. T10: open six connections → subscribe distinct channels → publish/replay → disconnect/reconnect using each cursor map → assert ack/replay or cursor-expired branch;
4. OpenAPI/exclusion: inspect generated spec and source strings as separate deterministic checks.

**Верификация:** s20 tests isolate scenario data, use bounded timeouts, and never treat a missing frame or stale fixture as success.

🎨🎨🎨 EXITING CREATIVE PHASE

## Component E — compatibility matrix и breaking-change gate

🎨🎨🎨 ENTERING CREATIVE PHASE: ALGORITHM  
**Компонент:** decision table для будущих изменений  
**Требования и ограничения:** phase 2 не активирует v2, но INTEG должен получить executable note, чтобы future changes не обходили policy.

### Вариант E1 — explicit matrix в contract note (рекомендуется)

| Изменение | `/api` допустимо | Требуется `/api/v2` | Тест/действие |
|---|---:|---:|---|
| Новый GET path | да | нет | OpenAPI path assertion |
| Новый optional response field | да | нет | schema + old fixture assertion |
| Новый optional query parameter | да | нет | old request remains valid |
| Переименование path/operationId | нет | да | migration matrix + dual-run period |
| Удаление/переименование required field | нет | да | v2 schema + client migration |
| Меняется meaning существующего enum | нет | да | explicit semantic migration |
| Новая WS channel | да | нет | unknown channel behavior + T10 |
| Новое optional WS frame field | да | нет | old client ignores field |
| Изменение обязательного frame/action | нет | да | protocol migration and new path/token |
| Изменение cursor meaning/retention | нет | да | replay compatibility test |

**Плюсы:** executable, reviewable, directly maps to OpenAPI/WS tests.

### Вариант E2 — prose-only ADR

**Плюсы:** коротко и легко написать.

**Минусы:** ambiguity при review; невозможно автоматически сопоставить изменение с expected test; future implementer может трактовать «breaking» иначе.

### Вариант E3 — runtime version registry/config

**Плюсы:** policy можно переключать конфигурацией.

**Минусы:** premature abstraction, hidden behavior, config drift и сложный OpenAPI generation; registry не нужен при одной активной compatibility line.

**Рекомендуемый подход:** E1. Contract note должен содержать matrix, stable vocabulary, endpoint/WS inventory, test commands и explicit «v2 not active» statement.

**Верификация:** reviewer сличает matrix с s20 tests и OpenAPI diff; отсутствие v2 при additive scope — pass, а не missing feature.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Канонический контракт для s20 IMPLEMENT

### HTTP

- Namespace: `/api`; docs `/api/docs`, redoc `/api/redoc`, spec `/api/openapi.json`.
- Version policy: additive only in phase 2; `/api/v2` reserved, not mounted.
- Stable operation IDs/tags for existing paths; no accidental mutation endpoints except explicitly approved session mutations.
- Typed response schemas; quality values preserve `fresh|stale|quarantine` semantics where applicable.
- Error branching uses stable machine codes, not message matching.
- OpenAPI descriptions and API messages exclude `AI`, `ИИ`, `sklearn`, `forwarder` and equivalent prohibited paths.

### WebSocket

- Endpoint remains `/api/stream`.
- Six simultaneous connections are independent; each has per-channel cursor map and cleanup on disconnect.
- Subscribe/replay ack includes requested channels, replay counts and oldest available cursors.
- Expired cursor produces explicit cursor-expired frame; no silent partial replay.
- Reconnect starts from client-held cursor; no server-side assumption that a disconnected subscription persists.
- Unknown additive frame fields are ignorable; unknown required actions fail with stable error.

### T7

- Tag removal/rename cannot silently produce a fresh value.
- Quarantine is observable in quality/state contract and survives API projection.
- Rebrowse after restore is deterministic and does not reuse stale cached binding without validation.
- Banner/status assertion uses stable state/code, never a localized message substring.

### Exclusion and OpenAPI

- Source grep and generated spec grep are separate checks.
- A passing exclusion test means forbidden implementation strings are absent from the approved surface; it does not assert that unrelated documentation is clean.
- OpenAPI expected set is exact for the phase-2 contract, with explicit additive entries documented in the integration note.

## Сценарий реализации по eNN-equivalent acceptance slices

s20 остаётся одним BACK IMPLEMENT шагом, но внутри него порядок проверок такой:

1. Freeze expected OpenAPI path/operation/tag/schema inventory before implementation changes.
2. Build deterministic emulator fixture and happy-path report/warning scenario.
3. Add T7 quarantine matrix: missing, renamed, restored, stale and fresh transitions.
4. Add T10 six-connection matrix: initial hello, subscriptions, publish/replay, disconnect, reconnect, cursor expiry.
5. Add exclusion scans for forbidden product/implementation strings.
6. Write `integration/contracts/b10-phase2.md` from this CR, including matrix and explicit no-v2 decision.
7. Run targeted pytest and inspect failures by contract seam; do not relax assertions to hide missing wiring.

## Failure policy

- Missing route, wrong operation ID/tag, wrong schema enum or unexpected mutation is a hard failure.
- Unknown mnemo binding, invalid tag or absent cursor data is fail-closed; no synthetic fresh value.
- Timeout, disconnect or cancelled WS task fails the affected T10 client and is reported; it cannot be counted as one of six successful posts.
- Cursor expiry is an expected explicit branch only when the server sends the cursor-expired contract; silent empty replay is failure.
- Forbidden string found in generated OpenAPI or API error descriptions fails the exclusion test.
- If a requirement is genuinely breaking, stop additive implementation and open a new v2 design/plan; do not encode an unreviewed compatibility exception in s20.

## Rewire

- [x] s20: `needs_creative: yes (CR-P2-11) — **closed**`; `Next Phase: BACK IMPLEMENT`; clickable link points to this artifact.
- [x] decompose index: CR-P2-11 marked ✅; s20 column is `yes (CR-P2-11) ✅`; next phase is `BACK IMPLEMENT`.
- [x] queue snapshot: next command is `BACK IMPLEMENT @s20`; no open creative remains for s20.

## Verification checklist

- [x] Один epic-scoped creative-файл создан в `memory-bank/back/creative/v1-p2-ship/`.
- [x] Skills gate содержит 2 core и 4 situational skills из allowlist; вне списка skills не использовались.
- [x] CR-P2-11 классифицирован как Architecture + Algorithm.
- [x] Для namespace, envelope, WS protocol, emulator seam и compatibility matrix предложены минимум 2 варианта с pros/cons.
- [x] Зафиксирован additive `/api` policy и explicit reserve `/api/v2` only for breaking changes.
- [x] Зафиксированы stable HTTP/WS contracts, T7 quarantine semantics и T10 six-client reconnect cursor.
- [x] Зафиксированы fail-closed/error/exclusion rules без fallback, который скрывает причину.
- [x] s20 и decompose index rewired на закрытый CR-P2-11.

## Handoff

- **Done:** BACK CREATIVE CR-P2-11 — API namespace/version policy, typed compatibility, WS reconnect contract, emulator seam, T7/T10 acceptance matrix.
- **Artifact:** [creative-api-versioning.md](creative-api-versioning.md); rewired [s20-integration-hard.yaml](../../plan/decompose-v1-p2-ship/s20-integration-hard.yaml) и [decompose index](../../plan/decompose-v1-p2-ship/index.md).
- **Next:** `BACK IMPLEMENT @s20`.
- **code_changed:** no.
- **New chat:** yes — один чат = один atomic subtask.

🎨🎨🎨 EXITING CREATIVE PHASE
