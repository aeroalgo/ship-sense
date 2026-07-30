# CR-STO-03 — Quarantine UX data flags: TagDisplayState, dual-path quality, native map diff, stale/no_data

**Creative ID:** CR-STO-03
**Decompose steps:** [s12-semantic-loader.md](../../plan/decompose-v1-p1-storage/s12-semantic-loader.md) · [s13-semantic-engine.md](../../plan/decompose-v1-p1-storage/s13-semantic-engine.md) · [s15-quarantine-diff.md](../../plan/decompose-v1-p1-storage/s15-quarantine-diff.md)
**Plan:** [plan-v1-p1-storage.md](../../plan/plan-v1-p1-storage.md) (§804–813 quarantine states, §221 tag state, §794 aggregate, §991–994 рекомендация, §778–802 native_map + validation)
**Дата:** 2026-07-29
**Режим:** BACK CREATIVE
**Уровень:** L4 (T-002 v1-p1 storage + semantic)
**AC:** AC-STO-S12, AC-STO-S13, AC-STO-S15 (B8.1–B8.6, §214–222)
**Unblocks:** s12 (loader/models) → s13 (engine) → s15 (quarantine persist) → T-003 HTTP/WS → T-004 UI badges

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `architecture-patterns` | граница SemanticEngine ↔ QuarantineService ↔ writer; где живёт state-machine (domain pure), где persist (adapter); separation engine.get_tag_state (read) vs quarantine.apply (write) |
| `property-based-testing` | инварианты: worst-of-child тотален/ассоциативен; diff детерминирован; state precedence линейный |
| `brainstorming` | dual-path (quality=4 на samples vs semantic-only) — рекомендация PLAN выбрана, здесь фиксируем контракт |
| `grill-me` | блокеров нет; все неясности разрешены рекомендацией §991–994 и схемой tag_quarantine (s04 done) |

---

## 0. Постановка проблемы

### 0.1 Что должно получиться

Единый контрактурованный поток «как тег получает display-state и как это отражается в данных», охватывающий три шага (s12 loader, s13 engine, s15 quarantine):

1. **TagDisplayState** enum: `normal | quarantine | no_data | stale` (+ системный `stop` для global map invalid).
2. **Dual-path** (рекомендация PLAN §991–994):
   - `quality=4 (quarantine)` на samples, записанных writer-ом пока тег в карантине → queryable historical truth.
   - `SemanticEngine.get_tag_state(tag_id)` → authoritative для UI badges (T-004 screens 1/8).
   - stale: нет sample row > `stale_threshold` → `no_data` **без** fake sample.
3. **Native map diff** → `QuarantineReport` (added/removed/changed) → persist в `tag_quarantine` (s04 done) → acknowledge flow.
4. **aggregate_status** worst-of-child по дереву vessel→room→system→mechanism→tags.

### 0.2 Зачем CR до кода

- s12 строит `VesselPack` / `NativeMap` модели — нужно знать, какие поля несёт `TagMeta` для state-резолва (mechanism_id, expected update rate для stale threshold per-tag).
- s13 строит `SemanticEngine.get_tag_state` — это **точка сборки** dual-path: engine читает `tag_quarantine` (persist s15) + последний sample timestamp (из writer/БД) + `stale_threshold`.
- s15 строит diff + persist — нужно зафиксировать `QuarantineReport` shape, `reason` vocabulary, acknowledge семантику.
- Без зафиксированного state-machine и contracts три шага расходятся в типах/семантике → rework.

### 0.3 Зафиксированные факты (verified 2026-07-29)

