# CR-COL-02 — Poll groups Modbus: max_gap, max_regs, heterogeneous hz, diag mode

**Creative ID:** CR-COL-02
**Decompose step:** [s08-modbus-connector.md](../plan/decompose-v1-p1-collector/s08-modbus-connector.md)
**Plan:** [plan-v1-p1-collector.md](../plan/plan-v1-p1-collector.md) (§12.2 Poll grouping, AC-B2-05/06/10, AC-B1-03/11)
**Дата:** 2026-07-26
**Режим:** BACK CREATIVE
**Уровень:** L4 (T-001)
**AC:** AC-B2-05, AC-B2-06, AC-B2-10, AC-B1-03, AC-B1-11
**Unblocks:** s08 (BACK IMPLEMENT) → s19 (integration modbus)

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `architecture-patterns` | алгоритм группировки (merge/split), separation of concerns |
| `improve-codebase-architecture` | границы PollScheduler vs Connector vs Config |
| `property-based-testing` | инварианты групп (gap ≤ max, size ≤ max, hz = min) |
| `brainstorming` | не понадобился — компоненты чётко очерчены plan/decompose |
| `grill-me` | блокеров нет; все неясности разрешены ниже |

---

## 0. Постановка проблемы

**Что нужно решить:**

1. **Poll grouping algorithm:** как эффективно группировать регистры Modbus для минимизации количества запросов при соблюдении ограничений на размер PDU и гетерогенные частоты опроса.
2. **ModbusTcpConnector design:** как реализовать subscribe (poll-эмитация) поверх `AsyncModbusClient` + `PollScheduler`, сохраняя контракт `SourceConnector`.
3. **Diag mode:** как обеспечить режим логирования raw register → decoded value для ПНР без изменения продакшн пути.

**Входные данные:**
- Tag map: `list[TagMapEntry]` с `native_id`, `fc`, `datatype`, `hz` (опционально из `PollConfig` или per-tag)
- Config: `poll: { default_hz, groups? }` или auto-derive из карты

**Выходные данные:**
- `list[PollGroup]` → каждая группа → один Modbus request (FC03/04 + contiguous range)
- Connector subscribe: internal poll loop @ group.hz → `on_sample(RawSample)` per tag

**Ограничения:**
- Modbus PDU limit: ~100–125 registers на запрос (стандарт 125 для FC03/04, conservative 100)
- FC3 (holding) и FC4 (input) — разные адресные пространства, нельзя мешать
- Гетерогенные hz внутри группы → hz группы = min(tag hz)
- Bitfield native_id `40200.3` — address 200, bit 3; битовые поля не меняют размер запроса (всё равно читаем целый регистр)

**Критерии успеха (AC):**
- **AC-B2-05:** Смежные регистры группируются; размер группы ≤ max_regs
- **AC-B2-06:** Каждая группа имеет свою частоту; default 1 Hz
- **AC-B2-10:** Diag mode: лог raw regs → decoded (env flag или config)
- **AC-B1-03:** ModbusTcpConnector реализует SourceConnector; работает параллельно с OpcUaConnector
- **AC-B1-11:** subscribe Modbus — polling loop; API единый с OPC UA

---

## 1. Компонент 1: PollScheduler — алгоритм группировки

### Требования и ограничения

Из plan §12.2:
```
1. Load tag map entries for source.
2. Split by function code (3 vs 4).
3. Sort by address.
4. Merge contiguous registers into groups where gap ≤ max_gap (default 0).
5. Split groups exceeding max_registers_per_request (default 100).
6. Assign group poll hz = min(tag hz) in group.
```

Дополнительно:
- native_id формат: `"40XXX"` (FC4) или `"40XXX.Y"` (бит); address = int(native_id[2:5]) для 5-значного, или parse
- FC из `TagMapEntry.fc` (3 или 4); fallback: 40xxx → 4, 30xxx → 3 (если нет fc)
- Если у тега нет явного hz → используем `poll.default_hz` или 1.0
- Bitfield: читаем целый регистр; бит извлекается в decoder (s06 уже реализовано)

