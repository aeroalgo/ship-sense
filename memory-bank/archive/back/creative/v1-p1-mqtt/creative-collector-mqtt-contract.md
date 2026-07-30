# CR-COL-05 — MQTT payload contract, topic taxonomy, broker topology, threshold tagging

**Creative ID:** CR-COL-05  
**Task:** T-008 v1-p1-mqtt  
**Plan:** [plan-v1-p1-mqtt.md](../../plan/plan-v1-p1-mqtt.md) (§4–§5, §12, ADR-T008-001..005)  
**Зависимые шаги:** [s03](../../plan/decompose-v1-p1-mqtt/s03-mqtt-payload-models.md), [s04](../../plan/decompose-v1-p1-mqtt/s04-mqtt-lifecycle-tracker.md), [s05](../../plan/decompose-v1-p1-mqtt/s05-mqtt-semantic-mapper.md), [s06](../../plan/decompose-v1-p1-mqtt/s06-mqtt-connector.md), [s10](../../plan/decompose-v1-p1-mqtt/s10-normalizer-mqtt-bridge.md)  
**Soft dependents:** [s08](../../plan/decompose-v1-p1-mqtt/s08-emulator-mqtt-publisher.md), [s09](../../plan/decompose-v1-p1-mqtt/s09-integration-mqtt.md) — topic/payload канон из этого файла  
**Дата:** 2026-07-27  
**Режим:** BACK CREATIVE  
**Уровень:** L4 (T-008)  
**Статус:** approved (proposal до ответа Канонерки §12; `schema_version` + migration path)

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `architecture-patterns` | plugin adapter B1, separation transport/semantic |
| `brainstorming` | broker/threshold/routing trade-offs |
| `property-based-testing` | idempotency + lifecycle transition invariants |

---

## 1. Резюме решений (ADR bundle)

| # | Тема | Решение | ADR |
|---|------|---------|-----|
| D1 | Topic taxonomy | `shipsense/v1/{panel}/{kind}/{channel_id}` — **topic primary** для routing; payload `@type` — зеркало для валидации | ADR-COL-05-01 |
| D2 | Broker topology prod | **Edge ShipSense** — Mosquitto sidecar; панели publish inbound на LAN2 | ADR-COL-05-02 |
| D3 | Broker topology dev | Compose `mosquitto:1883`, plain MQTT | ADR-COL-05-02 |
| D4 | Threshold exposure | **Отдельные pseudo-tags** `{tag_id}.{suffix}` → отдельные `RawSample` / `TelemetrySample` | ADR-COL-05-03 |
| D5 | Lifecycle | Kanoner enum → **native** `params.lifecycle` + `params.kanoner_state`; без схлопывания `returned_unacked`/`blocked` | ADR-COL-05-04 |
| D6 | First observation | **Silent seed** — Event только на transition, не на первом сообщении | ADR-COL-05-05 |
| D7 | Idempotency | `{source_id}:{channel_id}:{lifecycle}:{source_ts_iso}` | ADR-COL-05-06 |
| D8 | channel_test_enabled | `quality=uncertain`, `params.test_mode=true`; lifecycle Events **не подавлять** | ADR-COL-05-07 |
| D9 | EGT | **One message per engine**; mapper → 12+ N cylinder `RawSample` | ADR-COL-05-08 |
| D10 | Schema evolution | Обязательное поле `schema_version: "1.0"`; неизвестная major → quarantine + metric | ADR-COL-05-09 |

**Open для Канонерки (не блокирует IMPLEMENT proposal):** broker IP/TLS/certs, retain/LWT policy, publish frequency (1 Hz vs on-change), exact `channel_id` ↔ KKS table delivery format.

---

## 2. Компоненты и creative phases

---

### 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

**Decompose step:** [s03-mqtt-payload-models.md](../../plan/decompose-v1-p1-mqtt/s03-mqtt-payload-models.md), [s06-mqtt-connector.md](../../plan/decompose-v1-p1-mqtt/s06-mqtt-connector.md)