- `samples.quality SMALLINT CHECK (quality BETWEEN 0 AND 5)` — миграция 002. Значение 4 свободно (0=good default, 1=time_bad, 2–3 … reserved, 5 …). **Резервируем `quality=4` для quarantine.**
- `tag_quarantine (tag_id PK, reason TEXT, since TIMESTAMPTZ, native_id_hint TEXT, acknowledged BOOLEAN DEFAULT FALSE)` — миграция 004. PK = один активный quarantine per tag.
- `native_map_stub.yaml` shape (plan §761–778): `mappings: [{native_id, tag_id, codec, byte_order}], approved: bool`.
- `semantic_meta (pack_name, version, approved_at, checksum, manifest JSONB, UNIQUE(pack,version))` — s04 done; manifest хранит pack summary.
- Plan §804 quarantine table: trigger→state→UI mapping уже декларирован; creative фиксирует **machinery** под ним.
- `stale_threshold default 30 s` для 1 Hz (plan §813).

---

## Компонент 1 — Quality enum vocabulary (samples.quality 0–5)

🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture
Decompose step: [s12-semantic-loader.md](../../plan/decompose-v1-p1-storage/s12-semantic-loader.md) (models)
Компонент: словарь значений `samples.quality` (0–5), чтобы s12 loader / s13 engine / writer знали, что 4=quarantine, без магических чисел.

Требования и ограничения:
- `CHECK (quality BETWEEN 0 AND 5)` уже в миграции 002 — нельзя расширять за 5.
- Writer (s09 done) пишет quality из QualityEngine (collector CR-COL-04: good/bad/uncertain/stale/quarantine). Нужно согласование **коллекторной** quality с **storage** quality — это одна и та же шкала или две?

**Вариант A — одна сквозная шкала 0–5 (good=0, time_bad=1, uncertain=2, stale=3, quarantine=4, bad=5).**
Pros: один enum `SampleQuality`, writer проксирует коллекторное значение + storage-специфичные (time_bad из s08). Минимум дублирования; UI/query одна ось.
Cons: collector CR-COL-04 уже использует свои коды (good=0, bad, uncertain, stale, quarantine) — нужно проверить совместимость значений; расширение (Q4) ограничено потолком 5.

**Вариант B — две шкалы: collector-quality (свой enum) и storage-quality 0–5 (writer маппит при insert).**
Pros: изоляция изменений. Cons: двойной source of truth, таблица маппинга, риск расхождения; сложнее в query.

**Рекомендуемый подход: Вариант A** — одна сквозная шкала. Обоснование: samples.quality — единственный столбец истины в hypertable; collector и storage работают с одними физическими тегами; потолок 5 достаточен (5 состояний уже определены). Writer маппит `collector.Quality → SampleQuality` 1:1 на границе IPC/insert.

Фиксация значений (канон для s12 `models.py` enum `SampleQuality`):

| Значение | Имя | Источник-триггер |
|----------|-----|------------------|
| 0 | `good` | default, валидный sample |
| 1 | `time_bad` | s08 TimeAxis (битый source_ts год / вне skew) |
| 2 | `uncertain` | collector (CR-COL-04) — range/NaN/pass-through |
| 3 | `stale` | collector (CR-COL-04) — stuck/age |
| 4 | `quarantine` | **CR-STO-03**: tag в карантине → writer пишет quality=4 |
| 5 | `bad` | collector (CR-COL-04) — opc exception / modbus error / NaN-Inf |

Руководство по реализации:
- s12: `class SampleQuality(IntEnum)` в `models.py` со значениями выше + `DEFAULT = 0`.
- s13/s15: ссылаются на `SampleQuality.QUARANTINE == 4`.
- writer (s09 done, будущая доработка при s15): при insert sample, если `engine.get_tag_state(tag_id) == quarantine` → override quality=4 поверх коллекторного (приоритет quarantine выше коллекторного uncertain/stale).

Верификация:
- Unit: `SampleQuality.QUARANTINE == 4`, `min/max in [0,5]`.
- Интеграция s15: sample записан во время quarantine → `quality=4` в БД.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Компонент 2 — TagDisplayState machine (engine authoritative)

🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm
Decompose step: [s13-semantic-engine.md](../../plan/decompose-v1-p1-storage/s13-semantic-engine.md)
Компонент: `SemanticEngine.get_tag_state(tag_id) -> TagDisplayState` — pure resolver из 3 источников.