### Вариант 1A — Greedy merge (простой, O(n log n))

**Алгоритм:**
1. Разделить все теги на FC3 и FC4.
2. Для каждого FC:
   a. Отсортировать по address (из native_id).
   b. Инициализировать пустой список групп.
   c. Для каждого тега:
      - Если последний регистр последней группы + gap ≤ текущий address, и размер группы + 1 ≤ max_regs → добавить в группу.
      - Иначе → новая группа.
3. Для каждой группы:
   - hz = min(tag.hz или default)
   - native_ids = все native_id в группе (сохраняем для subscribe фильтрации)
4. Вернуть объединённый список групп (FC3 + FC4).

**Плюсы:**
- Простой, детерминированный, легко тестировать.
- O(n log n) из-за сортировки; линейный проход для merge.
- Соответствует плану буквально.

**Минусы:**
- Не оптимален по количеству групп при sparse карте (но для 586 тегов не критично).
- Не учитывает приоритеты (например, «критичные» теги в отдельные группы) — но таких требований нет.

**Пример:**
```
Теги: 40101 (fc3, 1Hz), 40102 (fc3, 1Hz), 40105 (fc3, 0.5Hz), 40200.3 (fc4, 1Hz)
max_gap=0, max_regs=100

FC3:
- Группа 1: [40101, 40102] @ 1Hz (contiguous, gap=0)
- Группа 2: [40105] @ 0.5Hz (gap=3 > 0)

FC4:
- Группа 3: [40200.3] @ 1Hz
```

### Вариант 1B — Optimal bin-packing с приоритетами (overkill)

**Идея:** использовать bin-packing (first-fit decreasing) для минимизации количества групп, учитывая приоритеты (если бы были).

**Плюсы:**
- Теоретически меньше групп → меньше TCP roundtrips.

**Минусы:**
- Значительно сложнее; для 586 тегов выигрыш сомнителен (пинг 1–10ms, 586/100 ~ 6 запросов).
- Нет требований на минимизацию; AC-B2-05 только «смежные + лимит».
- Сложнее тестировать edge cases (packing heuristics).

**Вывод:** over-engineering. Не выбираем.

### Вариант 1C — Config-driven explicit groups + auto-fill

**Идея:** если в `sources.yaml` указаны `poll.groups`, использовать их как «явные» группы; недостающие теги из карты → auto-group по алгоритму 1A в «default» группу.

**Плюсы:**
- Гибкость для ПНР: инженер может явно задать «analog_fast @ 10Hz», «discrete @ 0.1Hz».
- Auto-fill сохраняет простоту для stub/dev.

**Минусы:**
- Дополнительная логика merge «explicit + auto».
- Риск конфликтов: explicit group пересекается с auto?

**Анализ:** из примеров в плане (см. §16.1) группы уже используются для логической сегментации (`analog_fast`, `discrete`), но native_ids не указаны → auto-derive. Это поддерживает оба пути.

**Решение:** поддержать **оба**:
- Если `poll.groups` присутствуют и имеют `native_ids: [...]` → использовать как есть (валидировать, что все native_ids есть в карте).
- Если `native_ids: null` или отсутствуют → auto-derive из карты по алгоритму 1A, применяя `hz` из группы к выведенным тегам.
- Теги из карты, не попавшие ни в одну explicit group → auto-group в «неявную» группу с `default_hz`.

**Это не отдельный вариант, а расширение 1A.**

### Рекомендация для компонента 1

**Выбрать 1A + расширение на explicit groups (1C).**

**Обоснование:**
- Соответствует плану §12.2 буквально.
- Поддерживает явные группы из конфига (гибкость ПНР).
- Простота + детерминизм > теоретический оптимум (для edge не критично).
- Легко тестировать property-based: gap ≤ max_gap, size ≤ max_regs, hz = min.

**Deliverable (интерфейс):**
```python
@dataclass(frozen=True)
class PollGroup:
    name: str
    hz: float
    native_ids: list[str]  # contiguous, same FC, size ≤ max_regs

class PollScheduler:
    @staticmethod
    def build_groups(
        tag_map: list[TagMapEntry],
        *,
        max_gap: int = 0,
        max_regs: int = 100,
        default_hz: float = 1.0,
        explicit_groups: list[PollGroup] | None = None,
    ) -> list[PollGroup]:
        ...
```