**Компонент:** Topic taxonomy + message routing

**Требования и ограничения:**

- Две панели (APS, GEU) — разделение на уровне `panel` в topic и `source_id` в collector (`panel_aps`, `panel_geu`).
- Subscribe-only collector (I1); topic filter из `topic_prefix` в config.
- 4 логических типа сообщений (plan §4.2): analog, discrete, logical event, exhaust gas group.
- Должно работать в I3 emulator (s08) без Modbus-претензий (CR-COL-03 transport separation).
- Malformed/unknown routing → `MqttParseError`, connector alive.

#### Вариант 1 — Topic-only routing (suffix = kind + channel_id)

```
shipsense/v1/aps/analog/APS.TAI4101
shipsense/v1/geu/discrete/GEU.DI2201
shipsense/v1/aps/event/APS.EV0101
shipsense/v1/geu/egt/GEU.EGT1
```

**Плюсы:** стандартный MQTT pattern; cheap routing без JSON parse; ACL per panel/kind; emulator mirrors prod.

**Минусы:** channel_id дублируется в topic и payload; rename channel = new topic.

#### Вариант 2 — Flat topic + payload `@type` only

```
shipsense/v1/aps/channels/APS.TAI4101   + JSON { "@type": "analog", ... }
```

**Плюсы:** один topic tree; меньше subscribe filters.

**Минусы:** routing после full JSON parse; сложнее ACL; выше latency on_message.

#### Вариант 3 — Hybrid (выбран): topic = panel + kind + channel_id; payload `@type` mirror + validate

Topic определяет union member **до** pydantic; `@type` в JSON должен совпадать с kind из topic, иначе `MqttParseError` (`type_topic_mismatch`).

**Плюсы:** быстрый routing + contract self-check; JSON Schema export для Канонерки с discriminated union; I3/E2E deterministic fixtures.

**Минусы:** дублирование `@type` и path — приемлемо для промышленного контракта.

**Рекомендуемый подход:** **Вариант 3 (Hybrid)** — ADR-COL-05-01.

**Руководство по реализации:**

```text
parse_mqtt_payload(topic, data):
  1. split topic → (prefix, version, panel, kind, channel_id_from_topic)
  2. assert version == "v1" (else ParseError unsupported_version)
  3. map kind → expected @type enum
  4. pydantic validate data against typed model
  5. if data.channel_id != channel_id_from_topic → ParseError channel_mismatch
  6. if data["@type"] != expected → ParseError type_topic_mismatch
```

**Subscribe filters (per source):**

| source_id | topic_prefix (config) |
|-----------|----------------------|
| panel_aps | `shipsense/v1/aps/#` |
| panel_geu | `shipsense/v1/geu/#` |

**Верификация:**

- golden fixtures: 4 kinds × 1 channel each parse correctly
- topic/payload `@type` mismatch → explicit error path
- unknown kind segment → ParseError

🎨🎨🎨 EXITING CREATIVE PHASE

---

### 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

**Decompose step:** [s06-mqtt-connector.md](../../plan/decompose-v1-p1-mqtt/s06-mqtt-connector.md)

**Компонент:** Broker placement topology

**Требования и ограничения:**

- LAN2 Ethernet, две панели Weintek publish.
- Collector read-only; ACL контроль на edge предпочтителен (I1).
- Dev без живых панелей — compose mosquitto.
- Prod TLS slot (certs TBD) — config-ready, не блокирует plain dev.

#### Вариант A — Broker на edge ShipSense (sidecar Mosquitto)

Панели → `mqtt://<edge-lan2-ip>:1883` (или TLS 8883).

**Плюсы:** один endpoint для collector; централизованный ACL; мониторинг; соответствует plan §5.4 recommendation.

**Минусы:** firewall panel→edge; SPOF broker (mitigate: systemd restart + health).

#### Вариант B — Broker на каждой панели

Collector → 2 connections `panel_aps_host:port`, `panel_geu_host:port`.

