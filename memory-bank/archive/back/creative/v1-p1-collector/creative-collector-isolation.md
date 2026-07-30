# CR-COL-01 — Изоляция источников внутри collector + RestartPolicy + graceful stop

**Creative ID:** CR-COL-01
**Decompose step:** [s04-restart-supervisor.md](../../plan/decompose-v1-p1-collector/s04-restart-supervisor.md)
**Plan:** [plan-v1-p1-collector.md](../../plan/plan-v1-p1-collector.md) (§11.4 RestartPolicy, §11.5 observability, §15.3 graceful shutdown, §17.4 isolation test, R06, ADR-COL-002)
**Дата:** 2026-07-26
**Режим:** BACK CREATIVE
**Уровень:** L4 (T-001)
**AC:** AC-B1-04, AC-B1-05, AC-B1-06, AC-B1-12, AC-HLT-04
**Unblocks:** s04 (BACK IMPLEMENT) → s21 (integration dual-source isolation)

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `architecture-patterns` | модель изоляции (Task vs process), shutdown ordering |
| `improve-codebase-architecture` | границы SourceSupervisor vs CollectorApp vs connector |
| `property-based-testing` | инварианты `compute_backoff` (монotone, cap, jitter bounds) |
| `brainstorming` | не понадобился — компоненты чётко очерчены plan/decompose |
| `grill-me` | блокеров нет; все неясности разрешены ниже |

---

## 0. Постановка проблемы

В одном процессе `collector` (ADR процессов day-1: `collector` ‖ `writer` ‖ `api`) крутятся **2+ источника** — минимум `aps_main` (modbus_tcp) и `skt_geu` (opcua). Требования:

- **AC-B1-04** — сбой одного источника не влияет на поток второго.
- **AC-B1-05** — supervisor рестартует упавший источник по политике (backoff, max attempts).
- **AC-B1-06** — health статус каждого источника: `up` / `reconnecting` / `down` / `degraded`.
- **AC-B1-12** — метрики per-source: uptime, reconnects, `last_ok_ts`, sample_rate.
- **AC-HLT-04** — graceful shutdown: drain queues, disconnect sources.

Открытые вопросы план оставил CREATIVE (CR-COL-01):

1. **Модель изоляции:** supervised `asyncio.Task` на источник достаточно, или сразу process-per-source?
2. **Параметры `RestartPolicy` / формула backoff:** тип jitter, семантика `max_consecutive_failures`, что считать «consecutive failure».
3. **Graceful stop ordering:** как отменять task + гарантировать `disconnect()`, как CollectorApp дожидается drain.

**Граница обсуждения (из plan §17):** **не** обсуждать слияние collector с api — api всегда отдельный процесс (ADR day-1). CR-COL-01 касается только изоляции **внутри** collector.

---

## 1. Компонент 1 — Модель изоляции источников (Architecture)

🎨🎨🎨 ENTERING CREATIVE PHASE: ARCHITECTURE
Decompose step: [s04-restart-supervisor.md](../../plan/decompose-v1-p1-collector/s04-restart-supervisor.md)
Компонент: модель изоляции нескольких источников в одном процессе collector
Требования и ограничения: AC-B1-04 (изоляция), AC-B1-05 (restart), AC-HLT-04 (shutdown); event-loop async service (FastAPI/asyncio); максимум 2 источника в dev, расширяемо; риск R06 «asyncio isolation insufficient» = Низкая вероятность / Высокий impact.

### Вариант 1 — Supervised `asyncio.Task` per source (внутри общего event loop)

Один `asyncio.Task` на источник (`name=f"source:{source_id}"`). Каждый task запускает свой `SourceSupervisor._run()` цикл: `connect → subscribe → wait_until_dead → on Exception: backoff reconnect`. Падение task ловится внутри `_run` (try/except вокруг connect/subscribe), **не** через `task.add_done_callback` — потому что цикл самовосстановления живёт внутри task.

```text
CollectorApp.start()
  ├─ create raw_queue (shared, maxsize из config)
  ├─ for source in sources:
  │     connector = registry.create(source.config)
  │     sup = SourceSupervisor(connector, raw_queue, policy)
  │     await sup.start()        # asyncio.create_task(self._run())
  └─ start normalizer / health writer
```