**Примечание:** `PollGroup` уже есть в `config/models.py` (без `native_ids` в текущей версии? Нет, есть). Проверить: models.py:15–19 показывает `native_ids: list[str] | None`. Для runtime groups → `list[str]` (не None).

---

## 2. Компонент 2: ModbusTcpConnector — subscribe poll loop

### Требования и ограничения

Из interfaces.py:
```python
async def subscribe(
    self,
    native_ids: list[str],
    on_sample: OnSampleCallback,
) -> Subscription:
    """Push-режим. ... on_sample вызывается serially per connector instance."""
```

Из s08:
- subscribe = internal poll loop @ group hz → on_sample RawSample
- diag mode: log raw regs → decoded (flag)
- discover_tags из локальной карты

Из AC-B1-11:
- subscribe эмулируется polling-ом для Modbus (единое поведение API)

**Ключевой вопрос:** как организовать poll loop(ы) внутри subscribe?

### Вариант 2A — Один asyncio.Task на группу (рекомендуемый)

**Дизайн:**
- В `subscribe(native_ids, on_sample)`:
  1. Построить/использовать `PollScheduler.build_groups(...)` → `list[PollGroup]`.
  2. Для каждой группы создать `asyncio.Task` → `_poll_group(group, on_sample)`.
  3. `_poll_group`: `while not cancelled: await client.read_holding(group.start, group.count); decode per tag; on_sample per tag; await sleep(1/group.hz)`.
  4. Вернуть `Subscription(id, native_ids, cancel_event)`; `cancel()` → set event → все tasks отменяются.
- Все on_sample сериализуются через общий lock или просто через event loop (один loop → serially).

**Плюсы:**
- Параллелизм по группам (разные hz не блокируют друг друга).
- Чёткое разделение: группа = task = один Modbus request.
- Легко наблюдать: каждая группа — отдельный task name `poll:{source}:{group.name}`.
- Соответствует AC-B1-11 (polling emulation).

**Минусы:**
- N групп → N tasks на источник. Для 586 тегов / 100 = ~6 групп → 6 tasks. Не проблема.
- Нужно управлять lifecycle tasks (cancel + await на stop).

**Edge cases:**
- Таймаут группы → quality=bad для всех тегов группы (AC-B2-09); не роняем другие группы.
- Exception на одном регистре группы → bad для него; продолжаем опрашивать остальные (AC-B2-08).
- Reconnect: если `client.connected` упал → `await client.reconnect()`; на fail → backoff (но reconnect policy живёт в supervisor, не здесь; connector только пытается).

**Вопрос:** reconnect внутри connector или delegate в supervisor?

Из AC-B2-07: «TCP разрыв → quality=bad → reconnect → продолжение опроса.»

Из s07 (client): `reconnect() → bool`.

Из supervisor (уже реализовано): `connect → subscribe → wait_until_dead → on fail: backoff → reconnect`.

**Решение:** supervisor владеет reconnect policy. Connector в `_poll_group`:
- Если `read_*` бросает `ModbusClientError` (not connected) или `ModbusTimeoutError` → yield RawSample с `quality=bad`, `native_quality=error`.
- **Не** делает reconnect сам. Supervisor видит «wait_until_dead» (poll task упал или connector health degraded) → reconnect.
- Но: если disconnect случился mid-poll, connector должен уметь восстановить соединение при следующем subscribe? Нет — subscribe вызывается supervisor'ом после connect.

**Уточнение контракта:**
- `connect()` → TCP + session.
- `subscribe()` → старт poll loops (предполагает connected).
- Если во время subscribe соединение упало → poll loop бросает; supervisor ловит, ставит bad quality, делает reconnect, перезапускает subscribe.

**Для connector:** в `_poll_group` просто:
```python
try:
    regs = await self._client.read_holding(...)
except (ModbusClientError, ModbusTimeoutError) as e:
    for tag in group:
        await on_sample(RawSample(..., native_quality=str(e), ...))
    return  # task завершится; supervisor перезапустит
```

