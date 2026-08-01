# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-01, CR-P2-02, CR-P2-04

**Creative IDs:** CR-P2-01 · CR-P2-02 · CR-P2-04  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [decompose-v1-p2-ship/index.md](../../plan/decompose-v1-p2-ship/index.md)  
**Дата:** 2026-07-31  
**Режим:** BACK CREATIVE  
**Уровень:** L4  
**Статус:** closed для CR-P2-01/02/04; CR-P2-10 и CR-P2-12 остаются отдельными gates OTA

## Skills gate

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/architecture-patterns/SKILL.md`
- `.agents/skills/improve-codebase-architecture/SKILL.md`
- `.agents/skills/python-design-patterns/SKILL.md`
- `.agents/skills/property-based-testing/SKILL.md`
- `.agents/skills/clean-ddd-hexagonal/SKILL.md`
- `.agents/skills/async-python-patterns/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture` — проверить глубину seams между транспортом, доменными правилами и инфраструктурой, не вводя декоративные слои.
- `python-design-patterns` — удержать решения KISS/SRP и не построить универсальные factory/registry до появления второго реального адаптера.
- `property-based-testing` — Modbus parser и численные формулы имеют большие пространства входов, где fixture-only тесты пропустят граничные случаи.
- `clean-ddd-hexagonal` — выделить порты gateway/OTA/formula loader так, чтобы use-case и pure domain код не зависели от Docker, bootloader, SQLAlchemy или FastAPI.
- `async-python-patterns` — сетевой gateway и асинхронная генерация отчётов должны не блокировать collector/hot path; OTA health probes должны иметь timeout и явную отмену.

---

## Общий architectural baseline

Все три решения используют одну и ту же зависимость:

```text
transport / process adapter
        ↓
application policy (сценарий и переход состояния)
        ↓
pure domain rules + typed value objects
        ↓
ports (Protocol)
        ↓
infrastructure adapters (socket, filesystem, DB, bootloader, logger)
```

Нижние pure rules не импортируют FastAPI, SQLAlchemy, Docker SDK, RAUC CLI или конкретный Modbus/OPC клиент. Adapter имеет одну ответственность: перевести внешний протокол в typed input/output и вернуть typed error. Отдельный orchestration layer не добавляем: если use-case остаётся тонким вызовом одного порта, он не даёт глубины и удаляется.

Общие инварианты:

1. **Fail closed:** неизвестная операция, отсутствующий health signal, невалидная подпись, незавершённый frame или неоднозначный formula method не превращаются в разрешение.
2. **Explicit provenance:** rejected write, rollback reason, source method, gap и config/formula version записываются как данные, а не прячутся в строке лога.
3. **Additive contracts:** текущие API и storage paths сохраняются; новые поля добавляются без breaking alias.
4. **One source of truth:** policy находится в typed config/ship-pack; transport не дублирует бизнес-правила.
5. **Bounded I/O:** socket read, health probe, DB check и external command имеют timeout; отмена async task не проглатывается.

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture — CR-P2-01 I1 read-only gateway

**Decompose step:** [s01-i1-gateway.md](../../plan/decompose-v1-p2-ship/s01-i1-gateway.md)  
**Дополнительный consumer:** s15 proof artifact.  
**Компонент:** production barrier перед АПС: Modbus filtering gateway с возможностью позже подключить OPC UA read-only adapter.  
**Требования и ограничения:** I1-F1..F6, T4, FC 01–04 only, TCP fragmentation/pipelining, rejected-write log, отсутствие collector→APS bypass, не передавать write capability в collector.

## Вариант 1 — отдельный Modbus filtering gateway (рекомендуется для v1)

**Схема:**

```text
collector ──TCP──> gateway:collector-port
                       │
                       ├─ MBAP/PDU parser
                       ├─ function-code policy: {01,02,03,04}
                       ├─ reject audit (append-only)
                       └─ upstream TCP client ──> APS:502