**Плюсы:** проще для Канонерки (embedded broker).

**Минусы:** 2 TLS handshakes; 2 health streams; asymmetric config.

#### Вариант C — Broker на одной панели, relay второй

**Плюсы:** один collector endpoint.

**Минусы:** SPOF; relay logic на панели — вне нашего контроля.

**Рекомендуемый подход:** **Вариант A prod** + **compose Mosquitto dev** — ADR-COL-05-02.

**Руководство по реализации:**

| Profile | broker host | notes |
|---------|-------------|-------|
| dev compose | `mosquitto:1883` | `COLLECTOR_SOURCES_PROTOCOL=mqtt`, profile `mqtt-dev` (s12) |
| prod proposal | `${MQTT_BROKER_HOST}` on edge LAN2 | письмо Канонерке §12 п.1 |
| fallback doc | B documented in README | если Канонерка настаивает на panel-side broker |

- QoS default **1** (at least once); duplicate → idempotency (D7).
- Retain **false** для telemetry stream (proposal); если Канонерка использует retain — connector logs `retained=true` metric, still process.
- LWT — optional per panel; не блокирует v1.

**Верификация:** integration s09 testcontainer uses variant A topology (single broker, two publishers).

🎨🎨🎨 EXITING CREATIVE PHASE

---

### 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

**Decompose step:** [s05-mqtt-semantic-mapper.md](../../plan/decompose-v1-p1-mqtt/s05-mqtt-semantic-mapper.md), [s10-normalizer-mqtt-bridge.md](../../plan/decompose-v1-p1-mqtt/s10-normalizer-mqtt-bridge.md)

**Компонент:** Threshold tagging strategy (analog VVU/VU/NU/NNU)

**Требования и ограничения:**

- AC-MQTT-11: thresholds доступны downstream (T-003 `/api/setpoints`, T-004 trend lines).
- Один MQTT message несёт value + 4 порога + 4 control_enabled flags.
- Normalizer остаётся dumb — mapper выдаёт scalar `raw_value` где возможно (plan ADR-T008-002).
- Совместимость с существующим setpoints API (отдельные tag rows, не JSON blob only).

#### Вариант 1 — Separate pseudo-tags (отдельные RawSample per threshold)

Primary: `tag_id=TAI4101`, value=process value.

Thresholds (if `map.thresholds.expose: true`):

| suffix | native_id | tag_id | raw_value |
|--------|-----------|--------|-----------|
| VVU | `{channel_id}#VVU` | `TAI4101.VVU` | threshold_vvu |
| VU | `{channel_id}#VU` | `TAI4101.VU` | threshold_vu |
| NU | `{channel_id}#NU` | `TAI4101.NU` | threshold_nu |
| NNU | `{channel_id}#NNU` | `TAI4101.NNU` | threshold_nnu |

`control_enabled` ×4 → `params` on each threshold sample: `{ "control_enabled": bool }` or single metadata Event — **store on value sample** `params.threshold_control: { vvu: bool, vu: bool, nu: bool, nnu: bool }`.

**Плюсы:** `/api/setpoints` reads like Modbus path; trend overlay per tag; writer hypertable uniform.

**Минусы:** 5× samples per analog message (throughput ~5× for analogs); yaml map needs threshold suffix entries or convention in mapper.

#### Вариант 2 — Metadata-only on primary sample

`raw_value=float`, thresholds in `RawSample` extension — **нет** в текущей модели без schema change.

**Плюсы:** 1 sample per message.

**Минусы:** ломает setpoints API contract; T-004 needs new metadata path; writer/API rework.

#### Вариант 3 — Hybrid JSON sidecar tag

One pseudo-tag `{tag_id}.__thresholds` with dict raw_value.

**Плюсы:** one extra sample not four.

**Минусы:** API/UI must special-case; worse than V1 for trends.

**Рекомендуемый подход:** **Вариант 1 — separate pseudo-tags** — ADR-COL-05-03.

**Руководство по реализации:**