### Вариант 2B — Один Task на весь источник (sequential groups)

**Дизайн:** один task перебирает все группы последовательно; после каждой группы `await sleep(min_hz)`.

**Плюсы:**
- Меньше tasks (1 вместо N).

**Минусы:**
- Гетерогенные hz: быстрая группа (10Hz) будет ждать медленную (0.1Hz) → потеря timely samples.
- Нарушение AC-B2-06 (per group frequency).

**Вывод:** не подходит.

### Вариант 2C — External scheduler (APScheduler / aiocron)

**Идея:** delegate poll scheduling в стороннюю библиотеку.

**Плюсы:**
- Готовый код для cron-like scheduling.

**Минусы:**
- Дополнительная зависимость.
- Меньше контроля над error handling / reconnect.
- Overkill для простого «каждые N секунд».

**Вывод:** не выбираем.

### Рекомендация для компонента 2

**Выбрать 2A — один Task на группу.**

**Обоснование:**
- Соответствует AC-B2-06 (per group hz).
- Параллелизм без блокировки.
- Простая модель: группа = task = request.
- Supervisor уже спроектирован под «subscribe падает → reconnect».

**Deliverable (скелет):**
```python
class ModbusTcpConnector(BaseSourceConnector):
    def __init__(self, config: SourceConfig, client: AsyncModbusClient, tag_map: list[TagMapEntry]):
        super().__init__(config)
        self._client = client
        self._tag_map = {e.native_id: e for e in tag_map}
        self._poll_tasks: dict[str, asyncio.Task] = {}  # group_name → task
        self._diag = os.getenv("MODBUS_DEBUG") == "1" or config.extra.get("diag", False)

    async def subscribe(self, native_ids: list[str], on_sample: OnSampleCallback) -> Subscription:
        groups = PollScheduler.build_groups(
            [self._tag_map[nid] for nid in native_ids if nid in self._tag_map],
            max_gap=self._config.poll.max_gap if self._config.poll else 0,
            max_regs=self._config.poll.max_regs if self._config.poll else 100,
            default_hz=self._config.poll.default_hz if self._config.poll else 1.0,
        )
        sub_id = f"sub:{self.source_id}:{uuid4()}"
        for g in groups:
            task = asyncio.create_task(self._poll_group(g, on_sample), name=f"poll:{self.source_id}:{g.name}")
            self._poll_tasks[g.name] = task
        cancel_event = asyncio.Event()
        return Subscription(id=sub_id, tag_ids=native_ids, cancel_event=cancel_event)

    async def _poll_group(self, group: PollGroup, on_sample: OnSampleCallback) -> None:
        period = 1.0 / group.hz
        while True:
            try:
                # Определить FC из первого native_id (все в группе одного FC)
                fc = self._infer_fc(group.native_ids[0])
                addr, count = self._range_from_native_ids(group.native_ids)
                regs = await (self._client.read_holding if fc == 3 else self._client.read_input)(
                    address=addr, count=count
                )
                if self._diag:
                    logger.debug("modbus diag raw: source=%s group=%s regs=%s", self.source_id, group.name, regs)
                for i, nid in enumerate(group.native_ids):
                    raw_val = self._decode(nid, regs[i] if count == 1 else regs)  # для float32 — 2 regs
                    await on_sample(RawSample(
                        source_id=self.source_id,
                        native_id=nid,
                        raw_value=raw_val,
                        recv_ts=self._recv_ts(),
                    ))
            except (ModbusClientError, ModbusTimeoutError) as e:
                for nid in group.native_ids:
                    await on_sample(RawSample(
                        source_id=self.source_id, native_id=nid,
                        raw_value=None, native_quality=str(e), recv_ts=self._recv_ts()
                    ))
                return  # даём упасть; supervisor перезапустит
            await asyncio.sleep(period)
```

**Примечание:** `_decode` делегирует в `decoder.py` (уже реализовано s06). Connector не знает о float32/int/bit — только native_id → TagMapEntry → decoder.