```

**Плюсы:**

- Барьер ниже application-кода: даже скомпрометированный collector не получает маршрут к APS.
- T4 доказывает конкретный протокол и whitelist, а не только отсутствие вызывающего метода в SDK.
- Простая и локальная policy: разрешённые FC известны на границе, write FC 05/06/15/16/22/23 и неизвестные FC всегда получают Modbus exception 0x01.
- Можно ограничить compose network и firewall так, что единственным egress gateway будет APS:502.
- Нет преждевременной зависимости от OPC UA SDK и его разных вариантов write/call/history APIs.

**Минусы:**

- Нужны корректные MBAP fragmentation и TCP pipeline handling.
- Если фактический источник Q1 окажется только OPC UA, понадобится отдельный adapter.
- Gateway становится production process, который надо мониторить и включить в health/runbook.

## Вариант 2 — OPC UA dedicated read-only account/client

**Схема:** collector использует только отдельный service account, которому сервер АПС запрещает Write/Call/HistoryUpdate; client package не содержит этих методов.

**Плюсы:** меньше собственной сетевой логики; естественно для OPC UA node permissions; audit можно получать из server-side logs.

**Минусы:** защита зависит от корректности ACL/серверной конфигурации и account lifecycle; приложение всё ещё находится ближе к АПС; разные SDK и server profiles усложняют доказательство; T4 не получает универсальный wire-level reject для Modbus source.

## Вариант 3 — оба протокола сразу в dual-mode gateway

**Схема:** общий gateway process имеет Modbus filter и OPC UA read-only adapter, выбор `mode: modbus|opcua|both`.

**Плюсы:** покрывает неопределённость Q1; один operational surface; общий proof/audit contract.

**Минусы:** удваивает attack surface и тестовый matrix до подтверждения второго протокола; `both` может создать ошибочную иллюзию, что оба канала реально нужны; усложняет T4 и troubleshooting.

## Рекомендуемый подход

**Выбрать вариант 1 для v1: Modbus filtering gateway как обязательный production path.** Архитектура должна иметь protocol-neutral application port, но реализация OPC UA в s01 не создаётся. Если Q1 подтвердит OPC UA вместо Modbus, добавляется отдельный adapter за тем же port и тот же network/proof contract; это не оправдывает dual-mode в первом шаге.

Решение закрывает CR-P2-01 так:

- `mode` в `GatewaySettings` принимает `modbus` и оставляет `opcua` как явно неподключённый режим, который fail-fast с диагностикой; не использовать silent fallback.
- В production compose collector может подключаться только к gateway; APS сеть не содержит collector.
- Gateway имеет две зоны: pure `modbus_filter` и transport adapter. Application code не знает о socket framing.
- `rejected_writes.log` — append-only JSON Lines с `ts`, `function_code`, `source_ip`, `transaction_id`, `raw_pdu_sha256`, `reason`, `config_hash`; raw PDU не хранится целиком, чтобы не раздувать журнал и не утекали данные.
- Log write failure — hard failure для reject path: ответ write не может быть положительным, пока reject event не принят logger. Для read path logger failure даёт health degradation, но не разрешает write.

### Контракт pure parser/policy

```python
parse_mbap(buffer) -> ParseResult[Frame, NeedMoreData | ProtocolError]
classify(frame, policy) -> AllowRead | RejectWrite(reason, exception_code=0x01)
```

`parse_mbap` не читает socket и не меняет состояние. Он принимает bytes и возвращает consumed bytes, чтобы один buffer поддерживал несколько frames. `NeedMoreData` не является ошибкой и не отправляет ответ до полной frame; oversized length, invalid protocol id и impossible PDU дают protocol error и закрытие соединения.

`ModbusFilterGateway` orchestration:

1. bounded read into per-connection buffer;
2. repeatedly parse complete frames, оставляя хвост;
3. policy-check каждую frame независимо;
4. forward разрешённые read frames;
5. reject write/unknown без upstream call;
6. correlate response transaction id;
7. enforce per-frame timeout and connection cancellation.

### Тестовый и verification contract

- Example tests: FC 01/02/03/04 forwarded; FC 05/06/15/16 rejected with 0x01 and complete audit; malformed MBAP rejected; no upstream write call.
- Fragmentation: split MBAP header, split PDU, split between pipelined frames, three frames in one packet.
- Property-based tests: arbitrary byte chunks reassembled into same frame sequence; parser never consumes bytes beyond complete frame; allowed FC set is exactly `{1,2,3,4}`; a rejected function code never reaches upstream mock; transaction id remains correlated.
- Integration tests: collector→gateway→APS path works; direct collector→APS connection fails; gateway health reports upstream and audit logger state.
- T4 proof consumes only signed/configured allowlist and representative reject lines; proof generator (s15) must not infer read-only from an empty log.

**Результат:** [CR-P2-01] закрыт; s01 и s15 могут перейти к IMPLEMENT при сохранении CR-P2-10/12 только там, где они действительно требуются для OTA.

# 🎨🎨🎨 EXITING CREATIVE PHASE

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture — CR-P2-02 I5 OTA A/B

**Decompose steps:** [s12-i5-ota-rauc.md](../../plan/decompose-v1-p2-ship/s12-i5-ota-rauc.md), s19 runbook.  
**Связанные gates:** CR-P2-10 (точные health thresholds) и CR-P2-12 (edge OS base) остаются открытыми и не считаются закрытыми этим решением.  
**Компонент:** подписанное A/B обновление edge image без brick, с watchdog, health gate и anchorage policy.

## Вариант 1 — RAUC с A/B rootfs и U-Boot (рекомендуется)

**Плюсы:** хорошо соответствует system-image A/B, атомарному переключению и bootcount rollback; локальная проверяемая модель; подходит для одного судового edge без обязательного внешнего Mender server; однозначен для T5.

**Минусы:** требует дисциплины образа и bootloader integration; bundle/slot layout должен быть зафиксирован вместе с выбранным edge OS; потребуется lab harness для U-Boot/RAUC.

## Вариант 2 — Mender artifact + Docker-friendly deployment

**Плюсы:** удобнее для Docker-centric fleet; resume/artifact lifecycle и deployment metadata уже являются частью экосистемы.

**Минусы:** partition layout и инфраструктурные зависимости становятся менее локальными; полноценная ценность Mender раскрывается при fleet management, которого в v1 нет; усложняется proof того, что локальный watchdog действительно вернул рабочий слот.

## Вариант 3 — самописный updater поверх двух каталогов/контейнеров

**Плюсы:** быстрый prototype и минимальная внешняя зависимость.

**Минусы:** нет зрелой атомарной rootfs semantics; rollback, bootcount, interrupted write и recovery легко становятся неполными; неприемлемо для AC-B5/T5 и юридически чувствительного судового edge.

## Рекомендуемый подход

**Выбрать RAUC.** В v1 OTA является обновлением системного образа, а не только набора контейнеров. Edge OS base (CR-P2-12) может выбрать Ubuntu LTS или Yocto позже, но не должен менять policy contract: `rootfs_A/rootfs_B`, RAUC bundle, U-Boot `BOOT_SLOT`/bootcount, Ed25519 key path и health gate. Если CR-P2-12 выберет Yocto, RAUC остаётся; если выберет Ubuntu, RAUC работает как system-image integration. Mender не включать «на всякий случай».

### State machine и границы

```text
active A
  → verify bundle signature + hash
  → write inactive B using atomic RAUC install
  → set pending B + bootcount
  → reboot
  → health probe B
       pass → mark B good, clear pending
       fail/timeout → bootloader rollback to A