- `maps/mqtt_channels_*.yaml`: primary entry + optional `thresholds.expose: true` auto-generates 4 sibling tag_ids by convention `{tag_id}.{VVU|VU|NU|NNU}` without 4 extra yaml rows (mapper convention).
- Unknown channel_id → quarantine sample (`quality=quarantine`, reason `unknown_channel`) — FR-B-MQTT-11.
- Unit on threshold samples = same as primary unit (°C, bar, etc.).

**Верификация:**

- analog fixture → 1 value + 4 threshold samples when expose=true
- expose=false → value only
- setpoints API can query `TAI4101.VVU` independently (T-003 downstream)

🎨🎨🎨 EXITING CREATIVE PHASE

---

### 🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm

**Decompose step:** [s04-mqtt-lifecycle-tracker.md](../../plan/decompose-v1-p1-mqtt/s04-mqtt-lifecycle-tracker.md)

**Компонент:** Lifecycle enum mapping (Q4-A native)

**Требования и ограничения:**

- AC-MQTT-12: ровно один Event на transition.
- AC-MQTT-13: `params.reconstructed = false`.
- AC-MQTT-21: `returned_unacked`, `blocked` distinct — не map в generic `cleared`/`active`.
- CR-UI-03 lamp grammar consumes `lifecycle` display values.
- Storage Q4-A: native lifecycle strings preserved.

#### Вариант 1 — Collapse to 3-state (active/acked/cleared)

**Плюсы:** matches minimal CR-UI-03 doc table.

**Минусы:** loses Kanoner semantics; violates AC-MQTT-21; wrong journal UX.

#### Вариант 2 — Passthrough native Kanoner codes as lifecycle (выбран)

Store both:

- `params.lifecycle` — **canonical extended** (same string as Kanoner enum where applicable)
- `params.kanoner_state` — raw enum value (redundant but audit-friendly)
- `params.reconstructed: false`

#### Вариант 3 — Map to internal FSM then re-export

**Плюсы:** uniform internal model.

**Минусы:** extra layer; risk of collapse bugs.

**Рекомендуемый подход:** **Вариант 2 — passthrough extended lifecycle** — ADR-COL-05-04.

**Mapping tables (normative for IMPLEMENT):**

**Analog (`AnalogApsState` → Event):**

| Kanoner `aps_state` | `params.lifecycle` | `event_name` (on enter) | severity |
|---------------------|-------------------|-------------------------|----------|
| `normal` | `cleared` | `aps.threshold.cleared` | info |
| `exceeded_unacked` | `active` | `aps.threshold.exceeded` | alarm |
| `returned_unacked` | `returned_unacked` | `aps.threshold.returned_unacked` | warning |
| `exceeded_acked` | `active_acked` | `aps.threshold.exceeded_acked` | warning |
| `blocked` | `suppressed` | `aps.threshold.blocked` | info |

**Discrete (`DiscreteApsState`):**

| Kanoner | `params.lifecycle` | `event_name` |
|---------|-------------------|--------------|
| `normal` | `cleared` | `aps.discrete.cleared` |
| `active_unacked` | `active` | `aps.discrete.active` |
| `passive_unacked` | `returned_unacked` | `aps.discrete.passive_unacked` |
| `active_acked` | `active_acked` | `aps.discrete.active_acked` |
| `blocked` | `suppressed` | `aps.discrete.blocked` |

**Logical event (`LogicalEventState`):**

| Kanoner | `params.lifecycle` | `event_name` |
|---------|-------------------|--------------|
| `disabled` | `cleared` | `aps.event.disabled` |
| `enabled` | `active` | `aps.event.enabled` |
| `blocked` | `suppressed` | `aps.event.blocked` |

**First observation:** **silent seed** (ADR-COL-05-05) — `observe()` stores state, returns `None`. No synthetic "initial" Event.

**Duplicate state:** return `None`.

**Idempotency key:** `{source_id}:{channel_id}:{params.lifecycle}:{source_ts.isoformat()}` — ADR-COL-05-06.