**Diag mode:** если `self._diag`, лог raw regs + decoded (после decode). Формат: `source_id, group, raw_regs, decoded_values`.

---

## 3. Компонент 3: Диагностический режим (AC-B2-10)

### Требования

- **AC-B2-10:** Диагностический режим: log raw register → decoded value (ПНР Ф2.5).
- FR-B2-6: debug log mode env `MODBUS_DEBUG=1`.

**Не должен** влиять на продакшн путь (zero overhead если выключен).

### Вариант 3A — Env flag + conditional log (рекомендуемый)

**Дизайн:**
- `MODBUS_DEBUG=1` → `self._diag = True`.
- В `_poll_group` после `regs = await read_*`:
  ```python
  if self._diag:
      decoded = [self._decode(nid, regs_slice) for nid in ...]
      logger.debug("modbus diag: %s %s raw=%s decoded=%s", source, group, regs, decoded)
  ```
- Дополнительно: можно вывести в отдельный логгер `modbus.diag` с level DEBUG.

**Плюсы:**
- Простой toggle.
- Zero overhead если off (if check + logger disabled).
- Не требует изменения API.

**Минусы:**
- Нужно помнить включить env при ПНР.
- Лог может быть шумным при 1Hz × 586.

**Митigation:** уровень DEBUG; в продакшн логгер modbus.diag = WARNING по умолчанию.

### Вариант 3B — Config-driven per-source

**Дизайн:** в `SourceConfig.extra: { modbus_diag: true }` или `poll: { diag: true }`.

**Плюсы:**
- Явно в конфиге; можно включить для одного источника.

**Минусы:**
- Чуть больше кода для чтения.
- Env всё равно удобнее для разового ПНР.

**Решение:** поддержать оба: env OR config. Env имеет приоритет (override для отладки).

### Рекомендация для компонента 3

**Выбрать 3A + config fallback.**

**Deliverable:**
- Env `MODBUS_DEBUG=1` → diag on для всех modbus источников.
- Config `source.extra.modbus_diag: true` → per-source.
- Log: `logger.getLogger("collector.modbus.diag").debug(...)` с raw + decoded.
- В продакшн: `collector.modbus.diag` level WARNING (не спамит).

---

## 4. Компонент 4: discover_tags + read (sync path)

### discover_tags

- Из локальной карты: `[{native_id, name=tag_id, unit, datatype, description=None}]`.
- Не делает network I/O (Modbus не имеет имён; имена в карте).
- Если карта пуста → `[]`.

### read (on-demand)

- `read(native_ids)` → для каждого: определить FC + address → `read_holding/input` → decode → `RawSample`.
- Используется для health checks или explicit read (не основной путь).
- Ошибки: per-tag bad quality, не exception на весь read.

---

## 5. Интеграция с PluginRegistry + BaseSourceConnector

### Регистрация

В `registry.py` (или entrypoint collector):
```python
from collector.plugins.modbus.connector import ModbusTcpConnector
from collector.plugins.modbus.client import AsyncModbusClient

def _create_modbus(config: SourceConfig, tag_map: list[TagMapEntry]) -> SourceConnector:
    # Parse endpoint "host:port"
    host, port = config.endpoint.split(":")
    client = AsyncModbusClient(host=host, port=int(port))
    return ModbusTcpConnector(config, client, tag_map)

PluginRegistry.register("modbus_tcp", _create_modbus)
```

### Наследование

`ModbusTcpConnector(BaseSourceConnector)`:
- `__init__` вызывает `super().__init__(config)`.
- `source_id`, `protocol` из Base.
- `healthcheck` из Base (можно override `_compute_state` если нужно).
- Реализует abstract: connect, discover_tags, read, subscribe, disconnect.

### Параллельность с OPC UA (AC-B1-03)

- Два источника → два Supervisor → два connector.
- Оба реализуют `SourceConnector`.
- Нет shared state между ними.
- Supervisor isolation (CR-COL-01) уже обеспечивает: сбой одного не роняет другой.

---

## 6. Верификация (чекпоинты decompose s08 ↔ этот creative)