```

Policy/use-case не вызывает shell напрямую. Порты:

- `BundleVerifier.verify(path, expected_hash) -> VerifiedBundle` — Ed25519 и hash до записи slot B; invalid/unsigned — reject without mutation.
- `SlotManager.install(bundle)`, `set_pending(slot)`, `mark_good(slot)`, `rollback()` — RAUC/U-Boot adapter.
- `HealthProbe.check(deadline) -> HealthReport` — collector last sample `< 60s`, API `/health` success, DB writable; exact thresholds are CR-P2-10 and remain configurable/explicit.
- `VesselStatePort.current() -> VesselState` — source from existing vessel state/rpm policy; no direct raw RPM comparison in updater.
- `ClockPort` only for TTL/audit; monotonic clock drives watchdog deadlines.

### Fail-closed anchorage policy

`update_allowed` is true only if all are true:

1. current vessel state is `anchorage`;
2. state is fresh and not quarantined;
3. no active health failure or pending rollback;
4. approval is supplied by the required role once CR-P2-06 is closed;
5. manual override, if allowed by later policy, has explicit actor, TTL and audit record.

Transit, stale vessel state, missing rpm, conflicting manual/automatic state and expired override all deny update. `POST /api/admin/ota/approve` and `trigger` remain localhost/role-gated; public WAN is never a fallback path. The OTA agent itself rechecks anchorage immediately before install, so API approval cannot become a stale capability.

### Resume and recovery

Download uses bounded chunks/HTTP Range into a temporary file, fsyncs completed chunks and verifies full hash before RAUC install. Interrupted download leaves no pending slot. Interrupted install is delegated to RAUC atomic semantics; bootcount/watchdog handles interrupted boot. Never mark a slot good merely because process exit code is zero.

### T5 verification matrix

| Сценарий | Ожидание |
|---|---|
| unsigned bundle | reject before write to B; audit reason `signature_invalid` |
| bad hash | reject before install; slot state unchanged |
| healthy B | B becomes active/good after all health checks |
| B boots but collector dead | watchdog fails; rollback A |
| API healthy but DB read-only | health fails; rollback A |
| ten download interruptions | resume completes, final hash stable, one install |
| transit/unknown state | `update_allowed=false`, no install command |

Property-based tests cover state transitions: no path from unverified bundle to `pending`; failed health never produces `mark_good`; rollback is idempotent; chunk reassembly hash equals uninterrupted download; TTL never extends on read. Adapter tests mock RAUC/U-Boot; lab T5 runs real harness.

**Результат:** [CR-P2-02] закрыт для выбора OTA stack и A/B policy. CR-P2-10 и CR-P2-12 остаются самостоятельными creative gates; s12 нельзя считать полностью unblock по ним.

# 🎨🎨🎨 EXITING CREATIVE PHASE

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm + Architecture — CR-P2-04 B12 formulas v1

**Decompose steps:** [s02-b12-engine-core.md](../../plan/decompose-v1-p2-ship/s02-b12-engine-core.md), [s03-b12-formulas-v1.md](../../plan/decompose-v1-p2-ship/s03-b12-formulas-v1.md), [s05-b12-t9-fixtures.md](../../plan/decompose-v1-p2-ship/s05-b12-t9-fixtures.md).  
**Компонент:** versioned ship-pack formulas для motohours, fuel, averages/peaks, rounding и debounce.

## Вариант 1 — одна общая формульная функция с ветвлением по `type`

**Плюсы:** мало файлов на старте; быстро связать ReportEngine.

**Минусы:** типы отчётов и fuel methods начинают течь друг в друга; трудно тестировать инварианты; новая версия формулы рискует изменить старый run; provenance становится побочным словарём.

## Вариант 2 — pure calculation modules + typed manifest/loader (рекомендуется)

**Плюсы:** формулы тестируются без DB/API; `formulas_version` pinning естественно; каждая функция имеет ясный вход/выход и может отдавать value вместе с provenance; loader отвечает только за YAML validation; ReportEngine остаётся orchestration.

**Минусы:** чуть больше файлов и typed models; нужна дисциплина совместимости manifest и fixtures.

## Вариант 3 — SQL-first aggregation и формулы внутри запросов

**Плюсы:** меньше данных в Python для больших периодов; часть агрегаций эффективно делает Postgres.

**Минусы:** period boundary, monotonic clock, quality gaps, Q8 corrections и T9 bit-exact становятся завязаны на DB dialect; pure algorithm tests хуже; повторный расчёт трудно сделать по архивному payload вне DB.

## Рекомендуемый подход

**Выбрать вариант 2.** Формулы v1 — pure Python domain functions, ship-pack YAML — immutable input contract, ReportEngine — async orchestration, DB — хранение входного/выходного результата и append-only `report_runs`. SQL может предварительно выбрать samples, но не владеет semantics формулы.

### Versioning и loader

```yaml
# ship-pack/makarov/formulas/manifest.yaml
schema_version: 1
default_version: v1
versions:
  v1:
    released: 2026-11-01
    running_signal: bool_tag_then_compound
    fuel_method_default: flow_integral
    rounding: {fuel_unit: kg, fuel_rule: half_up, hours_decimals: 1}
    min_running_duration_sec: 60