Требования и ограничения:
- Sources: (a) `tag_quarantine` row (unacknowledged/acknowledged), (b) последний sample ts для stale/no_data, (c) pack validity (global stop).
- Precedence зафиксирована в §794 для aggregate, но не для per-tag state — нужно определить порядок.
- `stale_threshold` default 30 s, но per-tag override через `TagMeta.expected_rate_s` (mechanism-level).

**Вариант A — precedence: `stop > quarantine > no_data > stale > normal`** (бинарное разрешение, первое совпавшее).
Pros: детерминированно, просто в тестах, O(1) per tag. Cons: маскирует составные состояния (tag может быть одновременно quarantine и stale).

**Вариант B — bitmap флагов + функция проекции в TagDisplayState.**
Pros: полный контекст для UI tooltip. Cons: over-engineering для T-004 MVP; UI хочет одно состояние для badge.

**Рекомендуемый подход: Вариант A** с уточнением порогов `no_data` vs `stale`.
Обоснование: UI badge — single value; history/queryable truth уже в `samples.quality`. Precedence решает конфликт.

Правила резолва (`get_tag_state`, plan §804 + §994):

| Условие (проверяются сверху вниз, первое совпадение) | State |
|------------------------------------------------------|-------|
| global pack invalid (SemanticEngine invalid flag) | `stop` |
| `tag_quarantine` row exists AND `acknowledged = FALSE` | `quarantine` |
| нет sample row для tag за последние `no_data_window` (= 3× `stale_threshold`) | `no_data` |
| последний sample `official_ts` старше `stale_threshold` (но есть в window) | `stale` |
| иначе | `normal` |

Параметры:
- `stale_threshold`: `TagMeta.expected_rate_s × 3` если задано, иначе default 30 s.
- `no_data_window`: `max(stale_threshold × 3, 90 s)` — чтобы при 1 Hz (threshold 30 s) no_data возникал не раньше ~90 s отсутствия данных.
- acknowledged quarantine → НЕ отображается как quarantine (operator подтвердил); tag возвращается в normal/stale по данным.

Руководство по реализации:
- s13: `TagDisplayState(str, Enum)`: `normal | quarantine | no_data | stale | stop`.
- `get_tag_state` — async (читает последний sample ts из кэша/БД); кэш `last_sample_ts: dict[str, datetime]` обновляется writer callback или polling.
- Stop-флаг: `SemanticEngine._invalid: bool` выставляется loader-ом при global validation failure (s12).

Верификация:
- Unit (property-based): для любого тега ровно одно состояние; precedence транзитивна.
- TDD s13: quarantine→acknowledge→normal; stale при old ts; no_data при отсутствии.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Компонент 3 — aggregate_status worst-of-child

🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm
Decompose step: [s13-semantic-engine.md](../../plan/decompose-v1-p1-storage/s13-semantic-engine.md) (§794)
Компонент: `aggregate_status(node_id) -> AggregateStatus` по поддереву.

Требования и ограничения:
- Precedence: `critical > warning > quarantine > no_data > normal` (plan §794). Но `critical`/`warning` — это collector-alarm/event уровни, не TagDisplayState. Нужно reconciliation.

**Вариант A — два отдельных enum: `TagDisplayState` (per-tag) и `AggregateStatus` (node), с функцией проекции.**
AggregateStatus = worst-of проекций children: tag→{quarantine,no_data,stale,normal}, плюс event-уровни {critical,warning} из events table.
Pros: семантически чисто; aggregate знает и про data-state и про alarms. Cons: функция проекции нетривиальна.

**Вариант B — AggregateStatus = worst-of TagDisplayState только.**
Pros: просто. Cons: теряет alarm-уровни (critical/warning из событий) — UI mechanism banner не построить.

**Рекомендуемый подход: Вариант A.** Проекция:
- tag `quarantine` → AggregateStatus `quarantine`
- tag `no_data` → `no_data`
- tag `stale` → `normal` (stale не агрегируется на уровень узла — это per-tag hint; иначе любой stuck тег держит весь механизм в no_data-подобном). **Альтернатива: stale→warning** — оставлен open для T-004, по умолчанию `normal` чтобы не флудить.
- event `alarm` severity=critical → `critical`; severity=warning → `warning`.
- worst-of по порядку `critical > warning > quarantine > no_data > normal`.