- [ ] **Группы не превышают max_regs (AC-B2-05):** property test: для любых max_gap/max_regs, build_groups → все группы `len(native_ids) ≤ max_regs`.
- [ ] **Gap соблюдён (AC-B2-05):** property: consecutive addresses в группе differ ≤ max_gap + 1 (contiguous + gap).
- [ ] **Hz группы = min (AC-B2-06):** для группы с тегами 1Hz и 0.5Hz → group.hz == 0.5.
- [ ] **subscribe эмулирует poll (AC-B1-11):** mock client; subscribe → task создан; после sleep(period) → on_sample вызван; cancel → task done.
- [ ] **Diag mode (AC-B2-10):** с `MODBUS_DEBUG=1` → в логах raw + decoded; без → нет.
- [ ] **PluginRegistry.create("modbus_tcp") (AC-B1-03):** возвращает ModbusTcpConnector; isinstance(SourceConnector).
- [ ] **Два плагина одновременно:** создать modbus + opcua fake; оба subscribe; оба шлют в shared queue.
- [ ] **Error на одном регистре не роняет группу (AC-B2-08):** mock read возвращает exception для одного; остальные теги группы продолжают приходить (симулировать partial read fail? Или timeout всего запроса → все bad. См. ниже).

**Edge: partial group error.**

Modbus: если запрос 10 регистров, и сервер ответил exception на 5-м → весь response exception? Или partial?

**Анализ:** Modbus exception response — на весь PDU. Нет partial success. Если illegal address на одном → exception на запрос.

**Решение:** таймаут/exception на группу → все теги группы → bad quality (AC-B2-09). Это приемлемо: оператор видит «группа X не читается», а не «5 из 10 bad». Альтернатива (split на single reads) убивает perf.

Документировать в плане/коде: «группа атомарна для ошибок».

---

## 7. Решения по открытым вопросам (summary)

| Вопрос | Решение |
|--------|---------|
| max_gap default? | 0 (из плана §12.2). Можно override в PollConfig. |
| max_regs default? | 100 (conservative; Modbus spec 125). |
| Гетерогенные hz? | min() в группе. |
| Bitfield в группе? | Да; читаем целый регистр; бит в decoder. |
| Reconnect в connector? | Нет; supervisor владеет. Connector на error → bad samples + return (task ends). |
| Diag mode overhead? | Conditional + logger disabled → zero. |
| Explicit groups из config? | Поддержать: native_ids null → auto; non-null → validate + use. |
| Partial group error? | Вся группа bad (Modbus exception атомарен на PDU). |

---

## 8. Риски (перенос из plan + оценка после creative)

| Risk | Вероятность | Impact | Mitigation (после creative) |
|------|-------------|--------|------------------------------|
| R07 586 tags perf on weak edge PC | Низкая | Средний | Batch poll groups (этот creative); профилирование s15/s25. |
| Гетерогенные hz приводят к избыточным группам | Средняя | Низкий | min() hz — приемлемый trade-off; инженер может явно группировать. |
| Diag mode забыт включённым в прод | Низкая | Низкий | Уровень DEBUG; docs «выключить после ПНР». |

---

## 9. Deliverable — что реализует BACK IMPLEMENT s08

### Файлы

1. `apps/edge/collector/src/collector/plugins/modbus/poll_scheduler.py`
   - `class PollScheduler`
   - `build_groups(tag_map, max_gap=0, max_regs=100, default_hz=1.0, explicit_groups=None) → list[PollGroup]`

2. `apps/edge/collector/src/collector/plugins/modbus/connector.py`
   - `class ModbusTcpConnector(BaseSourceConnector)`
   - connect, discover_tags, read, subscribe (poll loops), disconnect
   - diag mode (MODBUS_DEBUG / config.extra)
   - _poll_group, _decode (delegate to decoder), _infer_fc, _range_from_native_ids

3. `apps/edge/collector/tests/unit/test_modbus_connector.py`
   - TDD: red → green
   - Property tests: gap, size, hz=min
   - subscribe poll emulation
   - diag mode toggle
   - error propagation (group bad on exception)