**Плюсы:**
- Нулевая инфраструктурная сложность: один процесс, один loop, стандартный asyncio.
- Shared `raw_queue` без IPC — `await raw_queue.put(sample)` напрямую (AC-B1-04: «отдельные put paths» = разные task, но одна очередь; backpressure через `await put`).
- `stop()` тривиален: `task.cancel()` + `await task` (ловим CancelledError) + `connector.disconnect()`.
- Метрики per-source — локальные счётчики на supervisor, без кросс-процессного IPC.
- Соответствует уже зафиксированному ADR-COL-002 (Proposed → этот creative его закрывает как Accepted).

**Минусы / риски:**
- R06: если плагин (модбус/opcua lib) бросает **синхронное** блокирующее исключение или зависает в C-коде (не отдаёт управление), он остановит **весь** event loop, а значит и второй источник. Mitigation:契约 плагина `SourceConnector` («плагин не блокирует event loop синхронным I/O > 1ms», см. [interfaces.py:42](apps/edge/collector/src/collector/domain/interfaces.py#L42)) + soak T1 (s25) как регрессионный фильтр.
- Утечка памяти / file descriptors в одном плагине бьёт по всему процессу (но не по «потоку второго источника» на уровне данных — задача второго источника продолжает `put`, просто процесс в целом деградирует). Это приемлемо: AC-B1-04 говорит про **поток данных**, а не про устойчивость процесса к утечкам памяти.
- Сильная корреляция срывов при отказе ОС-уровня (закончились FD) — но это «авария узла», не изоляция источника.

### Вариант 2 — Process-per-source (`multiprocessing` / subprocess)

Каждый источник — отдельный OS-процесс со своим event loop. Supervisor-родитель (collector main) следит за процессами, перезапускает по exit code.

**Плюсы:**
- Жёсткая OS-изоляция: segfault / блокировка C-библиотеки одного плагина не останавливает второй.
- Независимый GIL-поток (но I/O и так отдаёт GIL — выигрыш мнимый для нашего workload).
- Чистый kill `-9` процесса-источника = clean restart.

**Минусы:**
- IPC для `raw_queue`: pickle `RawSample` через pipe/queue — стоимость сериализации на каждый сэмпл (при ~586 тегах × несколько Гц это существенный overhead на edge).
- Усложнение shutdown: нужно дождаться child-процессы, обработать SIGCHLD, тайм-ауты на kill.
- Усложнение метрик/health: IPC для per-source счётчиков либо разделение health-снимка по процессам.
- Конфигурация/плагины должны быть re-importable в child — менеджмент `PluginRegistry` удваивается.
- **Противоречит** зафиксированному ADR day-1 (collector = один процесс) и ADR-COL-002 (Proposed: Task per source).

### Вариант 3 — Hybrid: asyncio.Task per source + внешний supervisor процесс на уровне collector

Task-per-source внутри collector, но collector сам запускается под внешним supervisor (systemd / docker restart=always / s6), который перезапускает **весь** collector при критическом отказе (segfault, OOM, зависание health-check).

**Плюсы:**
- Сохраняет простоту варианта 1 внутри приложения.
- Эскалация «asyncio isolation insufficient» (R06) обрабатывается на уровне деплоя без переписывания кода.
- Соответствует docker-compose (s23) — там уже `restart: unless-stopped` естественно.

**Минусы:**
- Не даёт изоляции **между источниками** внутри одного collector — только изоляцию collector↔writer↔api и авторекавери процесса. Для AC-B1-04 (один источник vs другой) гибрид = вариант 1.
- Двойной уровень «supervisor» может запутать терминологию (внешний OS-supervisor vs внутренний `SourceSupervisor`).

### Рекомендуемый подход: Вариант 1 (supervised asyncio.Task per source), с эскалацией варианта 3 на уровне деплоя

**Обоснование:**
1. ADR-COL-002 уже Proposed в сторону Task-per-source; ADR day-1 фиксирует collector как один процесс. Вариант 2 ломает оба — без доказанной необходимости (R06 вероятность Низкая).
2. AC-B1-04 формулируется про **поток данных** второго источника, а не про OS-изоляцию — Task-per-source это удовлетворяет: task B продолжает `await raw_queue.put(...)` независимо от состояния task A.
3. Стоимость IPC варианта 2 (сериализация RawSample на каждый сэмпл) на edge-нагрузке неоправданна без данных soak.
4. Вариант 3 — это не альтернатива, а **дополнение**: `SourceSupervisor` (внутренний, per-source) + docker `restart`/systemd (внешний, per-process). Они ортогональны; реализация s04 касается только внутреннего.
5. Soak T1 (s25) — регрессионный фильтр для R06: если всплывёт блокировка loop, эскалация до варианта 2 — отдельный creative после soak, **не** сейчас (YAGNI).

**ADR-COL-002: Proposed → Accepted** (после этого creative).

### Руководство по реализации

- Один `asyncio.Task` на источник создаётся в `SourceSupervisor.start()` через `asyncio.create_task(self._run(), name=f"source:{source_id}")`.
- `asyncio.create_task` + имя — **обязательно** (`name=`), для диагностики `asyncio.all_tasks()` и логов при shutdown.
- Внешний loop-level exception handler (`loop.set_exception_handler`) — **не** нужен для AC-B1-04: цикл самовосстановления живёт внутри `_run` (try/except вокруг connect/subscribe), и `CancelledError` отдельно прокидывается. `set_exception_handler` оставляем на уровень `CollectorApp` (s05+), не s04.
- `raw_queue` — **единая** shared `asyncio.Queue` ( создаётся в CollectorApp, не в supervisor). Backpressure = `await put` (см. компонент 3 §edge cases). AC-B1-04 «отдельные put paths» = разные task-продюсеры, **не** разные очереди.
- Изоляция проверяется unit-тестом с двумя fake-коннекторами (см. §верификация): убийство fake A не останавливает fake B `put`.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## 2. Компонент 2 — RestartPolicy / backoff (Algorithm)

🎨🎨🎨 ENTERING CREATIVE PHASE: ALGORITHM
Decompose step: [s04-restart-supervisor.md](../../plan/decompose-v1-p1-collector/s04-restart-supervisor.md)
Компонент: `RestartPolicy` dataclass + `compute_backoff(attempt, policy) → float` + семантика счётчика failures
Требования и ограничения: AC-B1-05 (backoff, max attempts); plan §11.4 default `initial=1.0, max=60.0, max_consecutive_failures=None, jitter=True`; риск «reconnect storm» (plan §11.3) — mitigation «exponential backoff cap 60s; jitter».

### Что считать «failure» и «consecutive»

- **Failure** = любое исключение из `connect()` или из активной подписки (subscribe упала, transport порвался, `read`/push бросил). Не-failure: `CancelledError` (это shutdown, прокидывается).
- **Consecutive failure counter** (`_consecutive_failures`) сбрасывается в 0 при **успешном** `connect()` + хотя бы одном доставленном сэмпле через `subscribe` (т.е. подписка реально ожила). Сброс только по `connect()` недостаточен — connect может формально пройти, но подписка тут же падает (полуоткрытый канал).
- `attempt` в `compute_backoff` = текущее значение `_consecutive_failures` (0-based для первой попытки → `initial_backoff`). После N неудач подряд при `max_consecutive_failures` is not None → source переходит в состояние `down` (AC-B1-06), task переходит в «cold» режим: ждёт ручного restart или внешнего сигнала (health degraded). При `None` — infinite retries (default; edge-сервис должен сам себя лечить).

### Вариант 1 — Exponential ×2, cap, **full jitter** (AWS-style decorrelated)

```python
def compute_backoff(attempt: int, policy: RestartPolicy) -> float:
    expo = min(policy.initial_backoff_sec * (2 ** attempt), policy.max_backoff_sec)
    if not policy.jitter:
        return expo
    return random.uniform(0.0, expo)   # full jitter
```

- `attempt=0` → expo=initial (1.0); `attempt=1` → 2.0; …; `attempt=6` → 64→cap 60.
- Full jitter: равномерно `[0, expo]`. Минимизирует синхронные «reconnect storms» при массовой потере сети (все источники рвутся одновременно и пытаются реконнектить в одной фазе).

**Плюсы:** лучший anti-thundering-herd при 2+ источниках, падающих одновременно (общая сеть/шлюз); простая формула; well-known (AWS architecture blog).
**Минусы:** высокая дисперсия — иногда задержка ~0 при большом expo (быстрый, почти мгновенный реконнект), что может молотить сервер. Для edge с 2 источниками это допустимо (не thousands clients).

### Вариант 2 — Exponential ×2, cap, **equal jitter** (`expo/2 + uniform(expo/2, expo)`)

```python
def compute_backoff(attempt: int, policy: RestartPolicy) -> float:
    expo = min(policy.initial_backoff_sec * (2 ** attempt), policy.max_backoff_sec)
    if not policy.jitter:
        return expo
    return expo / 2 + random.uniform(0.0, expo / 2)
```

**Плюсы:** гарантированная нижняя граница `expo/2` — меньше «мгновенных» реконнектов; сохраняет anti-herd.
**Минусы:** слабее размытие фазы, чем full jitter.

### Вариант 3 — Fixed delay (constant)

**Плюсы:** детерминизм, простейший тест.
**Минусы:** reconnect storm при общей потери сети; медленнее среднего восстановления. **Не** удовлетворяет mitigation «jitter» из plan §11.3.

### Рекомендуемый подход: Вариант 1 (full jitter) — default `jitter=True`

**Обоснование:**
- Edge: ровно те условия, где full jitter выигрывает — 2+ источника за общим шлюзом/сетью, одновременный разрыв → одновременные реконнекты. Anti-thundering-herd важнее пик-латентности.
- Формула тривиальна, тестируется property-based (инварианты ниже).
- `jitter` flag позволяет в тестах отключить (`policy RestartPolicy(jitter=False)`) — детерминированный backoff для assertions (без `sleep` в тестах: тестировать **значение** `compute_backoff`, не реальное ожидание).
- cap 60s зафиксирован plan §11.4 — соблюдается `min(..., max_backoff_sec)`.

### Инварианты (для property-based testing, skill `property-based-testing`)

Для всех `attempt ≥ 0` и `policy` с `initial_backoff_sec > 0`, `max_backoff_sec ≥ initial_backoff_sec`:

1. **Bound (jitter off):** `compute_backoff(attempt, policy(jitter=False)) == min(initial * 2**attempt, max)`.
2. **Monotone cap (jitter off):** последовательность `attempt=0..∞` не убывает и сходится к `max_backoff_sec`.
3. **Range (jitter on):** `0.0 ≤ result ≤ min(initial * 2**attempt, max)`.
4. **Cap:** для `attempt` достаточно большого (`2**attempt * initial ≥ max`) — `result ≤ max_backoff_sec` всегда (даже с jitter).
5. **Determinism toggle:** `jitter=False` → одинаковый результат на одинаковых аргументах (no randomness).

Замечание по тестам: `random` в `compute_backoff` — явно seed-able в тестах (`random.seed`) ИЛИ тестируем `jitter=False` детерминированно + отдельный диапазонный тест на `jitter=True`. Не делать `asyncio.sleep(backoff)` в unit-тестах — только проверять **значение** delay и логику счётчика; реальный sleep покрыть fast-интеграцией с mock-time (`asyncio_loop` + patch `asyncio.sleep`) или опустить (soak).

🎨🎨🎨 EXITING CREATIVE PHASE

---

## 3. Компонент 3 — Graceful stop / shutdown ordering (Architecture)

🎨🎨🎨 ENTERING CREATIVE PHASE: ARCHITECTURE
Decompose step: [s04-restart-supervisor.md](../../plan/decompose-v1-p1-collector/s04-restart-supervisor.md)
Компонент: `SourceSupervisor.stop()` + интеграция в `CollectorApp` shutdown (AC-HLT-04)
Требования и ограничения: plan §15.3 ordering «stop supervisors → drain raw_queue (timeout 10s) → stop normalizer → final snapshot»; §11.3 «subscribe cancel on shutdown: CancelledError propagation; disconnect in finally»; `SourceConnector.disconnect()` — idempotent (interfaces.py).

### Вариант 1 — Cooperative-then-cancel: cancel task → await (swallow CancelledError) → disconnect

```python
async def stop(self) -> None:
    if self._task and not self._task.done():
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
    await self._connector.disconnect()   # idempotent
```

- `task.cancel()` инжектит `CancelledError` в точку await внутри `_run` (обычно `await self._wait_until_dead(sub)` или `await asyncio.sleep(backoff)`).
- `_run` обязан **прокидывать** `CancelledError` (`except asyncio.CancelledError: raise`) — тогда `await self._task` поднимет его, мы глотаем.
- `disconnect()` — **всегда**, в `stop`, не в `_run.finally` (чтобы disconnect был однократным и контролируемым снаружи). `disconnect` idempotent → безопасен даже если плагин уже закрыл transport.

**Плюсы:** минимальный, соответствует plan §15.3 и outline §8; deterministic; нет grace-period таймеров (источник либо отменён, либо уже сам умер — в обоих случаях disconnect корректен).
**Минусы:** cancel «жёсткий» — если плагин в момент cancel делает долгий unsynchronized C-call (не в await), CancelledError сработает только на следующем await. Но契约 плагина (interfaces.py:42) это и так запрещает; для зависшего плагина спасает только внешний supervisor (вариант 3 из компонента 1, уровень деплоя).

### Вариант 2 — Cooperative stop via `asyncio.Event` + grace period, затем cancel

```python
def __init__(...):
    self._stop_event = asyncio.Event()

async def _run(self):
    while not self._stop_event.is_set():
        ...

async def stop(self, grace_sec: float = 5.0):
    self._stop_event.set()
    try:
        await asyncio.wait_for(self._task, timeout=grace_sec)
    except asyncio.TimeoutError:
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
    await self._connector.disconnect()
```

**Плюсы:** плагин может «дочитать» текущий poll-cycle / flush перед выходом (мягче для in-flight данных).
**Минусы:** добавляет grace-таймер и состояние `_stop_event` — сложность; для collector in-flight данных немного (мы push-им, не батч-им); grace period != drain raw_queue (drain — отдельная фаза в CollectorApp, §15.3 шаг 3).

### Рекомендуемый подход: Вариант 1 (cancel + await + disconnect)

**Обоснование:**
- Drain raw_queue — отдельный шаг CollectorApp (§15.3), **не** ответственность supervisor. Supervisor отвечает только за остановку своего источника. Вариант 2 смешивает две ответственности.
- `disconnect()` idempotent + CancelledError propagation в `_run` → вариант 1 корректен и минимален.
- Grace period (вариант 2) — преждевременная общность (YAGNI): источник push-овый, in-flight данных на момент SIGTERM почти нет; reconnect-loop и так прерывается мгновенно.
- Для случая «плагин завис в C-коде» ни один вариант не поможет внутри процесса — это уровень внешнего supervisor (deploй). Не плодить таймеры ради неисправимого.

### Руководство по реализации (shutdown ordering на уровне CollectorApp — относится к s05/s14, **не** s04, но фиксируем для согласованности)

`SourceSupervisor.stop()` (s04) — только cancel+await+disconnect **своего** connector. CollectorApp shutdown (s05+, AC-HLT-04) собирает оркестрацию:

1. `collector_state = stopping`
2. `await asyncio.gather(*(sup.stop() for sup in supervisors))` — параллельная остановка всех источников
3. drain `raw_queue` (`timeout=10s`, plan §15.3) — ждём пока normalizer вычистит
4. stop normalizer worker
5. final health snapshot write
6. exit 0

**s04 реализует только шаг 2-компонент** (`SourceSupervisor.stop`); CollectorApp-оркестрация — отдельный заход (s05/s14). В s04 unit-тестировать `stop()` изолированно.

### Edge cases (зафиксировать в реализации `_run`)

- **`connect` сразу падает** (сервер недоступен): `_consecutive_failures += 1`, `backoff = compute_backoff(...)`, `await asyncio.sleep(backoff)`, повтор. Health → `reconnecting`.
- **`connect` OK, `subscribe` падает** (канал полуоткрыт): то же, но **важно** `disconnect()` перед backoff (否则 resource leak — открытый transport). → `_run` finally: `with contextlib.suppress(Exception): await self._connector.disconnect()` **перед** sleep, если connect успел.
- **`_wait_until_dead` возвращается без исключения** (плагин сам завершил подписку): трактуем как failure → reconnect (плагин не должен сам закрывать, но defensive).
- **`raw_queue.put` блокирует** (queue full): `await put` приостановит `on_sample` → обратное давление на источник. Не кидать, не дропать (drop = data loss, против ТЗ). Health source остаётся `up`, но sample_rate падает — это видно в метриках (AC-B1-12). Для s04 — оставить `await put` как есть; maxsize queue определяется в s05.
- **Двойной `stop()`**: `if self._task and not self._task.done()` гарантирует идемпотентность; повторный `disconnect` безопасен (idempotent contract).
- **`stop()` до `start()`**: `self._task is None` → `if` пропускается, `disconnect()` всё равно вызывается (defensive, плагин мог частично инициализироваться).

🎨🎨🎨 EXITING CREATIVE PHASE

---

## 4. Маппинг на файлы s04 (deliverable)

| Файл | Содержимое (из этого creative) |
|------|--------------------------------|
| `apps/edge/collector/src/collector/util/backoff.py` | `compute_backoff(attempt, policy)` — full jitter (вариант 1 компонента 2); pure-функция. |
| `apps/edge/collector/src/collector/core/restart_policy.py` | `@dataclass(frozen=True) RestartPolicy` — `initial_backoff_sec=1.0, max_backoff_sec=60.0, max_consecutive_failures=None, jitter=True` (plan §11.4 дословно). |
| `apps/edge/collector/src/collector/core/supervisor.py` | `SourceSupervisor` — `start/stop/_run/_on_sample/_wait_until_dead`; счётчик `_consecutive_failures`; state для health (`up`/`reconnecting`/`down`); edge cases §3. |
| `apps/edge/collector/tests/unit/test_supervisor.py` | dual fake isolation (AC-B1-04); backoff монотонность/cap/jitter (инварианты §2); cancel+disconnect (AC-HLT-04); consecutive-failure reset on first sample. |

**Минимальные интерфейсы (из decompose s04, подтверждённые здесь):**

```python
# restart_policy.py
@dataclass(frozen=True)
class RestartPolicy:
    initial_backoff_sec: float = 1.0
    max_backoff_sec: float = 60.0
    max_consecutive_failures: int | None = None   # None = infinite
    jitter: bool = True

# backoff.py
def compute_backoff(attempt: int, policy: RestartPolicy) -> float: ...

# supervisor.py
class SourceSupervisor:
    def __init__(self, connector: SourceConnector, raw_queue: asyncio.Queue[RawSample], policy: RestartPolicy) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    # internal: _run, _on_sample, _wait_until_dead, _consecutive_failures, state
```

**Не входит в s04** (явно вынести за пределы, anti-scope-creep): `raw_queue` creation + maxsize config (s05), CollectorApp shutdown оркестрация (s05/s14), Prometheus metric exposition (s14), external OS-supervisor/docker restart (s23 деплой), loop-level exception handler (CollectorApp, s05+).

---

## 5. Верификация (чекпоинты decompose s04 ↔ этот creative)

- [ ] **Dual fake source isolation (AC-B1-04):** два fake-коннектора в одном loop; fake A бросает в `subscribe`/`connect`; fake B продолжает `put` в `raw_queue`. Assertion: после убийства A, в `raw_queue` продолжают появляться сэмплы с `source_id == B`.
- [ ] **Backoff растёт до max (AC-B1-05):** `jitter=False` policy; подряд N failures → `compute_backoff` последовательность `[1, 2, 4, 8, 16, 32, 60, 60, ...]`. Cap соблюдён.
- [ ] **Backoff range с jitter:** 1000 попыток `compute_backoff(attempt, jitter=True)` → все в `[0, min(initial*2**attempt, max)]`.
- [ ] **`stop()` cancel + disconnect (AC-HLT-04):** после `stop()` — `connector.disconnect()` вызван ровно 1 раз; task done; повторный `stop()` не падает.
- [ ] **`stop()` до `start()`:** не падает, `disconnect()` вызван.
- [ ] **Consecutive reset:** после серии failures + успешный connect + 1 delivered sample → счётчик 0; следующая failure → backoff снова `initial`.
- [ ] **`max_consecutive_failures` exhausted:** при `max_consecutive_failures=3` после 3 failures → state `down`, `compute_backoff` больше не вызывается (или вызывается, но реконнекта нет — фиксировать в реализации как «cold» режим).

**Тестовая стратегия:** без реальных `asyncio.sleep` — patch `asyncio.sleep` (или inject clock), проверять **значения** delay и состояние счётчика/state. Backoff-формула — отдельные unit-тесты pure-функции (property-based где уместно). Dual-isolation — асинхронный тест с двумя fake и событийным управлением (`asyncio.Event` в fake для симуляции падения).

---

## 6. Метрики / observability (AC-B1-06, AC-B1-12 — зафиксировать поля, exposition в s14)

`SourceSupervisor` держит локально (exposition в Prometheus — s14, не s04):

- `_state: SourceState` — `UP` / `RECONNECTING` / `DOWN` / `DEGRADED` (mapping к AC-B1-06).
- `_reconnect_count: int` (= BaseSourceConnector._reconnect_count, синхронизировать).
- `_last_ok_ts: datetime | None` — обновляется на каждый доставленный сэмпл.
- `_consecutive_failures: int`.
- sample_rate — производная (сэмплов/сек), считается в health writer (s14), не хранится в supervisor.

Health-снимок для `healthcheck()` (через `BaseSourceConnector.healthcheck()`, уже есть в interfaces.py:122) — supervisor обновляет `_state`/`_last_ok_ts` на connector'е через helpers. **Не** дублировать health-логику в supervisor — переиспользовать `BaseSourceConnector.healthcheck()`.

State transitions (AC-B1-06):

```text
init → RECONNECTING (попытка connect)
connect+sample OK → UP
connect/subscribe failure → RECONNECTING (+ sleep backoff)
max_consecutive_failures reached → DOWN
queue backpressure (put slow) but samples flow → DEGRADED
shutdown (CancelledError) → (без перехода, задача умирает)
```

---

## 7. Решения по открытым вопросам (summary)

| Вопрос | Решение |
|--------|---------|
| asyncio.Task vs process-per-source? | **Task per source** (вариант 1). Process-per-source — эскалация после soak T1, не сейчас (R06 вероятность Низкая). ADR-COL-002: Proposed → **Accepted**. |
| Тип jitter? | **Full jitter** (`uniform(0, expo)`), `jitter=True` default; toggle off для детерминированных тестов. |
| Семантика `max_consecutive_failures`? | Счётчик consecutive failures; сброс на connect+first-sample; при `None` — infinite (default); при `K` → state `DOWN` (cold). |
| Где живёт drain raw_queue? | **Не** в supervisor. CollectorApp shutdown (s05, §15.3 шаг 3). Supervisor только stop своего connector. |
| `disconnect` в `_run.finally` или в `stop`? | В **`stop`** (контролируемо, однократно); + defensive `disconnect` в `_run` перед backoff, если connect успел (anti resource leak). |
| `_resolve_native_ids`? | Не часть s04-creative; относится к wiring tag-карты источника (s08/s10). В s04 — fake/native_ids напрямую в тестах. |
| Внешний OS-supervisor? | docker `restart`/systemd (s23) — уровень деплоя, **не** код s04. |

---

## 8. Риски (перенос из plan + оценка после creative)

| Risk | Вероятность | Impact | Mitigation (после creative) |
|------|-------------|--------|------------------------------|
| R06 asyncio isolation insufficient | Низкая | Высокий | Task-per-source +契约 плагина (no sync blocking) + soak T1 (s25). Эскалация до process-per-source — отдельный creative если soak всплывёт. |
| Reconnect storm (plan §11.3) | Средняя | Средний | Full jitter + cap 60s (компонент 2). |
| Resource leak при полуоткрытом канале | Средняя | Средний | defensive `disconnect` в `_run` перед backoff (§3 edge cases). |
| Drop vs backpressure на full queue | Низкая | Высокий | `await put` (no drop) — данные не теряем; maxsize/s05. |

---

## 9. Next

- **BACK IMPLEMENT s04** (новый чат): реализовать по §4 deliverable, TDD red→green по §5.
- После s04: s08 (modbus connector, CR-COL-02) и s10 (opcua connector) получат готовый supervisor.
- s21 (integration dual-source) закроет AC-B1-04 end-to-end (этот creative закрывает unit-уровень).