Руководство по реализации:
- s13: `AggregateStatus(str, Enum)`: `normal | no_data | quarantine | warning | critical`.
- `aggregate_status(node_id)`: DFS по поддереву, собрать children states (tag states + descendant aggregates + active alarms), вернуть worst по precedence. Кэш инвалидации при quarantine/event изменениях.

Верификация:
- Property-based: worst-of ассоциативен/коммутативен; identity = `normal`.
- TDD s13: один quarantine tag в mechanism → mechanism=quarantine; alarm critical → узел=critical поверх.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Компонент 4 — NativeMap diff → QuarantineReport

🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm
Decompose step: [s15-quarantine-diff.md](../../plan/decompose-v1-p1-storage/s15-quarantine-diff.md) (§219, §788, §802)
Компонент: `diff_native_map(approved: VesselPack, new_map: NativeMap) -> QuarantineReport`.

Требования и ограничения:
- Вход: approved pack (native_map с `approved: true`) vs новый new_map (live).
- Результат должен покрывать: new native_id без tag (→ added), tag без native_id больше (→ removed), native_id сменил tag (→ changed).
- `reason` vocabulary для `tag_quarantine.reason` (TEXT, без enum constraint в s04) — фиксируем канон строки.
- orphan native_ids в stub mode → warning, не error (plan §802).

**Вариант A — три списка (added/removed/changed) + per-entry reason string.**
Pros: исчерпывающий diff, UI показывает что именно изменилось. Cons: больше типов.

**Вариант B — единый список `changes` с `kind` enum.**
Pros: однородно. Cons: consumer всё равно группирует по kind.

**Рекомендуемый подход: Вариант A** — `QuarantineReport(added, removed, changed: list[QuarantineEntry])`, где каждый `QuarantineEntry(tag_id, native_id, reason, kind)`.

`reason` vocabulary (канон строки, машиночитаемый префикс):

| kind | reason string | trigger |
|------|---------------|---------|
| added | `native_unmapped:<native_id>` | new_map содержит native_id без соответствия в approved tag_map → candidate quarantine |
| added | `native_to_unknown_tag:<native_id>:<tag_id>` | native_id маппит на tag_id отсутствующий в approved assets |
| removed | `native_removed:<native_id>` | approved native_id пропал из new_map (tag может потерять live-source) |
| changed | `native_remap:<native_id>:<old_tag>:<new_tag>` | native_id теперь указывает на другой tag_id |

Алгоритм diff:
1. `approved_map = {native_id: tag_id}` из approved pack.
2. `new_mapping = {native_id: tag_id}` из new_map.
3. added = native_id ∈ new \ approved → entry.
4. removed = native_id ∈ approved \ new → entry.
5. changed = native_id ∈ both, tag_id differs → entry.
6. Для added/changed где tag_id ∈ new но ∉ approved assets tree → `native_to_unknown_tag`.

Quarantine создаётся **только для tag_id, присутствующих в approved assets** (чтобы не плодить карантин на несуществующие теги). Unknown-tag entries идут в report (для UI/alert), но `apply_quarantine` пропускает их.

Руководство по реализации:
- s15: `diff_native_map` pure function (без БД), тестируется на fixtures.
- `QuarantineReport` и `QuarantineEntry` — pydantic модели в `semantic/models.py` (s12 создаёт) или `quarantine.py` (s15). **Решение: в `models.py` (s12)**, т.к. engine (s13) возвращает `QuarantineReport` из `diff_native_map` по API (plan §790).

Верификация:
- Property-based: diff симметричен при swap round-trip для changed; idempotent (diff(x,x)=∅).
- TDD s15: added/removed/changed scenarios; unknown tag skipped in apply.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Компонент 5 — tag_quarantine persist + acknowledge flow

🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture
Decompose step: [s15-quarantine-diff.md](../../plan/decompose-v1-p1-storage/s15-quarantine-diff.md) (§803 table, §804)
Компонент: `apply_quarantine(report, session)` + `acknowledge(tag_id, session)` против `tag_quarantine` (s04 done).

Требования и ограничения:
- `tag_quarantine` PK = tag_id → один активный quarantine per tag (нет history-цепочки; overwrite).
- `acknowledged BOOLEAN` — operator подтверждает; после ack state возвращается к normal/stale (компонент 2).
- When re-diff убирает проблему (tag снова маппится верно) → row должен зачищаться, иначе acknowledged навсегда.

**Вариант A — full-reconcile per diff: upsert added/changed, delete removed, keep acknowledged только если причина та же.**
Pros: `tag_quarantine` всегда отражает текущий diff; нет зомби-rows. Cons: теряется history acknowledged quarantine (но history в samples.quality=4 + events).

**Вариант B — append-only: никогда не delete, только acknowledge.**
Pros: audit trail в таблице. Cons: PK=tag_id конфликтует (нужен surrogate key + миграция s04); UI должно фильтровать актуальные.

**Рекомендуемый подход: Вариант A** (full-reconcile). `tag_quarantine` = **current** state, history → `samples.quality=4` + `events` (s07 done). Это соответствует PK=tag_id из s04.

Алгоритм `apply_quarantine(report, session)`:
1. Собрать target tag_ids из report (только known в approved assets).
2. `DELETE FROM tag_quarantine WHERE tag_id NOT IN (targets) AND reason LIKE 'native_%'` — снять карантин с устранённых (только native-* причин; будущие причины — нет).
3. Для каждого target: `INSERT ... ON CONFLICT (tag_id) DO UPDATE SET reason=EXCLUDED.reason, native_id_hint=EXCLUDED.native_id_hint` **с сохранением `acknowledged`** если reason не изменился; сброс `acknowledged=FALSE` если reason изменился (operator должен перепроверить).
4. Event `quarantine_applied` (s07 events_repo) для audit.

`acknowledge(tag_id, session)`:
- `UPDATE tag_quarantine SET acknowledged=TRUE WHERE tag_id=$1`.
- Если row нет → no-op (idempotent) или warning log.
- Event `quarantine_acknowledged`.

Верификация:
- TDD s15: apply создаёт rows; re-diff без проблемы → rows удалены; acknowledge flips; changed reason → acknowledged=FALSE.
- Интеграция: engine.get_tag_state отражает acknowledged (компонент 2).

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Компонент 6 — Dual-path contract: quality=4 на samples vs semantic state

🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture
Decompose step: cross-cutting [s13](../../plan/decompose-v1-p1-storage/s13-semantic-engine.md) + [s15](../../plan/decompose-v1-p1-storage/s15-quarantine-diff.md) + writer (s09)
Компонент: контракт кто пишет `quality=4` и кто читает — чтобы не было гонок и двойной истины.

Требования и ограничения:
- Writer (s09 done) вставляет samples; должен знать state тега в момент insert.
- `SemanticEngine.get_tag_state` async читает кэш; quarantine меняется реже (operator action / diff), не каждые 1 Hz.

**Вариант A — writer опрашивает `engine.is_quarantined(tag_id)` (sync, bool из кэша) перед insert; ставит quality=4.**
Pros: минимум latency на hot path; кэш обновляется quarantine service. Cons: writer зависит от engine; гонка на границе quarantine onset/offset (sample в момент перехода).

**Вариант B — writer пишет collector quality как есть; отдельный reconciler проставляет quality=4 ретроспективно.**
Pros: writer не зависит от engine. Cons: окно с неконсистентным quality; extra job; complexity.

**Рекомендуемый подход: Вариант A** с **кэшем quarantined-tag-set в SemanticEngine**.
Обоснование: writer уже в том же процессе (apps/edge); quarantine — редкое событие; кэш `set[str]` tag_ids в карантине обновляется `apply_quarantine`/`acknowledge` и не требует запроса на каждый sample.

