# CR-COL-04 — Quality mapping: OPC StatusCode / Modbus exception / NaN-Inf / range / stale / quarantine → Quality

**Creative ID:** CR-COL-04
**Decompose step:** [s11-quality-engine.md](../../plan/decompose-v1-p1-collector/s11-quality-engine.md)
**Plan:** [plan-v1-p1-collector.md](../../plan/plan-v1-p1-collector.md) (§7.1 Quality enum, §14.2 quality rules YAML, AC-B4-04/07/08/12, AC-B3-06)
**Дата:** 2026-07-27
**Режим:** BACK CREATIVE
**Уровень:** L4 (T-001)
**AC:** AC-B3-06, AC-B4-04, AC-B4-07, AC-B4-08, AC-B4-12
**Unblocks:** s11 (BACK IMPLEMENT) → s13 (NormalizerWorker consume) → s22 (dirt: opc_bad_quality / nan_inf / stuck_value)

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `architecture-patterns` | stratification evaluator (native_quality → NaN/range → stale), pure function vs class, где живут mapping таблицы |
| `improve-codebase-architecture` | граница QualityEngine ↔ NormalizerWorker ↔ UnitConverter; YAML как данные, не код |
| `property-based-testing` | инварианты: NaN/Inf → bad всегда; stale монотонно по age; map_func тотальна |
| `brainstorming` | частично — выбор value-encoding для bad (null vs sentinel) потребовал сравнения |
| `grill-me` | блокеров нет; все неясности разрешены в §0.4 |

---

## 0. Постановка проблемы

### 0.1 Что должно получиться

Единый `QualityEngine` (pure function core + YAML-конфиг), который на входе имеет:

- `RawSample` (выход B2 Modbus / B3 OPC) с `raw_value: Any`, `native_quality: str | None`, `recv_ts`, `source_ts`
- `TagMapEntry` (map entry: `range_min`, `range_max`, `datatype`)
- `now: datetime` (для stale)
- правила из `quality_rules.yaml`

…и на выходе даёт **один из 5 значений `Quality`** (`good | bad | uncertain | stale | quarantine`), плюс сохранённое значение (или null) и опциональную причину-диагностику.

Это ядро **B4 Normalizer** (FR-B4-3 `QualityEngine.apply(rules, sample, map_entry, age)`). Все 5 значений должны быть **достижимы тестами** (AC-B4-04). Правила — **YAML без правки кода** (AC-B4-12).

### 0.2 Входные данные (as-is сегодня)

**Modbus (B2):** `ModbusTcpConnector._poll_group` строит `RawSample`:

- успех → `raw_value` = декодированное число/bool/str, `native_quality = "good"` ([modbus/connector.py:177](apps/edge/collector/src/collector/plugins/modbus/connector.py#L177))
- decode error на теге → `raw_value=None`, `native_quality=str(e)` ([modbus/connector.py:186](apps/edge/collector/src/collector/plugins/modbus/connector.py#L186))
- group-level exception (`ModbusTimeoutError` / `ModbusException` / `ModbusClientError`) → все теги группы → `raw_value=None`, `native_quality=str(e)` ([modbus/connector.py:196](apps/edge/collector/src/collector/plugins/modbus/connector.py#L196))

Modbus client ([modbus/client.py](apps/edge/collector/src/collector/plugins/modbus/client.py)) бросает типизированные исключения:
- `ModbusClientError` (базовая; «not connected», protocol error)
- `ModbusTimeoutError` (подкласс `ModbusClientError`)
- `pymodbus.exceptions.ModbusException` (protocol: illegal address, function rejected, slave failure — **exception codes 01..08**)

Проблема: сегодня `native_quality` на error = свободная строка `str(e)`. Это **не structured code**. Чтобы маппить в Quality, нужен либо парсинг строк (хрупко), либо сменить контракт: connector кладёт в `native_quality` **нормализованный токен** (напр. `"modbus.timeout"`, `"modbus.exception.02"`), а `QualityEngine` маппит токен → Quality по YAML.

**OPC UA (B3):** `SubscriptionManager._make_raw_sample` ([opcua/subscription.py:95](apps/edge/collector/src/collector/plugins/opcua/subscription.py#L95)):

- `status = getattr(data, "StatusCode", None)` из `DataChangeNotif`
- `native_quality = str(status)` — asyncua отдаёт asyncua-объект StatusCode; его `str()` ≈ `"StatusCode.Good"` / `"StatusCode.Bad"` / `"StatusCode.Uncertain"` (или с под-флагами `Bad.NoCommunication` и т.п.)
- sync path `OpcUaConnector.read` ([opcua/connector.py:157](apps/edge/collector/src/collector/plugins/opcua/connector.py#L157)): на exception `native_quality=str(e)`.

Проблема: `str(StatusCode)` у asyncua **зависит от версии asyncua** и иногда возвращает имя enum, иногда hex. Нужен **явный `StatusCode.name`/`.value` extraction**, а не `str()`.

**NaN/Inf:** ни Modbus, ни OPC декодер сейчас NaN/Inf не фильтруют. float32 decode ([modbus/decoder.py](apps/edge/collector/src/collector/plugins/modbus/decoder.py)) через `struct.unpack` может вернуть `nan`/`inf` — это «валидный» float, но физически бессмысленный. AC-B4-08 / AC-I3-08 требуют: NaN/Inf → `bad`. Это работа QualityEngine, а не decoder (decoder не знает про quality semantics).

**Out-of-range:** `TagMapEntry.range_min/range_max` уже в модели ([config/models.py:61](apps/edge/collector/src/collector/config/models.py#L61)). Сегодня никто их не проверяет. AC-B4-07: out-of-range → `uncertain` (или `bad`), **значение сохраняется**. Это работа QualityEngine.

**Stale:** возраст семпла = `now - (source_ts or recv_ts)`. При `> stale_threshold_sec` → `stale`. Но «stale» в нашей системе двусмысленно:
1. **Единичный старый семпл** (source давно не присылал) — это про **NormalizerWorker**: он смотрит «когда последний раз приходил свежий семпл для тега», а не на возраст одного RawSample. AC-I3-07 `stuck_value` именно про это.
2. **Возраст одного RawSample** (`source_ts` давно в прошлом относительно `now`) — это про **этот самый RawSample**: полезно для OPC push, где значение может прийти с задержкой, или для re-queued семплов.

Решение ниже — QualityEngine проверяет **возраст одного семпла** (вариант 2, дешёвый, deterministic); NormalizerWorker (s13) поверх добавляет «tag hasn't updated in N sec» логику (вариант 1). В этом creative — только возраст семпла.

**Quarantine:** `quarantine` = tag map mismatch / unknown new tag (B8/T7). Сейчас B8/T7 не реализованы (план фазы 2). Но Quality-значение `quarantine` должно быть **достижимо** (AC-B4-04). Решение: QualityEngine принимает опциональный флаг/причину `quarantined=True` (поставляется NormalizerWorker, если tag не найден в map); сам QualityEngine quarantine не инициирует.

### 0.3 Что НЕ в scope этого creative

- **NormalizerWorker loop** (s13): orchestration, raw_queue consume, event detection, «tag stale» (вариант 1 выше). QualityEngine — только pure-функциональная оценка одного RawSample.
- **UnitConverter** (s12): scale/offset, units.yaml. QualityEngine не делает conversion — он оценивает **raw_value до conversion** (range проверка на raw или на converted — см. §5; решение: на raw, т.к. conversion не ломает физический диапазон).
- **HealthAggregator** (s14): уже done, не трогаем.
- **B8/T7 tag-map mismatch detector**: фаза 2; QualityEngine только принимает флаг.

### 0.4 Открытые вопросы (разрешены)

| Вопрос | Решение | Где зафиксировано |
|--------|---------|-------------------|
| `native_quality` свободная строка vs structured token? | **Structured token** (напр. `modbus.timeout`, `opcua.StatusCode.Bad`). Connector нормализует; QualityEngine маппит токен → Quality по YAML. | §1, §2 |
| OPC `str(StatusCode)` хрупко — брать `.name`? | Да: `getattr(status, "name", None) or str(status)`. Connector фиксирует токен `opcua.<name>`. | §1.4 |
| NaN/Inf проверять в decoder или engine? | **Engine** (decoder не знает quality; AC-B4-08 — это quality rule). | §3 |
| Range на raw или converted value? | **Raw** (conversion linear, не ломает диапазон; проверка до conversion = раньше fail). | §5 |
| Stale: per-sample age или per-tag «no update»? | **Per-sample age** здесь (вариант 2). Per-tag «no update» — NormalizerWorker s13. | §6 |
| bad: value=null или sentinel? | **value=null (None)**. Sentinel добавляет магию в downstream; null уже в `TelemetrySample.value: float|...|None`. | §0.5, §4 |
| Где живёт приоритет правил (NaN vs range vs stale)? | Fixed order в evaluator, **не** в YAML (см. §7). | §7 |
| Quarantine кто инициирует? | **NormalizerWorker** (tag not in map); QualityEngine принимает флаг. | §8 |
| YAML reload: hot или restart? | **Restart** (load once at startup). Hot reload — premature (YAGNI); AC-B4-12 говорит «rules в YAML без правки кода», не «hot reload». | §9 |

### 0.5 Дизайн-принципы (YAGNI + Existing-reuse)

1. **Reuse existing `Quality` enum** ([domain/models.py:8](apps/edge/collector/src/collector/domain/models.py#L8)) — не добавляем новые значения.
2. **Reuse `TagMapEntry.range_min/range_max`** — не дублируем в YAML.
3. **Pure function core** (`evaluate(...)`) — тестируется без I/O, как FR-B4-5 требует для `normalize`.
4. **YAML = данные, не код**: никаких `eval`, лямбд, плагинов в YAML. Только статические таблицы token→Quality + скалярные thresholds.
5. **Connector отвечает за token, engine — за mapping**: разделение по arrow of data flow (connector знает протокол, engine знает quality semantics).
6. **Никаких defensive fallbacks**: unknown token → explicit default из YAML (`unknown_native_quality: uncertain`), не silent good. Исключение — ломает pipeline, но видим ошибку (per project rule «чинить причину, не fallback»).

---

## 1. Компонент 1: OPC UA StatusCode → Quality (полная таблица)

### Требования и ограничения

- **AC-B3-06:** StatusCode → quality mapping (FR-B3-5 `map_opcua_status() → Quality`).
- **AC-I3-13:** сценарий `opc_bad_quality` — Bad StatusCode от сервера → bad.
- Вход: OPC UA StatusCode из `DataChangeNotif` (asyncua) или исключение из `read`.
- asyncua StatusCode имеет структуру: битовые поля (Severity bits 13-15: `00`=Bad, `01`=Uncertain, `10`=Good... на самом деле OPC UA: Good=000/0xx, Uncertain=01x, Bad=1xx в severity bits), плюс `.name`/`.value`.
- Полная таблица OPC UA StatusCode — **большая** (~200 кодов: Good, GoodClamped, Uncertain, UncertainLastUsableValue, Bad, BadNoCommunication, BadOutOfService, ...). Маппить **все** — overkill для фазы 1.
- Ограничение фазы 1: маппить **по severity class** (Good / Uncertain / Bad), с override-таблицей для конкретных кодов, которые требуют отличной семантики (напр. `BadWaitingForInitialData` → stale, а не bad).

### Вариант 1A — Severity-class mapping + override table (рекомендуемый)

**Идея:** два уровня в YAML:

```yaml
opcua:
  severity_class:
    good: good           # bits 13-15 = 000/0xx
    uncertain: uncertain # bits = 01x
    bad: bad             # bits = 1xx
  overrides:
    BadWaitingForInitialData: stale   # сервер ещё не отдал первое значение
    BadNoCommunication: bad
    BadOutOfService: bad
    UncertainLastUsableValue: uncertain
    GoodClamped: uncertain             # значение было clamped — под вопросом
  unknown_status: uncertain            # не распознан → безопасный дефолт
```

Connector извлекает из asyncua StatusCode: severity bits (`status.value & 0xC0000000`), либо `.name`, кладёт в `native_quality` токен `opcua.<StatusName>` (напр. `opcua.BadNoCommunication`). Engine:
1. Если `StatusName` в `overrides` → тот Quality.
2. Иначе → `severity_class[<class>]`.

**Плюсы:**
- Покрывает **все** ~200 StatusCode без перечисления — severity class выводится из bits.
- Override — точечные исключения (явные, читаемые).
- Таблица компактна (~10 override-строк vs 200).
- Соответствует OPC UA spec (severity — это first-class concept).

**Минусы:**
- Нужен разбор severity bits (асинхронные отличия asyncua: у некоторых версий `.value` — это 32-битный код, у других `.doc`/`.name` — строка). Требует **один** helper в connector.
- Override lookup — O(1) dict, но добавляет шаг перед class fallback.

### Вариант 1B — Полный явный enum → Quality table

**Идея:** перечислить все ~200 StatusCode явно в YAML:

```yaml
opcua:
  map:
    Good: good
    GoodClamped: uncertain
    GoodLocalOverride: uncertain
    Uncertain: uncertain
    UncertainLastUsableValue: uncertain
    Bad: bad
    BadNoCommunication: bad
    # ... ещё ~190 строк
  unknown_status: uncertain
```

**Плюсы:**
- Максимально явно — каждый код виден.
- Нет разбора bits.

**Минусы:**
- ~200 строк YAML на каждый проект (duplication OPC UA spec).
- Любой новый код в asyncua → не в таблице → `unknown_status`. Фактически тот же severity-fallback, но вручную.
- YAGNI нарушение: 95% кодов маппятся тривиально по severity.

### Вариант 1C — Code-based (hex value) mapping

**Идея:** маппить по числовому `StatusCode.value` (hex): `0x80000000` = BadNoCommunication и т.д.

**Плюсы:** не зависит от asyncua naming.

**Минусы:** нечитаемо (`0x803B0000` vs `BadWaitingForInitialData`); те же ~200 значений; хрупко к версиям asyncua (значения стабильны по OPC UA spec, но ~).

### Рекомендация для компонента 1

**Вариант 1A — severity-class + overrides.** Покрывает весь спектр минимальным YAML, явно обрабатывает edge-cases (BadWaitingForInitialData → stale), соответствует OPC UA spec. Реализация — один helper в OpcUaConnector/SubscriptionManager для извлечения severity+name, остальное в YAML.

### 1.4 Извлечение StatusCode из asyncua (контракт connector → engine)

asyncua `StatusCode` объект (из `DataChangeNotif.monitored_item.Value.StatusCode`):

```python
# в SubscriptionManager._make_raw_sample:
status_obj = getattr(data, "StatusCode", None)  # может быть None
if status_obj is not None:
    name = getattr(status_obj, "name", None) or str(status_obj)
    native_quality = f"opcua.{name}"   # токен: opcua.Good, opcua.BadNoCommunication
else:
    native_quality = None              # сервер не отдал StatusCode
```

Severity bits (если name ненадёжен): `severity = (status_obj.value >> 30) & 0x3` → `0`=Good, `1`=Uncertain, `2`=Bad. Connector **не** парсит bits сам — engine делает это **только если** name отсутствует (fallback). Нормальный путь — name-based override → class-by-name-prefix (`Good*`/`Uncertain*`/`Bad*`).

**Решение упрощённо:** engine смотрит на **префикс имени** токена (`opcua.Good*` → good, `opcua.Bad*` → bad, `opcua.Uncertain*` → uncertain), плюс explicit overrides. Это избегает bit-parsing полностью и устойчиво к asyncua naming. Bit-parsing — только documented fallback в helper `opcua_severity_class(name)`, покрытый тестом.

**Изменение connector кода (s10 уже done — нужен минимальный patch в s11 IMPLEMENT или в s13):**

> ⚠️ `SubscriptionManager._make_raw_sample` сегодня делает `native_quality = str(status)` ([subscription.py:108](apps/edge/collector/src/collector/plugins/opcua/subscription.py#L108)). Для CR-COL-04 контракт меняется на `native_quality = f"opcua.{name}"`. Это правка существующего кода — вынести в s11 IMPLEMENT как явный refactor шаг (connector-side), либо в s13. **Решение:** правка в s11 (т.к. engine и connector-контракт — одна atomic deliverable s11). Аналогично Modbus connector: today `native_quality=str(e)`, меняется на `native_quality="modbus.<token>"` (см. §2.5).

### 1.5 Полная таблица OPC UA → Quality (deliverable для YAML)

Базис: severity prefix. Override — конкретные имена asyncua StatusCode (канон OPC UA Part 8).

| Токен (`opcua.<name>`) | Severity | Quality (override / class) | Примечание |
|------------------------|----------|----------------------------|------------|
| `opcua.Good` | Good | good | норма |
| `opcua.GoodClamped` | Good | **uncertain** | значение было ограничено |
| `opcua.GoodLocalOverride` | Good | **uncertain** | локальная подмена |
| `opcua.Uncertain*` | Uncertain | uncertain | весь класс |
| `opcua.Bad` | Bad | bad | общий Bad |
| `opcua.BadNoCommunication` | Bad | bad | нет связи с устройством |
| `opcua.BadOutOfService` | Bad | bad | устройство в обслуживании |
| `opcua.BadSensorFailure` | Bad | bad | датчик неисправен |
| `opcua.BadWaitingForInitialData` | Bad | **stale** | сервер ждёт первое значение → «устарело» |
| `opcua.BadWaitingForInitialData` alt | — | stale | AC-I3-13 сценарий |
| `opcua.BadDataLost` | Bad | bad | |
| `opcua.BadNoData` | Bad | **stale** | нет данных за период |
| `opcua.BadNoDataAvailable` | Bad | stale | |
| `opcua.Bad*` (прочие) | Bad | bad | весь класс |
| `None` (status не пришёл) | — | good | нет сигнала о плохом — считаем good (см. §1.6) |
| неизвестный токен | — | uncertain | `unknown_status` safe default |

### 1.6 `native_quality = None` — это good?

**Да.** Семантика: `None` = «протокол не сообщил о проблеме». Для Modbus успешное чтение сегодня уже ставит `native_quality="good"` — меняем на **`None`** для успеха (явное отсутствие проблемы). Для OPC push без StatusCode — `None` = good. Это согласовано с `Quality.GOOD` дефолтом в `Event`/`TelemetrySample`.

> **Контракт-изменение для s11:** Modbus success-path `native_quality="good"` → `native_quality=None`. OPC success-path уже `None` по факту (status object None). Engine: `None` → good (short-circuit, до NaN/range/stale проверок).

---

## 2. Компонент 2: Modbus exception code → Quality

### Требования и ограничения

- **AC-B2-08:** exception на одном регистре не роняет цикл опроса остальных.
- **AC-B2-09:** timeout → bad quality.
- **FR-B2-5:** per-register exception → RawSample with `native_quality=exception_code`.
- Modbus exception codes (MBException): 01 IllegalFunction, 02 IllegalDataAddress, 03 IllegalDataValue, 04 SlaveDeviceFailure, 05 Acknowledge, 06 SlaveDeviceBusy, 08 MemoryParityError.
- pymodbus кидает `ModbusException` (базовый) с `.code` attr для ExceptionResponse.

### Вариант 2A — Типизированный token + code mapping (рекомендуемый)

**Идея:** connector нормализует исключение в токен вида `modbus.<class>.<code>`:

```python
# в ModbusTcpConnector error handling:
except ModbusTimeoutError:
    native_quality = "modbus.timeout"
except ModbusClientError as e:
    native_quality = "modbus.client_error"
except ModbusException as e:
    code = getattr(e, "code", None)
    native_quality = f"modbus.exception.{code}" if code else "modbus.exception"
```

YAML:

```yaml
modbus:
  map:
    timeout: bad
    client_error: bad            # not connected / protocol
    exception.1: bad             # IllegalFunction
    exception.2: bad             # IllegalDataAddress
    exception.3: bad             # IllegalDataValue
    exception.4: bad             # SlaveDeviceFailure
    exception.5: uncertain       # Acknowledge — устройство занято, повтор
    exception.6: uncertain       # SlaveDeviceBusy
    exception.8: bad             # MemoryParityError
  unknown_exception: bad         # безопасный дефолт для Modbus
```

**Плюсы:**
- Structured token — машиночитаемый, не парсим `str(e)`.
- Explicit per-code mapping в YAML.
- Покрытие тестами каждого кода (AC-B4-04 достижение bad через разные пути).

**Минусы:**
- Требует правки connector error-handling (сегодня `native_quality=str(e)`).
- `exception.5`/`.6` как uncertain — спорно (Acknowledge в Modbus = «команда принята, долго выполняется»); для фазы 1 reasonable.

### Вариант 2B — Строковый парсинг `str(e)`

**Идея:** оставить `native_quality=str(e)`, в engine regex-парсить «timeout», «ModbusException code=2» и т.д.

**Плюсы:** ноль правок connector.

**Минусы:** хрупко — формат `str(e)` зависит от pymodbus версии; локали; locale-dependent. **Отвергаем** (project rule: чинить причину, не строковый fallback).

### Вариант 2C — Прямой тип-объект в native_quality (не строка)

**Идея:** класть в `native_quality` сам exception объект / enum.

**Плюсы:** maximum fidelity.

**Минусы:** ломает pydantic-сериализацию `RawSample` (`native_quality: str | None`); JSON round-trip в test_domain_models падает. **Отвергаем** — `RawSample.native_quality` контракт уже `str | None` и сериализуется.

### Рекомендация для компонента 2

**Вариант 2A — типизированный token + YAML code mapping.** Structured, тестируемый, не ломает сериализацию. Правка connector — точечная (4 except-блока).

### 2.5 Изменение Modbus connector кода (в s11 IMPLEMENT)

[modbus/connector.py:186-196](apps/edge/collector/src/collector/plugins/modbus/connector.py#L186) — сегодня:

```python
except Exception as e:  # noqa: BLE001
    bad = RawSample(..., native_quality=str(e), ...)
```

Меняем на типизированный token (нужен import `ModbusClientError`, `ModbusTimeoutError`, `ModbusException`):

```python
except ModbusTimeoutError:
    token = "modbus.timeout"
except ModbusClientError:
    token = "modbus.client_error"
except ModbusException as e:
    code = getattr(e, "code", None)
    token = f"modbus.exception.{code}" if code else "modbus.exception"
bad = RawSample(..., native_quality=token, ...)
```

И аналогично в `_poll_group` group-level handler ([modbus/connector.py:196](apps/edge/collector/src/collector/plugins/modbus/connector.py#L196)).

**Это правка существующего файла** — отметить в s11 как «connector-side quality-token contract» шаг (до engine).

---

## 3. Компонент 3: NaN/Inf handling (AC-B4-08, AC-I3-08)

### Требования и ограничения

- **AC-B4-08:** NaN/Inf → quality=bad, value=null или sentinel (CREATIVE — решаем тут).
- **AC-I3-08:** сценарий `nan_inf` — NaN/Inf в float → bad, не valid number.
- Вход: `raw_value: Any` (может быть float `nan`/`inf`/`-inf`, int, bool, str, None).
- Только **float** может быть NaN/Inf (int/bool/str — нет). `math.isnan` требует float (или int работает для isnan? нет — `math.isnan("x")` TypeError). Нужна safe check.

### Вариант 3A — Engine-side `math.isfinite` check + value=null (рекомендуемый)

**Идея:** в evaluator, после native_quality mapping, если `raw_value` — float и не finite:

```python
def _is_non_finite(value: Any) -> bool:
    return isinstance(value, float) and not math.isfinite(value)

if _is_non_finite(raw_value):
    return EvalResult(quality=Quality.BAD, value=None, reason="nan_or_inf")
```

YAML:

```yaml
value:
  nan_inf: bad   # всегда bad; не configurable в good/uncertain (физически бессмысленно)
```

`value=None` (null) в `TelemetrySample` — UI фронта (T-004) рисует прочерк.

**Плюсы:**
- AC-B4-08 буквально (`value=null`).
- `math.isfinite` — stdlib, O(1).
- Достижение `bad` через NaN — один из 5 required путей (AC-B4-04).

**Минусы:**
- Теряем исходное значение (NaN). Для diag можно сохранить в `reason`.

### Вариант 3B — Sentinel value (напр. `float("nan")` сохраняется, quality=bad)

**Идея:** value остаётся `nan`, но quality=bad. Frontend сам фильтрует nan.

**Плюсы:** сохраняется trace.

**Минусы:**
- NaN в JSON — non-standard (JSON не поддерживает NaN; pydantic может сериализовать как `NaN` строку или ошибку). `TelemetrySample.model_dump(mode="json")` с NaN → либо `"NaN"` (нестандарт), либо ValidationError.
- Downstream (writer, T-002) должен фильтровать NaN везде —扩散.
- AC-B4-08 буквально предлагает `value=null` первым.

**Отвергаем.**

### Вариант 3C — Decoder-side NaN rejection

**Идея:** Modbus float32 decoder возвращает None для NaN-битовых паттернов.

**Плюсы:** engine не знает про NaN.

**Минусы:**
- OPC UA может прислать NaN напрямую (не через decoder) — engine всё равно должен проверять.
- Decoder смешивает concerns (декодирование vs quality).
- AC-B4-08 — это quality rule, не decoder rule.

**Отвергаем.**

### Рекомендация для компонента 3

**Вариант 3A — engine-side `math.isfinite`, value=null.** AC-B4-08 буквально, stdlib, JSON-safe. `nan_inf: bad` в YAML — фиксированное (не configurable в good), но presence в YAML = «правило без правки кода» (AC-B4-12 intent: правила видны/редактируемы, даже если значение зафиксировано).

---

## 4. Компонент 4: value-encoding для bad (null vs sentinel) — сквозное решение

### Постановка

Когда quality=bad/uncertain/stale — что класть в `TelemetrySample.value`?

`TelemetrySample.value: float | int | bool | str | None` ([domain/models.py:40](apps/edge/collector/src/collector/domain/models.py#L40)) — None уже в типе.

### Вариант 4A — null для bad/quarantine; raw value сохраняется для uncertain/stale (рекомендуемый)

| Quality | value |
|---------|-------|
| good | converted value |
| uncertain | **raw/converted value** (AC-B4-07: out-of-range → uncertain, значение сохраняется) |
| stale | **last value** (или raw — оператор видит последнее известное, но помечено stale) |
| bad | **null** (AC-B4-08 для NaN; экстраполируем на все bad) |
| quarantine | **null** (данные не валидны) |

**Плюсы:**
- AC-B4-07 буквально (uncertain сохраняет значение).
- bad/quarantine → null — UI единообразно рисует «нет данных».
- stale сохраняет значение — оператор видит последнее (UI — штриховка).

**Минусы:**
- stale vs bad семантика значения разная (stale=есть, bad=нет) — документировать.

### Вариант 4B — всегда null кроме good

**Плюсы:** проще.

**Минусы:** AC-B4-07 нарушение (uncertain должен сохранять).

**Отвергаем.**

### Рекомендация для компонента 4

**Вариант 4A.** Зафиксировано в таблице выше; encoder-логика в §9 (evaluator flow).

---

## 5. Компонент 5: Out-of-range (AC-B4-07)

### Требования и ограничения

- **AC-B4-07:** Out-of-range по карте → uncertain/bad, значение сохраняется.
- Вход: `TagMapEntry.range_min`, `range_max` (both optional; [config/models.py:61](apps/edge/collector/src/collector/config/models.py#L61)).
- Применяется к **numeric** value (float/int). bool/str/None — skip range check.
- Проверка на **raw_value** до unit conversion (решение §0.4: conversion linear, не меняет «в диапазоне или нет» физически; raw-range = engineer-range после scale).

> Уточнение: `range_min/max` в карте — это **physical/engineer range** (post-scale, напр. -50..150 °C). Если scale/offset применяются в UnitConverter **после** QualityEngine, то проверять raw_value на physical range — некорректно. **Два варианта:** (a) engine работает до conversion → range в YAML задаётся в **raw units**; (b) engine работает после conversion → range в physical units. Pipeline: RawSample → QualityEngine → UnitConverter → TelemetrySample? Или RawSample → UnitConverter → QualityEngine?

### Вариант 5A — QualityEngine на raw_value, range в raw units (рекомендуемый)

Pipeline B4 (s13): `RawSample → QualityEngine.evaluate(raw_value, ...) → UnitConverter.convert(value) → TelemetrySample`.

`range_min/max` в карте = **raw register range** (до scale). Оператор при конфигурации ставит raw-диапазон (напр. для температуры с scale=0.1: raw range 0..1500 = 0..150°C).

**Плюсы:**
- QualityEngine pure, не зависит от UnitConverter.
- Range проверка — раньше в pipeline (fail fast).
- Тестируется изолированно (без units.yaml).

**Минусы:**
- range в raw units менее интуитивен для инженера (надо знать scale).
- Если scale меняется — range тоже.

### Вариант 5B — QualityEngine после conversion, range в physical units

Pipeline: `RawSample → UnitConverter → QualityEngine(converted_value) → TelemetrySample`.

**Плюсы:** range в physical units (интуитивно: -50..150 °C).

**Минусы:**
- QualityEngine зависит от UnitConverter (s12) — coupling.
- Conversion для NaN/Inf — `scale*nan = nan`, ок, но для None (bad upstream) — TypeError. Нужен guard.
- Тестирование QualityEngine требует units.yaml.

### Вариант 5C — QualityEngine дважды (raw + converted)

**Плюсы:** оба диапазона.

**Минусы:** over-engineering (YAGNI); один диапазон достаточен для фазы 1.

### Рекомендация для компонента 5

**Вариант 5A — QualityEngine на raw_value, range в raw units.** Документировать в map: `range_min/max` = raw register range. **Если** окажется, что инженеры ставят physical range — добавить `range_kind: raw|physical` флаг в map в фазе 2 (YAGNI сейчас). Pipeline в s13: engine **до** converter.

**Out-of-range → uncertain** (default), не bad (AC-B4-07 даёт выбор; uncertain безопаснее — значение есть, но под вопросом). Configurable в YAML:

```yaml
range:
  out_of_range: uncertain   # или bad
```

---

## 6. Компонент 6: Stale (возраст семпла)

### Требования и ограничения

- **AC-B4-12 (косвенно):** stale_threshold_sec в YAML.
- **AC-I3-07:** stuck_value → stale (но это per-tag «no update», см. §0.2 вариант 1 — NormalizerWorker s13).
- Здесь: **per-sample age** = `now - (raw.source_ts or raw.recv_ts)`.
- Только для **aware datetimes** (RawSample.recv_ts — aware по контракту; source_ts optional aware).

### Вариант 6A — Per-sample age, configurable threshold (рекомендуемый)

```yaml
stale_threshold_sec: 3.0   # возраст > 3с → stale
```

```python
age = (now - (raw.source_ts or raw.recv_ts)).total_seconds()
if age > rules.stale_threshold_sec:
    return EvalResult(quality=Quality.STALE, value=raw_value, reason="sample_age_exceeded")
```

**Плюсы:**
- Pure, deterministic, O(1).
- STALE достижим тестом (AC-B4-04).
- value сохраняется (§4).

**Минусы:**
- Не покрывает «tag hasn't sent anything in N sec» (это NormalizerWorker s13).

### Вариант 6B — Per-tag «last seen» tracking в engine

**Идея:** engine держит dict `{tag_id: last_recv_ts}`, при evaluate обновляет и проверяет gap.

**Плюсы:** покрывает stuck_value.

**Минусы:**
- Engine stateful — ломает pure-function тестирование (FR-B4-5).
- Stateful → не thread-safe / не idempotent.
- Это работа NormalizerWorker (s13), не engine.

**Отвергаем** (выносим в s13).

### Рекомендация для компонента 6

**Вариант 6A — per-sample age.** Engine stateless. Per-tag staleness — NormalizerWorker s13 (вне scope).

> **Важно для AC-B4-04 (5 значений):** per-sample stale в engine + stuck_value в s13 — оба производят STALE. Для s11 теста достаточно engine-age: семпл с `source_ts = now - 10s`, threshold=3 → stale.

---

## 7. Компонент 7: Приоритет правил (evaluator order)

### Постановка

Правила: native_quality mapping (OPC/Modbus), NaN/Inf, range, stale, quarantine — все могут сработать на одном RawSample. Какой wins?

### Вариант 7A — Fixed priority order в code (рекомендуемый)

Порядок (от высокого к низкому):

1. **quarantine** (явный флаг от NormalizerWorker: tag not in map) — wins всё.
2. **native_quality mapping** (OPC Bad / Modbus exception) — если токен маппится в bad, не имеет смысла проверять range (значение всё равно невалидно).
3. **NaN/Inf** — non-finite value → bad (перекрывает range, т.к. range сравнение с NaN всегда False).
4. **range** — out-of-range → uncertain.
5. **stale** — возраст → stale.
6. **good** — дефолт.

**Почему такой порядок:**
- quarantine самый высокий — данные помечены невалидными глобально, перебивает всё.
- native_quality (bad) выше NaN — если сервер уже сказал Bad, не пересматриваем.
- NaN выше range — range с NaN не определён.
- range выше stale — свежий но out-of-range → uncertain важнее «старый но в диапазоне».
- stale самый низкий среди «проблем» — возраст — мягкий сигнал.

**Плюсы:**
- Deterministic, документирован, тестируем (каждая пара правил).
- Не configurable в YAML (порядок = семантика, не данные).

**Минусы:**
- Не гибко (но гибкость тут = риск; YAGNI).

### Вариант 7B — Configurable priority в YAML

```yaml
priority: [quarantine, native_quality, nan_inf, range, stale]
```

**Плюсы:** maximum flexibility.

**Минусы:** оператор может сломать семантику; 99% не нужно. **YAGNI.**

### Рекомендация для компонента 7

**Вариант 7A — fixed order в code.** Документирован в docstring + тестах (тест «NaN + out-of-range → bad», «bad native + stale → bad» и т.д.).

---

## 8. Компонент 8: Quarantine trigger

### Требования и ограничения

- AC-B4-04: quarantine должен быть **достижим**.
- Семантика (§7.1 plan): tag map mismatch / unknown new tag (B8/T7) — фаза 2.
- QualityEngine не детектирует tag-map mismatch (не имеет tag_map).

### Вариант 8A — Опциональный флаг `quarantined` в evaluate (рекомендуемый)

```python
def evaluate(
    raw: RawSample,
    map_entry: TagMapEntry | None,   # None = tag not in map
    now: datetime,
    rules: QualityRules,
) -> EvalResult:
    if map_entry is None:
        return EvalResult(quality=Quality.QUARANTINE, value=None, reason="tag_not_in_map")
    ...
```

NormalizerWorker (s13): при consume RawSample ищет tag в map; если нет → передаёт `map_entry=None` → engine → quarantine.

**Плюсы:**
- Engine не зависит от tag_map (получает map_entry или None).
- QUARANTINE достижим тестом (`map_entry=None`).
- B8/T7 (фаза 2) просто начнёт ставить None в новых случаях.

**Минусы:**
- NormalizerWorker должен знать контекст (есть ли тег в map) — но это его работа.

### Вариант 8B — Engine принимает явный enum/quarantine reason

**Плюсы:** explicit.

**Минусы:** NormalizerWorker и так определяет — двойная работа.

### Рекомендация для компонента 8

**Вариант 8A — `map_entry=None` → quarantine.** Минимальный, чистый.

---

## 9. Компонент 9: YAML schema + QualityEngine API (AC-B4-12)

### Требования и ограничения

- **AC-B4-12:** Quality rules — YAML без правки кода.
- **FR-B4-3:** `QualityEngine.apply(rules, sample, map_entry, age)`.
- **FR-B4-5:** pure function для тестов.
- **FR-B4-6:** YAML-driven.

### Вариант 9A — Pydantic model для rules + pure `evaluate()` + reload-at-startup (рекомендуемый)

**Файлы:**
- `config/quality_rules.yaml` — данные.
- `core/quality_engine.py` — `QualityRules` (pydantic) + `QualityEngine` (loads YAML once) + pure `evaluate()`.

**YAML schema (full deliverable):**

```yaml
# quality_rules.yaml — canon для collector (CR-COL-04)
version: 1

stale_threshold_sec: 3.0

# native_quality token → Quality
opcua:
  severity_class:
    good: good
    uncertain: uncertain
    bad: bad
  overrides:
    GoodClamped: uncertain
    GoodLocalOverride: uncertain
    BadWaitingForInitialData: stale
    BadNoData: stale
    BadNoDataAvailable: stale
  unknown_status: uncertain

modbus:
  map:
    timeout: bad
    client_error: bad
    exception.1: bad      # IllegalFunction
    exception.2: bad      # IllegalDataAddress
    exception.3: bad      # IllegalDataValue
    exception.4: bad      # SlaveDeviceFailure
    exception.5: uncertain  # Acknowledge
    exception.6: uncertain  # SlaveDeviceBusy
    exception.8: bad      # MemoryParityError
  unknown_exception: bad

# value rules
value:
  nan_inf: bad            # фиксировано (AC-B4-08)

# range rules
range:
  out_of_range: uncertain # AC-B4-07

# safe defaults
unknown_native_quality: good  # None / не распознанный токен без явного правила
```

**Pydantic model:**

```python
class OpcUaRules(BaseModel):
    severity_class: dict[str, str] = {...}
    overrides: dict[str, str] = Field(default_factory=dict)
    unknown_status: str = "uncertain"

class ModbusRules(BaseModel):
    map: dict[str, str] = Field(default_factory=dict)
    unknown_exception: str = "bad"

class ValueRules(BaseModel):
    nan_inf: str = "bad"

class RangeRules(BaseModel):
    out_of_range: str = "uncertain"

class QualityRules(BaseModel):
    version: int = 1
    stale_threshold_sec: float = 3.0
    opcua: OpcUaRules = Field(default_factory=OpcUaRules)
    modbus: ModbusRules = Field(default_factory=ModbusRules)
    value: ValueRules = Field(default_factory=ValueRules)
    range: RangeRules = Field(default_factory=RangeRules)
    unknown_native_quality: str = "good"
```

**API:**

```python
@dataclass(frozen=True)
class EvalResult:
    quality: Quality
    value: float | int | bool | str | None
    reason: str | None = None

class QualityEngine:
    """Loads quality_rules.yaml once at startup (reload = restart)."""

    def __init__(self, rules: QualityRules) -> None: ...
    @classmethod
    def from_yaml(cls, path: Path) -> "QualityEngine": ...

    def evaluate(
        self,
        raw: RawSample,
        map_entry: TagMapEntry | None,
        now: datetime,
    ) -> EvalResult:
        # pure: no I/O, deterministic по (raw, map_entry, now, self._rules)
        ...
```

**Плюсы:**
- Pydantic валидирует YAML при load (fail fast, не silent).
- `evaluate()` — pure, тестируется без I/O (FR-B4-5).
- YAML = данные, легко редактировать (AC-B4-12).
- Reload-at-startup (YAGNI hot reload).

**Минусы:**
- Pydantic model — ~30 строк boilerplate.

### Вариант 9B — Plain dict YAML + функциональный evaluate

**Идея:** rules = `dict[str, Any]`, evaluate принимает dict.

**Плюсы:** меньше boilerplate.

**Минусы:**
- Нет валидации (typo в YAML → silent wrong quality).
- Нет default-ов (каждый call должен defensive).
- Difficult to document schema.

### Вариант 9C — dataclass rules + toml/json

**Идея:** dataclass + JSON.

**Плюсы:** native python.

**Минусы:** AC-B4-12 и plan §14.2 говорят YAML; config loader уже YAML-based ([config/loader.py](apps/edge/collector/src/collector/config/loader.py)).

### Рекомендация для компонента 9

**Вариант 9A — pydantic `QualityRules` + pure `evaluate()` + YAML.** Валидация, defaults, pure core, YAML-canonical. Reload = restart (AC-B4-12 = «rules в YAML без правки кода», не hot-reload — §0.4).

### 9.4 Evaluator flow (pseudocode — для s11 IMPLEMENT)

```python
def evaluate(self, raw, map_entry, now):
    # 1. quarantine (map_entry None)
    if map_entry is None:
        return EvalResult(QUARANTINE, None, "tag_not_in_map")

    value = raw.raw_value

    # 2. native_quality mapping (OPC/Modbus)
    if raw.native_quality is not None and raw.native_quality != "good":
        q = self._map_native(raw.native_quality)
        if q == BAD:
            return EvalResult(BAD, None, f"native:{raw.native_quality}")
        # uncertain/stale from native — продолжаем проверять value? Нет: native wins для non-good
        # (uncertain OPC + valid value → uncertain; AC-B4-07 out-of-range тоже uncertain —
        #  но native-source uncertain важнее. Решение: native non-good → return immediately.)
        if q == UNCERTAIN:
            return EvalResult(UNCERTAIN, self._encode_value(value, q), f"native:{raw.native_quality}")
        if q == STALE:
            return EvalResult(STALE, self._encode_value(value, q), f"native:{raw.native_quality}")
        # q == GOOD (override) → продолжаем к value/range/stale

    # 3. NaN/Inf
    if isinstance(value, float) and not math.isfinite(value):
        return EvalResult(BAD, None, "nan_or_inf")

    # 4. range (numeric only)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if self._out_of_range(value, map_entry):
            q = Quality(self._rules.range.out_of_range)
            return EvalResult(q, value, "out_of_range")

    # 5. stale (per-sample age)
    ts = raw.source_ts or raw.recv_ts
    if ts is not None and now is not None:
        age = (now - ts).total_seconds()
        if age > self._rules.stale_threshold_sec:
            return EvalResult(STALE, value, "sample_age_exceeded")

    # 6. good
    return EvalResult(GOOD, value, None)

def _map_native(self, token: str) -> Quality:
    # opcua.* / modbus.* / прочее
    if token.startswith("opcua."):
        name = token[len("opcua."):]
        if name in self._rules.opcua.overrides:
            return Quality(self._rules.opcua.overrides[name])
        return self._opcua_class(name)  # prefix: Good*/Uncertain*/Bad*
    if token.startswith("modbus."):
        key = token[len("modbus."):]
        return Quality(self._rules.modbus.map.get(key, self._rules.modbus.unknown_exception))
    return Quality(self._rules.unknown_native_quality)  # unknown → safe default
```

`_encode_value(value, q)`:
- BAD / QUARANTINE → None
- UNCERTAIN / STALE / GOOD → value

---

## 10. Интеграция с существующим кодом (as-is ↔ to-be)

### 10.1 Что меняется в существующих файлах

| Файл | as-is | to-be | В каком шаге |
|------|-------|-------|--------------|
| [modbus/connector.py:182](apps/edge/collector/src/collector/plugins/modbus/connector.py#L182) | success: `native_quality="good"` | `native_quality=None` | **s11** (connector-side contract) |
| [modbus/connector.py:186-196](apps/edge/collector/src/collector/plugins/modbus/connector.py#L186) | error: `native_quality=str(e)` | `native_quality="modbus.<token>"` | **s11** |
| [opcua/subscription.py:108](apps/edge/collector/src/collector/plugins/opcua/subscription.py#L108) | `native_quality=str(status)` | `native_quality=f"opcua.{name}"` | **s11** |
| [opcua/connector.py:164](apps/edge/collector/src/collector/plugins/opcua/connector.py#L164) | error: `native_quality=str(e)` | `native_quality="opcua.exception"` (или конкретнее) | **s11** |

### 10.2 Что не меняется

- `RawSample.native_quality: str | None` — контракт сохраняется (строка, но теперь structured token).
- `Quality` enum — без изменений.
- `TelemetrySample.value: ... | None` — None уже в типе.
- `TagMapEntry.range_min/max` — без изменений.

### 10.3 Где живёт `QualityEngine` instance

- NormalizerWorker (s13) создаёт `QualityEngine.from_yaml(config/quality_rules.yaml)` при старте.
- В s11 — только класс + YAML + unit-тесты (без wiring в worker; wiring = s13).

### 10.4 Тестовый контракт (s11 TDD sequence)

Чекпоинт s11: «5 quality values покрыты тестами; YAML reloadable; NaN/Inf → bad». Отображение в компоненты:

| Чекпоинт | Покрытие |
|----------|----------|
| 5 quality values | §1.5 (bad/uncertain/good via OPC), §2 (bad via Modbus), §3 (bad via NaN), §5 (uncertain via range), §6 (stale), §8 (quarantine via map_entry=None) |
| YAML reloadable | §9 — `from_yaml` при restart; test: edit YAML in tmp_path → new instance → новое правило применяется |
| NaN/Inf → bad | §3 |

---

## 11. Верификация (чекпоинты decompose s11 ↔ этот creative)

| s11 checkpoint | Где решено в creative |
|----------------|----------------------|
| Все 5 Quality достижимы тестами | §1.5, §2, §3, §5, §6, §8 — каждая Quality имеет explicit test-case |
| Правила из YAML без правки кода | §9 — `quality_rules.yaml` + pydantic `QualityRules` |
| NaN/Inf → bad | §3 — `math.isfinite` check, value=null |
| (plan §11) OPC StatusCode → Quality (AC-B3-06) | §1 — severity-class + overrides |
| (plan §11) Modbus exception → Quality | §2 — typed token + code map |
| (plan §11) stale | §6 — per-sample age |
| (plan) map_opcua_status() / map_modbus_exception() | §1 / §2 — методы в engine (`_map_native` dispatches) |

**s11 интерфейс (из decompose) ↔ creative mapping:**

| s11 interface | Creative ref |
|---------------|--------------|
| `class QualityEngine — evaluate(raw, map_entry, now) → Quality` | §9 (`EvalResult` с value+reason; `.quality` accessor) |
| `fn map_opcua_status(status_code) → Quality` | §1.4 — публичная standalone helper `map_opcua_status(name) → Quality` (делегирует в `_rules.opcua`) |
| `fn map_modbus_exception(code) → Quality` | §2 — `map_modbus_exception(token_or_code) → Quality` |
| rules YAML: stale_threshold_sec, out_of_range→uncertain\|bad, nan_inf→bad | §9 (полный schema) |

> **Уточнение API:** decompose s11 обещает `evaluate(...) → Quality` (возвращает Quality). Но для value-encoding (§4) нужен также value + reason. **Решение:** `evaluate()` → `EvalResult` (dataclass с `.quality`, `.value`, `.reason`); `EvalResult.quality` — это Quality. Дополнительно standalone `map_opcua_status()` / `map_modbus_exception()` для direct use / тестов (не через RawSample). **Это расширяет lean-интерфейс s11** — отметить в rewire (§Rewire s11).

---

## 12. Решения по открытым вопросам (summary)

| # | Вопрос | Решение |
|---|--------|---------|
| Q1 | native_quality: free string vs token? | **Structured token** `opcua.<name>` / `modbus.<token>` |
| Q2 | OPC StatusCode extraction | `getattr(status, "name", None) or str(status)`; prefix-class fallback |
| Q3 | NaN check location | Engine (`math.isfinite`) |
| Q4 | value for bad | null (None); uncertain/stale сохраняют value |
| Q5 | range check target | raw_value (engine до converter); range в raw units |
| Q6 | stale semantics | per-sample age (engine); per-tag → s13 |
| Q7 | rule priority | fixed order в code: quarantine > native > NaN > range > stale > good |
| Q8 | quarantine trigger | `map_entry=None` |
| Q9 | YAML reload | restart-only (load once) |
| Q10 | OPC full table | severity-class + ~6 overrides (не 200 строк) |
| Q11 | Modbus code mapping | typed token `modbus.exception.<code>` + YAML per-code |
| Q12 | bad value: null vs sentinel | null |
| Q13 | native non-good + valid value | native wins (return immediately, не объединять с range) |
| Q14 | evaluate return type | `EvalResult(quality, value, reason)`; `.quality` = Quality |

---

## 13. Риски (перенос из plan + оценка после creative)

| Риск | Оценка | Mitigation |
|------|--------|------------|
| asyncua StatusCode.name нестабилен между версиями | средний | prefix-class fallback (`Good*`/`Bad*`/`Uncertain*`); тест с mock status; documented |
| `native_quality` контракт-меняет существующие тесты (test_modbus_connector, test_opcua_connector) | средний | s11 IMPLEMENT обновляет ассерты в существующих тестах (`.native_quality == "timeout"` → `== "modbus.timeout"`); covered в TDD sequence |
| range в raw units неинтуитивен | низкий | документ в map + комментарий в YAML; `range_kind` флаг — фаза 2 если надо |
| Modbus exception code 5/6 как uncertain спорно | низкий | configurable в YAML; default uncertain (повторяем) |
| Engine pure но `now` передаётся снаружи — рассинхрон с recv_ts | низкий | now = `datetime.now(timezone.utc)` в NormalizerWorker (s13); в тестах фиксированный now |
| native non-good short-circuit скрывает out-of-range | низкий | документировано; для bad это ок (значение невалидно); uncertain native + range — оба uncertain, не критично |

---

## 14. Deliverable — что реализует BACK IMPLEMENT s11

### 14.1 Файлы (создание + правки)

**Создание:**
- `apps/edge/collector/src/collector/core/quality_engine.py` — `QualityRules` (pydantic) + `EvalResult` (dataclass) + `QualityEngine` + `map_opcua_status()` + `map_modbus_exception()`
- `apps/edge/collector/config/quality_rules.yaml` — canon rules (§9)
- `apps/edge/collector/tests/unit/test_quality_engine.py` — TDD unit-тесты

**Правки (connector-side contract):**
- [modbus/connector.py](apps/edge/collector/src/collector/plugins/modbus/connector.py) — `native_quality` токены (success=None, error=`modbus.<token>`)
- [opcua/subscription.py](apps/edge/collector/src/collector/plugins/opcua/subscription.py) — `native_quality = f"opcua.{name}"`
- [opcua/connector.py](apps/edge/collector/src/collector/plugins/opcua/connector.py) — error path token
- Существующие тесты connector-ов — обновить ассерты native_quality (test_modbus_connector, test_opcua_connector)

### 14.2 Интерфейсы (lean — без кода)

- `dataclass EvalResult`: `quality: Quality`, `value: float|int|bool|str|None`, `reason: str|None`
- `class QualityEngine`:
  - `__init__(rules: QualityRules)`
  - `from_yaml(path: Path) -> QualityEngine` (classmethod)
  - `evaluate(raw: RawSample, map_entry: TagMapEntry | None, now: datetime) -> EvalResult`
- `fn map_opcua_status(name: str, rules: OpcUaRules) -> Quality` (standalone, pure)
- `fn map_modbus_exception(token: str, rules: ModbusRules) -> Quality` (standalone, pure)
- `class QualityRules(BaseModel)` + sub-models (§9) — pydantic, validates YAML

### 14.3 TDD последовательность (из s11, уточнённая creative)

Vertical slices (per TDD skill — one test → one impl):

1. **RED:** `test_good_when_no_native_quality_and_in_range` → GREEN: minimal `evaluate` returns GOOD.
2. **RED:** `test_nan_inf_returns_bad_null` → GREEN: NaN/Inf check (AC-B4-08).
3. **RED:** `test_out_of_range_returns_uncertain_value_kept` → GREEN: range check (AC-B4-07).
4. **RED:** `test_stale_when_age_exceeds_threshold` → GREEN: stale age check.
5. **RED:** `test_quarantine_when_map_entry_none` → GREEN: map_entry None → QUARANTINE.
6. **RED:** `test_modbus_timeout_token_maps_to_bad` → GREEN: `_map_native` modbus dispatch.
7. **RED:** `test_modbus_exception_code_maps_via_yaml` (code 5 → uncertain) → GREEN: YAML modbus.map.
8. **RED:** `test_opcua_bad_status_maps_to_bad` → GREEN: opcua dispatch + prefix class.
9. **RED:** `test_opcua_override_badwaiting_for_initial_data_to_stale` → GREEN: overrides table.
10. **RED:** `test_rule_priority_nan_beats_range` → GREEN: fixed order.
11. **RED:** `test_yaml_reload_new_instance_applies_edited_rule` → GREEN: `from_yaml` reload.
12. **RED:** `test_bad_value_is_null_uncertain_keeps_value` → GREEN: `_encode_value`.
13. **RED (connector contract):** update `test_modbus_connector` assertions (`modbus.timeout` token); `test_opcua_connector` (`opcua.<name>` token) → GREEN: connector правки.
14. Refactor: extract `_map_native`, `_encode_value`, `_out_of_range`, `_opcua_class`.

### 14.4 Чекпоинт верификации (из s11)

- [x] 5 quality values покрыты тестами — §14.3 slices 1–5 (+ 6–9 for native paths)
- [x] YAML reloadable — §14.3 slice 11 (reload via new instance; restart-only)
- [x] NaN/Inf → bad — §14.3 slice 2

### 14.5 AC traceability

| AC | Slice(s) | Компонент |
|----|----------|-----------|
| AC-B4-04 (5 values reachable) | 1,2,3,4,5 | §1,§2,§3,§5,§6,§8 |
| AC-B4-07 (out-of-range, value kept) | 3,12 | §5,§4 |
| AC-B4-08 (NaN/Inf → bad) | 2 | §3 |
| AC-B4-12 (YAML rules, no code change) | 6,7,8,9,11 | §9 |
| AC-B3-06 (StatusCode → Quality) | 8,9 | §1 |

---

## 15. Next

- **Rewire (§ ниже):** s11 + index — `needs_creative: closed`, blockers ✅.
- **FINISH:** creative artifact done; code_changed: no.
- **Next command:** `BACK IMPLEMENT s11` (новый чат; TDD по §14.3).

---

## Rewire (creative → dependents)

- [ ] **s11-quality-engine.md:**
  - строка `**needs_creative:** yes` → `no — **closed** (CR-COL-04, 2026-07-27)`
  - `**CREATIVE:** CR-COL-04 → ...` → добавить ссылку `[creative-collector-quality-mapping.md](../../creative/v1-p1-collector/creative-collector-quality-mapping.md)`
  - `**Next Phase:** BACK CREATIVE` → `BACK IMPLEMENT`
  - добавить §Creative mapping notes (кратко: EvalResult, token contract, connector правки) со ссылкой на creative
- [ ] **decompose-v1-p1-collector/index.md:**
  - blockers table CR-COL-04: `pending` → `**done** (2026-07-27) ✅`
  - step s11 row: `needs_creative` col `yes` → `no (done)`, `next_phase` → `BACK IMPLEMENT`, `status` → `pending` (снять `needs_creative`)
  - Summary-чеклист s11 — без изменений (implement ещё не done)
- [ ] **activeContext.md** — FINISH router обновит (creative в done)

---

## Handoff

- **Done:** BACK CREATIVE CR-COL-04 — Quality mapping: OPC UA StatusCode (severity-class + overrides), Modbus exception (typed token + per-code YAML), NaN/Inf (engine `math.isfinite`, value=null), out-of-range (raw_value, uncertain, value kept), stale (per-sample age), quarantine (map_entry=None), rule priority (fixed order), YAML schema (pydantic `QualityRules`), `EvalResult(quality,value,reason)`, connector-side token contract (`opcua.<name>` / `modbus.<token>`)
- **Files:** `memory-bank/back/creative/v1-p1-collector/creative-collector-quality-mapping.md`
- **Rewire:** s11-quality-engine.md (link + needs_creative closed + Next Phase BACK IMPLEMENT); decompose index (blockers ✅, status cleared)
- **Next:** `BACK IMPLEMENT s11` (TDD vertical slices §14.3; deliverable §14)
- **Tool / model:** Claude Code + premium-coding (CREATIVE); Cursor + fast-editing (IMPLEMENT)
- **New chat:** yes — one chat = one atomic subtask (creative → implement)

---

**Конец документа.**