### Интерфейсы (lean)

```python
class PollScheduler:
    @staticmethod
    def build_groups(...) -> list[PollGroup]: ...

class ModbusTcpConnector(BaseSourceConnector):
    async def connect(self) -> None: ...
    async def discover_tags(self) -> list[RawTagDescriptor]: ...
    async def read(self, native_ids: list[str]) -> list[RawSample]: ...
    async def subscribe(self, native_ids: list[str], on_sample: OnSampleCallback) -> Subscription: ...
    async def disconnect(self) -> None: ...
```

### TDD последовательность (из s08)

1. Тесты `test_modbus_connector.py` пишутся первыми → падают.
2. Минимальная реализация PollScheduler (build_groups).
3. Минимальная реализация connector (connect/discover/read без subscribe).
4. subscribe poll loop.
5. Diag mode.
6. Error handling (group bad, per-tag bad).
7. Тесты зелёные.
8. PluginRegistry registration (проверить в интеграционном или отдельном тесте).

### Чекпоинт верификации (из s08)

- [ ] Группы не превышают max_regs
- [ ] subscribe эмулирует poll
- [ ] PluginRegistry.create("modbus_tcp") работает
- [ ] AC-B2-05/06/10, AC-B1-03/11 покрыты

---

## 10. Next

- **BACK IMPLEMENT s08** (новый чат): TDD red→green по §9.
- После s08: s10 (opcua connector) может быть параллельно (не зависит).
- s19 (integration modbus) → валидация end-to-end: emulator Modbus → collector B2 → RawSample в queue.
- Параллельно: CR-COL-04 (quality) → s11, если ещё не сделан.

---

## Приложение A: Примеры группировки (для тестов)

**Вход (stub map фрагмент):**
```yaml
tags:
  - native_id: "40101"
    tag_id: TAI4101
    type: float32
    fc: 3
    hz: 1.0
  - native_id: "40103"
    tag_id: TAI4102
    type: float32
    fc: 3
    hz: 1.0
  - native_id: "40105"
    tag_id: TAI4103
    type: float32
    fc: 3
    hz: 0.5
  - native_id: "40200.3"
    tag_id: XA1201
    type: bit
    fc: 4
    hz: 1.0
```

**max_gap=0, max_regs=100, default_hz=1.0:**

```
FC3 groups:
  - name: "auto_40101", hz: 1.0, native_ids: ["40101", "40103"]  # contiguous, gap=0
  - name: "auto_40105", hz: 0.5, native_ids: ["40105"]

FC4 groups:
  - name: "auto_40200", hz: 1.0, native_ids: ["40200.3"]
```

**Явная группа в config:**
```yaml
poll:
  default_hz: 1.0
  groups:
    - name: analog_critical
      hz: 10.0
      native_ids: ["40101", "40103"]
```

→ build_groups с explicit → вернёт explicit как есть (validate native_ids в карте), остальные авто.

---

## Приложение B: Diag log пример

```
DEBUG collector.modbus.diag: source=aps_main group=auto_40101 raw=[0x4228, 0x0000, 0x4248, 0x0000] decoded=[42.0, 50.0]
```

Формат: `source={source_id} group={group.name} raw={regs} decoded={values}`.

---

**Конец документа.**

## Handoff
- **Done:** BACK CREATIVE CR-COL-02 — Poll groups Modbus: алгоритм группировки (max_gap, max_regs, min hz), дизайн ModbusTcpConnector (poll loop per group), diag mode (MODBUS_DEBUG + config)
- **Files:** `memory-bank/back/creative/creative-collector-modbus-poll-groups.md`
- **Rewire:** s08-modbus-connector.md (link + needs_creative closed + Next Phase BACK IMPLEMENT); decompose index (blockers ✅, status cleared)
- **Next:** `BACK IMPLEMENT s08` (TDD red→green по deliverable §9)
- **Tool / model:** Claude Code + premium-coding (CREATIVE); Cursor + fast-editing (IMPLEMENT)
- **New chat:** yes — one chat = one atomic subtask (creative → implement)