```

Manifest loader:

1. validate schema and required keys;
2. resolve explicit version or `latest` once at request boundary;
3. return immutable `FormulaSet` with pinned version;
4. reject unknown version, conflicting fuel method or missing required tag config;
5. persist pinned `formulas_version` in every `report_runs` record and response.

`latest` is never stored in a report. Recalculation creates a new version row and retains old body/provenance.

### Running signal decision

V1 supports two explicitly configured modes, in priority order only when the configured source exists:

1. **`bool_tag`** — canonical Q4 running tag; values are normalized to `{0,1}` with invalid/quarantined values excluded and represented as a gap.
2. **`compound`** — `rpm > rpm_min AND oil_pressure ∈ norm`; both source tags and thresholds must be present in config. Missing one input does not silently mean stopped; interval is invalid/gap.

`bool_tag_then_compound` means a report config selects the source at load time, not per sample. It does not switch mid-period because a tag went stale. The selection and fallback prohibition go to provenance. `min_running_duration_sec` removes configured flutter only through an explicit debounce state machine; it does not fabricate valid samples in gaps.

### Fuel method Q8 decision

V1 implements both methods, but each report pins one method:

- **A `flow_integral` (default):** integrate calibrated flow over valid intervals; gaps split the integral and appear in provenance.
- **B `level_delta`:** `start - end + bunkering_in`, with configured tank calibration and corrections for heel/trim/temperature. A bunkering event missing from the event stream raises anomaly/provenance; it does not get guessed.

No automatic A↔B switch inside one report. If the selected method has insufficient data, output is explicitly limited/preliminary with `fuel_method_unavailable` and gaps; never substitute another method invisibly. This preserves Q8 auditability and lets T9 identify the method.

### Numeric and period rules

- Integrate over half-open `[from, to)` intervals.
- Use `Decimal` for configured corrections and boundary presentation; preserve source precision during accumulation.
- Round only once at presentation boundary: fuel kg/l per manifest, hours to 0.1; aggregate before rounding.
- Time-weighted average uses only valid intervals; peak/min retains value plus official timestamp.
- Quality `good` is required for integral/average; quarantine/stale intervals are omitted and added to `provenance.gaps`/`stale_intervals`.
- Clock adjustment uses B7 official/monotonic timeline and sets `clock_adjustment_in_period`; no wall-clock duration subtraction.
- Data watermark `< period.to` produces `preliminary`, not a fake final.

### Suggested module seams

```text
app/reports/formulas/
  models.py       # FormulaSet, FormulaInput, FormulaResult, FormulaProvenance
  loader.py       # YAML → immutable FormulaSet
  running.py      # bool/compound state machine
  fuel.py         # flow_integral, level_delta
  aggregates.py   # tw_avg, peak/min, interval splitting
  rounding.py     # boundary-only Decimal rounding