**channel_test_enabled=true:** still emit lifecycle Events; add `params.test_mode=true`; value samples get `quality=uncertain` via mapper/QualityEngine path — ADR-COL-05-07.

**Верификация:**

- property: sequence of repeated states → 0 events
- transition table spot checks per kind
- `returned_unacked` ≠ `cleared` in stored params

🎨🎨🎨 EXITING CREATIVE PHASE

---

### 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

**Decompose step:** [s03-mqtt-payload-models.md](../../plan/decompose-v1-p1-mqtt/s03-mqtt-payload-models.md)

**Компонент:** JSON payload schema (field names, types, versioning)

**Требования и ограничения:**

- Pydantic v2 models in s03; golden fixtures for s09.
- Export JSON Schema file for Kanoner (`docs/contracts/mqtt-kanoner-v1.schema.json` — create in s03 or s07).
- Timestamp timezone-aware UTC.

#### Вариант 1 — Russian field names from Kanoner docs

**Плюсы:** literal match to panel export.

**Минусы:** code/JSON inconsistency; harder OSS maintenance.

#### Вариант 2 — English snake_case canonical (выбран)

Align with plan §4.2 proposal; Kanoner doc mapping table in schema `description`.

#### Вариант 3 — Single blob `data` opaque dict

**Плюсы:** flexible.

**Минусы:** no validation; defeats T-008 purpose.

**Рекомендуемый подход:** **Вариант 2** + **`schema_version: "1.0"`** mandatory — ADR-COL-05-09.

**Common envelope (all kinds):**

```json
{
  "@type": "analog",
  "schema_version": "1.0",
  "channel_id": "APS.TAI4101",
  "source_ts": "2026-07-27T12:00:00.000Z"
}
```

**AnalogChannelPayload fields:**

| Field | Type | Required |
|-------|------|----------|
| value | number | yes |
| threshold_vvu, threshold_vu, threshold_nu, threshold_nnu | number | yes |
| control_vvu, control_vu, control_nu, control_nnu | boolean | yes |
| aps_state | enum AnalogApsState | yes |
| channel_test_enabled | boolean | yes (default false) |

**DiscreteChannelPayload:** `aps_state`, `input_active`, `channel_test_enabled`, envelope fields.

**LogicalEventPayload:** `event_state`, `input_active`, `channel_test_enabled`, envelope fields.

**ExhaustGasGroupPayload (ADR-COL-05-08 — one message per engine):**

| Field | Type |
|-------|------|
| engine_id | string (e.g. `GEU.EGT1`) — also topic channel_id |
| cylinder_deviation | number[12] |
| engine_mean_temp | number |
| max_allowed_deviation | number |
| operator_min_mean, operator_max_mean | number |
| operator_max_dev_at_min_mean, operator_max_dev_at_max_mean | number |
| cylinder_correction | number[12] |
| aps_permission | boolean[12] |

Mapper emits:

- per-cylinder deviation: `tag_id` from map `{engine_kks}.CYL{n}.DEV`
- mean: `{engine_kks}.MEAN`
- corrections/permissions: suffix convention `.CORR{n}`, `.APS_PERM{n}` when mapped

Stub map in s07 aligns with `tags_stub.yaml` GEU subset.

**Enum codes (wire format, string):**

```text
AnalogApsState: normal | exceeded_unacked | returned_unacked | exceeded_acked | blocked
DiscreteApsState: normal | active_unacked | passive_unacked | active_acked | blocked
LogicalEventState: disabled | enabled | blocked
```

**Верификация:** pydantic strict; invalid enum → MqttParseError; unknown schema_version major → quarantine path.

🎨🎨🎨 EXITING CREATIVE PHASE

---

### 🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm

**Decompose step:** [s10-normalizer-mqtt-bridge.md](../../plan/decompose-v1-p1-mqtt/s10-normalizer-mqtt-bridge.md)

**Компонент:** Normalizer / EventDetector bypass for mqtt tags

**Требования и ограничения:**