Контракт:
- `SemanticEngine.quarantined_tags() -> frozenset[str]` — snapshot текущих unacknowledged quarantine tag_ids (sync, из in-memory set, обновляемого s15).
- Writer insert path: `quality = SampleQuality.QUARANTINE if tag_id in engine.quarantined_tags() else collector_quality`. **Precedence: quarantine выше uncertain/stale, но ниже bad (5)** — bad-данные не маскируем как quarantine. Уточнённое правило: `quarantine переопределяет {0,1,2,3}`, но **не** `{5 bad}`.

Гонки: допустимо ±1 sample window на границе перехода — quality фиксирует момент записи, `tag_quarantine.since` фиксирует момент решения. UI (T-004) показывает state из engine, не из quality — поэтому визуальной гонки нет.

Руководство по реализации:
- s13: `quarantined_tags()` метод + in-memory `set` обновляемый из s15 apply/acknowledge (engine подписан на quarantine service или s15 дергает `engine._invalidate_quarantine_cache(session)`).
- s15: после `apply_quarantine`/`acknowledge` → `engine.refresh_quarantine_cache(session)`.
- writer (s09 done; доработка в s15 scope или отдельный micro-step): импорт `SampleQuality`, проверка set.

Верификация:
- TDD s13: quarantined_tags отражает apply/acknowledge; s15: writer-путь quality=4 (mock engine).
- Интеграция T-002: sample записан в окне quarantine → quality=4 в БД + engine.get_tag_state=quarantine.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Сводка решений (для IMPLEMENT)

| Решение | Значение |
|---------|----------|
| `SampleQuality` enum | 0=good, 1=time_bad, 2=uncertain, 3=stale, **4=quarantine**, 5=bad (s12 models.py) |
| `TagDisplayState` | `normal \| quarantine \| no_data \| stale \| stop` (s13) |
| `get_tag_state` precedence | stop > quarantine(unacked) > no_data(no sample в 3×threshold) > stale(last ts > threshold) > normal |
| `AggregateStatus` | `normal \| no_data \| quarantine \| warning \| critical`; worst-of, stale→normal на aggregate |
| `QuarantineReport` | pydantic в models.py (s12); added/removed/changed списки `QuarantineEntry` |
| `reason` vocabulary | `native_unmapped:*`, `native_to_unknown_tag:*:*`, `native_removed:*`, `native_remap:*:*:*` |
| `tag_quarantine` | full-reconcile per diff; PK=tag_id; history → samples.quality=4 + events |
| acknowledge | flip `acknowledged=TRUE`; changed reason → reset acknowledged=FALSE |
| dual-path | writer ставит quality=4 если tag ∈ `engine.quarantined_tags()`, override {0–3}, не override bad(5) |
| stale_threshold | `TagMeta.expected_rate_s × 3` или 30 s; no_data_window = max(3×threshold, 90 s) |

## Файлы, создаваемые/правимые этим CR (в downstream steps)

- `apps/edge/semantic/models.py` (s12): `SampleQuality`, `TagDisplayState`, `AggregateStatus`, `QuarantineReport`, `QuarantineEntry`, `NativeMap` — все enum/модели из компонентов 1–4.
- `apps/edge/semantic/engine.py` (s13): `get_tag_state`, `aggregate_status`, `quarantined_tags`, `diff_native_map` (делегирует pure diff из s15).
- `apps/edge/semantic/quarantine.py` (s15): `diff_native_map` pure, `apply_quarantine`, `acknowledge`, `refresh_quarantine_cache`.
- Тесты: `tests/storage/test_semantic_loader.py`, `test_semantic_engine.py`, `test_quarantine.py`.

## Верификация CR (definition of closed)

- [x] Все 6 компонентов имеют зафиксированный контракт (типы + алгоритмы).
- [x] Нет открытых блокеров (grill-me не требуется).
- [x] Согласовано со схемой БД (s02 quality CHECK, s04 tag_quarantine).
- [x] Skills: architecture-patterns (границы), property-based-testing (инварианты) — применены.
- [x] Rewire: s12/s13/s15 + decompose index — см. ниже.