```

`ReportEngine` composes these functions and writes `ReportOutput`; it does not import YAML parser details into algorithm modules. `report_runs` repository exposes insert-only `insert_run`; DB trigger enforces UPDATE denial. Async generation executes outside collector writer and publishes a job state without blocking hot path.

### Formula verification

- Example tests: constant running integral; midnight crossing; clock jump; flow method A; level method B with bunkering; gap splitting; rounding at boundary; debounce 59/60/61 sec; preliminary watermark.
- Property-based tests: integral over adjacent intervals is additive when no gap; adding a gap never increases total; time-weighted average remains within valid input bounds; boundary rounding is idempotent; `formulas_version` remains pinned; no valid interval is created from quarantine; method A/B outputs never silently mix.
- T9 fixtures: `watch_midnight_cross`, `daily_clock_jump`, `fuel_flowmeter_24h` (Q8 A), `daily_gap_midday`; canonical JSON excludes generated_at before SHA256. Add a Q8 B fixture when calibrated level/bunkering fixture is available; otherwise preserve explicit fixture waiver.
- Negative tests: unknown formula version, missing running source, unknown fuel method, invalid correction config, duplicate bunkering event, negative duration.

**Результат:** [CR-P2-04] закрыт: running source contract, Q8 A/B method pinning, versioning, gaps/provenance and T9 invariants fixed.

# 🎨🎨🎨 EXITING CREATIVE PHASE

---

## Решения и открытые gates

| Creative ID | Решение | Статус | Что остаётся отдельно |
|---|---|---|---|
| CR-P2-01 | Modbus filtering gateway; protocol-neutral port для будущего OPC adapter | **closed** | Q1 может потребовать отдельный OPC adapter; это не dual-mode v1 |
| CR-P2-02 | RAUC A/B system-image update, U-Boot bootcount, fail-closed anchorage | **closed** | CR-P2-10 health thresholds; CR-P2-12 edge OS |
| CR-P2-04 | Pure versioned formulas, explicit running source, pinned Q8 A/B, gap provenance | **closed** | Q5 register/report forms — CR-P2-07 |

## Implementation guidance

1. s01 сначала реализует pure MBAP parser/policy и tests, затем transport/compose isolation; s15 использует только structured reject events.
2. s12 сначала реализует pure OTA state machine/verifier/anchorage gate через ports, затем RAUC adapter и lab mocks; exact health values не фиксировать повторно до CR-P2-10.
3. s02 сначала фиксирует `report_runs`, period/provenance и async job seam; s03 добавляет formula loader/integrators; s05 замораживает T9 canonical fixtures. Не переносить formula semantics в SQL.
4. Не добавлять generic plugin framework, event bus или отдельный orchestration service: текущие seams уже дают достаточную глубину и тестируемость.
5. Все error paths должны быть typed/stable; отсутствие данных показывается как gap/quarantine/preliminary, а не как zero/false/success.

## Verification summary

- [x] Один файл на batch, с epic-scoped path.
- [x] Core skills и situational skills gate перечислены.
- [x] Каждый CR имеет 3 варианта, pros/cons и обоснованную рекомендацию.
- [x] Architecture/Algorithm типы обозначены.
- [x] Gateway, OTA и formulas имеют pure seams, failure policy и test contract.
- [x] T4/T5/T9 requirements связаны с решениями.
- [ ] CR-P2-10 и CR-P2-12 — отдельные creative gates, не закрыты этим batch.

**Следующий режим:** `BACK IMPLEMENT` @s01 после обновления зависимостей; следующим чатом можно продолжить `BACK IMPLEMENT`.