- Modbus/OPC EventDetector unchanged (regression).
- MQTT Events pre-built in mapper/tracker with `reconstructed=false`.
- Dedup by idempotency_key (R-M4).

#### Вариант 1 — Tag map flag `skip_event_detector: true` + parallel Event queue

**Плюсы:** explicit; matches s10 lean interface.

**Минусы:** two paths in normalizer.

#### Вариант 2 — Protocol-based auto-skip in normalizer

**Плюсы:** no yaml flag.

**Минусы:** implicit magic.

**Рекомендуемый подход:** **Вариант 1** — `TagMapEntry.skip_event_detector: true` for all mqtt-mapped tags; set automatically when loading mqtt channel maps.

Events flow: mapper → dedicated `events_queue` or callback `write_event` (align T-001 s05 pattern in IMPLEMENT).

Normalizer: mqtt scalar samples through existing QualityEngine; **no flip reconstruction**.

**Верификация:** modbus sample still generates reconstructed events in tests; mqtt does not.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## 3. JSON Schema export (proposal artifact for Kanoner)

Path (IMPLEMENT s03): `docs/contracts/mqtt-kanoner-v1.schema.json`

Root: `$id: https://shipsense.local/schemas/mqtt/v1`  
Discriminator: `@type` ∈ `analog | discrete | event | egt`

Minimum example analog fixture path: `apps/edge/collector/tests/fixtures/mqtt/analog_tai4101.json`

---

## 4. Config contract (delta to plan §7)

No change to `sources.yaml` shape; add documented defaults:

```yaml
subscribe:
  topic_prefix: "shipsense/v1/aps/#"
  qos: 1
options:
  publish_allowed: false
  schema_version_expected: "1.0"
```

---

## 5. I3 emulator alignment (CR-COL-05b scope note)

Full fidelity scenarios — optional CR-COL-05b; **minimum for s08:**

- Publish same topic taxonomy and JSON envelope as §2–§3.
- Deterministic lifecycle transitions in ScenarioRunner hook post-s18.
- Do not encode Modbus registers in MQTT payload.

---

## 6. Risks residual

| ID | Mitigation |
|----|------------|
| R-M1 Schema change by Kanoner | `schema_version`; minor additive fields ignored if optional |
| R-M2 Broker placement | proposal A + documented B fallback |
| R-M5 Threshold tags | ADR-COL-05-03 closed |
| R-M7 TLS late | config slots in s01; dev plain |

---

## 7. Follow-up Канонерке (unchanged from plan §12)

Отправить JSON Schema + topic tree §2 + broker proposal A. Ответы могут increment `schema_version` to 1.1 without rewiring architecture.

---

## 8. IMPLEMENT guidance per step

| Step | Action |
|------|--------|
| s03 | pydantic models + parse_mqtt_payload + fixtures per §3 |
| s04 | mapping tables §2 lifecycle + silent seed + idempotency |
| s05 | pseudo-tags §2 thresholds + EGT expansion + quarantine |
| s06 | subscribe `shipsense/v1/{panel}/#`, pipeline parse→map |
| s10 | skip_event_detector flag + event passthrough |
| s08 | publisher uses this topic/JSON canon |

---

## Handoff

- **Done:** BACK CREATIVE CR-COL-05 — MQTT contract proposal: topic taxonomy hybrid, broker edge-side prod, pseudo-tag thresholds, native lifecycle passthrough, silent seed, schema v1.0, EGT one-message-per-engine.
- **Files:** `memory-bank/back/creative/v1-p1-mqtt/creative-collector-mqtt-contract.md`; rewire s03–s06, s10 + decompose index.
- **Next:** `BACK IMPLEMENT s01` (mqtt config scaffold) — можно параллельно; затем s02 → s03..s06 по порядку index.
- **Tool / model:** Claude Code + premium-coding для s03–s06 semantic stack; Cursor + fast-editing для s01/s02/s07.
- **New chat:** yes — one chat = one IMPLEMENT substep.
