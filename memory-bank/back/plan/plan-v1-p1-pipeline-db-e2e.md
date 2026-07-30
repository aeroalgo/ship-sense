# BACK PLAN — Pipeline DB E2E: emulator → collector → writer → TimescaleDB

**Task ID:** T-002 (gap-close persistence; cross-cut T-001 + T-008)  
**Plan ID:** `v1-p1-pipeline-db-e2e`  
**Уровень:** L3  
**Роль:** BACK  
**Статус:** decomposed  
**Дата:** 2026-07-29  
**Decompose:** [`decompose-v1-p1-pipeline-db-e2e/index.md`](decompose-v1-p1-pipeline-db-e2e/index.md) — **единственный трекер шагов**  
**SUSPENSION GUARD:** active — plan output unlimited (exhaustive, без telegraph / 200-line cap)

**Триггер:** T-001 edge-runtime-smoke и T-008 mqtt-smoke доказывают сквозной поток только до **writer-stub / framing drain** (`samples/sec > 0` в логе). T-002 s01–s18 реализовали реальный `WriterService` + Timescale hypertables + compose `writer` image, но storage suite (s18) использует **mocks**; live acceptance «данные из эмулятора лежат в `samples`/`events`» **не доказан** ни pytest, ни compose SQL assert. BUGFIX package-path/compose-runtime (2026-07-29) снял QA-1..QA-3 blockers импортов и restart loop — стек поднимается, но **нет теста полного цикла с записью в БД**.

**Scope:** автоматические тесты + compose smoke, которые доказывают:

```text
emulator (MQTT publisher и/или Modbus/OPC I3)
  → broker/transport
  → collector (parse + map + normalizer + IpcCanonicalSink)
  → writer (TCP :9009, flush_batches)
  → TimescaleDB (таблица samples [+ events])
  → SQL assert COUNT / tag_id / value
```

**Не входит:**
- API / session (T-003), FRONT UI (T-004+)
- Shore forward (T-007)
- Production ACL/TLS Mosquitto
- Полный 586-tag Hz soak в CI (отдельный `@pytest.mark.load` / nightly; здесь — минимальный доказательный count)
- Изменение framing-контракта IPC (уже стабилен)
- Новый semantic pack / quarantine redesign (CR-STO-03 закрыт)
- Переписывание mqtt-smoke / edge-runtime-smoke (они остаются regression; этот план **надстраивает** persistence gate)

**Родители / refs:**
- Storage: [`plan-v1-p1-storage.md`](plan-v1-p1-storage.md) · [`implement-v1-p1-storage/`](../implement/implement-v1-p1-storage/index.md) · s17/s18
- MQTT: [`plan-v1-p1-mqtt.md`](plan-v1-p1-mqtt.md) · [`plan-v1-p1-mqtt-smoke.md`](plan-v1-p1-mqtt-smoke.md) · [`implement-v1-p1-mqtt/`](../implement/implement-v1-p1-mqtt/index.md)
- Collector smoke: [`plan-v1-p1-edge-runtime-smoke.md`](plan-v1-p1-edge-runtime-smoke.md)
- BUGFIX paths: [`bugfix-20260729-package-path-compose-runtime.md`](../bugfix/bugfix-20260729-package-path-compose-runtime.md)
- QA storage blocked context: [`qa-20260729-v1-p1-storage.md`](../qa/qa-20260729-v1-p1-storage.md)

**Compose:** `/docker-compose.yml`  
**Канон структуры плана:** аналог `plan-v1-p1-mqtt-smoke.md` + persistence layer из T-002

---

## 1. Goal (цель)

Сделать **доказуемым в автоматических тестах**, что данные, которые эмулятор «пульнул», проходят полный боевой контур и **персистятся в TimescaleDB** с проверяемыми полями (`tag_id`, `value`, `quality`, timestamps), а не только видны как `samples/sec` в логе stub/writer.

**Definition of Done:**

1. Есть pytest-модуль(и) `@pytest.mark.integration` (+ `@pytest.mark.slow` где нужен Docker), который поднимает **реальный** Timescale (testcontainers **или** compose `db`) и **реальный** `WriterService.run_tcp`, прогоняет поток emulator→collector→IPC и делает `SELECT` из `samples` / `events`.
2. MQTT path covered: `MqttPublisherAdapter` / `emulator.mqtt_publish` → Mosquitto → collector MQTT stack → IPC → writer → DB.
3. Modbus (I3) path covered минимум одним тестом: live emulator Modbus → collector Modbus connector (+ Normalizer) → IPC → writer → DB (один стабильный tag, напр. `TAI4101` / native `40101`).
4. Compose smoke script (или pytest-compose helper): `docker compose` (default stack и/или `--profile mqtt-dev`) → `psql`/`asyncpg` COUNT(`samples`) > 0 в окне 60 s после healthy.
5. Тесты **не** мокают `SamplesRepo.insert_batch` / `EventsRepo.insert_batch` на happy-path E2E (моки допустимы только в negative/unit соседних suite).
6. Документирована матрица «что доказывает pytest / что доказывает compose / что остаётся nightly load».
7. Runner contract: из корня репо `.venv/bin/pytest …` с `pythonpath` из `pyproject.toml` (BUGFIX уже добавил); marker `e2e` или reuse `integration`+`slow` — зафиксировать в `pyproject.toml`.

---

## 2. Контекст / мотивация / gap matrix

### 2.1 Что уже доказано

| Слой | Доказательство | Что *не* доказывает |
|------|----------------|---------------------|
| MQTT plugin + Mosquitto E2E | `apps/edge/collector/tests/integration/test_mqtt_e2e.py` → **MockSink** | Persist в PSQL |
| MQTT compose smoke | mqtt-smoke s01–s07 → writer log `samples/sec` | Реальный writer был stub на момент smoke; сейчас image real, но **нет SQL assert** |
| Modbus/OPC live emulator | `test_modbus_emulator.py` / `test_opcua_emulator.py` → IntegrationSink in-memory | IPC + DB |
| IPC framing | `test_ipc_sink.py` (mock TCP peer) | Writer decode + DB insert |
| Writer batch / repos | `tests/storage/test_writer_batch.py`, `test_samples_repo.py` — **AsyncMock session** | Live hypertable + alembic |
| Storage «integration» s18 | `test_storage_integration.py` — mocks | Emulator/collector path |
| Compose s17 wiring | `test_s17_integration.py` — YAML/Dockerfile static asserts | Live data path |
| Load 586 Hz | `test_load_586hz.py` — CountingRepo mock | Real DB write |

### 2.2 Критическая дыра

```mermaid
flowchart LR
  subgraph proven ["Уже доказано"]
    E[emulator publish] --> B[broker / Modbus]
    B --> C[collector normalize]
    C --> S[MockSink / writer log samples/sec]
  end
  subgraph missing ["Дыра этого плана"]
    C2[IpcCanonicalSink] --> W[WriterService TCP]
    W --> DB[(samples / events)]
    DB --> A[SQL assert]
  end
  C -.->|нет автоматического моста с assert| C2
```

**Пользовательский запрос (канон):** «тесты как эмулятор пуляет данные, мы их принимаем и пишем в базу — прогнать весь цикл вместе с записью в БД».

### 2.3 Почему нельзя «просто расширить s18 mocks»

s18 закрыл contract/correlation/quota/load на уровне **сервисных границ storage**. Persistence E2E — другой уровень: **transport + framing + ORM + hypertable + migrations**. Смешивать в один файл с mocks = ложное чувство покрытия. Новый suite / plan id обязателен.

---

## 3. Architecture (целевой test harness)

### 3.1 Два транспортных контура (оба в scope)

#### Contour A — MQTT (primary для этого плана; denser fixtures уже есть)

```text
MqttPublisherAdapter (seed=42, panel=aps[,geu])
  → Mosquitto :1883
  → MqttConnector + channel_map + Normalizer
  → IpcCanonicalSink → WriterService.run_tcp
  → SamplesRepo / EventsRepo → Timescale samples/events
  → SELECT tag_id IN ('TAI4101', ...) AND COUNT(*) >= N
```

Ожидаемые tag_id из maps (канон):
- APS.TAI4101 → `TAI4101`
- GEU.TAI4101 → `TGEU4101`
- Discrete/event → `DIA1401` / `EVA0101` и зеркала GEU (см. `mqtt_channels_*.yaml`)

#### Contour B — Modbus I3 (secondary; доказывает default compose path без mqtt-dev)

```text
ModbusServerAdapter (emulator tags_stub / integration fixture)
  → ModbusTcpConnector + tag_map
  → Normalizer
  → IpcCanonicalSink → WriterService.run_tcp
  → samples
  → SELECT tag_id = 'TAI4101' (или map из fixture) COUNT >= 1
```

OPC UA — **опциональный** Phase D (не блокирует DoD); достаточно Modbus + MQTT.

### 3.2 Слои тестов (ADR-PIPE-001 — layered gates)

| Layer | Имя | Инфра | Что поднимаем | Assert |
|-------|-----|-------|---------------|--------|
| **L0** | Writer←IPC unit-ish | in-proc TCP | WriterService + real asyncpg session + alembic | framing frame → row in `samples` |
| **L1** | Pipeline in-proc E2E | testcontainers: Timescale (+ Mosquitto for MQTT) | publisher/connector + Normalizer + IpcCanonicalSink + WriterService | SQL COUNT + value approx |
| **L2** | Compose persistence smoke | docker compose (уже существующие сервисы) | emulator[+mqtt] + collector[+mqtt] + writer + db | `psql -c "SELECT count(*) FROM samples"` > 0 |

**Рекомендация:** реализовать **L0 → L1 → L2** в этом порядке. L0 даёт быстрый red/green без Mosquitto; L1 — полный цикл в CI с Docker; L2 — production wiring acceptance (закрывает QA-3 live acceptance для storage).

### 3.3 Timescale test fixture (L0/L1)

**Вариант выбранный (ADR-PIPE-002):** `testcontainers` с образом `timescale/timescaledb:2.14.2-pg16` (тот же, что compose `db`).

Фикстура (новый модуль, предпочтительно `tests/pipeline/conftest.py` или `tests/storage/conftest_pipeline.py`):

1. Старт контейнера, expose 5432.
2. `DATABASE_URL=postgresql+asyncpg://shipsense:shipsense@host:port/shipsense` (+ sync `postgresql+psycopg://…` для alembic).
3. `alembic upgrade head` через `subprocess` или Alembic API с `migration_database_url()` из `apps.edge.storage.__main__`.
4. `async_sessionmaker` yield session / engine.
5. Teardown: dispose engine, stop container.

**Запрещено:** SQLite / non-Timescale Postgres — hypertable DDL (`create_hypertable`) упадёт; это не fallback, а явный skip/`pytest.fail` с понятной ошибкой если образ недоступен.

**Skip policy:** если Docker daemon недоступен → `@pytest.mark.skip` с reason `Docker required for pipeline DB E2E` (не silent pass). Marker `integration` + `slow`.

**Альтернатива (отклонена как единственный путь):** только compose L2 без L1 — медленнее feedback, хуже локализует framing vs SQL bugs. Compose остаётся обязательным L2 gate, не единственным.

### 3.4 Writer harness (общий для L0/L1)

```python
# Псевдо-контракт фикстуры (имена зафиксировать в IMPLEMENT)
async def writer_tcp_service(db_session) -> tuple[WriterService, tuple[str, int]]:
    samples_repo = SamplesRepo(db_session)
    events_repo = EventsRepo(db_session)
    service = WriterService(
        session=db_session,
        samples_repo=samples_repo,
        events_repo=events_repo,
        flush_interval_ms=50,  # ускорить тест; production default 100
        max_batch_size=5000,
    )
    # bind ephemeral port 127.0.0.1:0
    server_task = asyncio.create_task(service.run_tcp("127.0.0.1", 0))
    # получить фактический port из service._server.sockets[0]
    yield service, ("127.0.0.1", port)
    await service.shutdown()
    await server_task
```

**Важно:** `WriterService.run_tcp` сейчас не экспортирует bound port до listen. IMPLEMENT обязан либо:
- (A) расширить `run_tcp` / добавить `start_tcp()` возвращающий `(host, port)` после `start_server`, **или**
- (B) в тесте вызвать `asyncio.start_server` wrapper / monkeypatch — **запрещено** как обход: правим production API минимально (вариант A предпочтителен).

Минимальный production change (разрешён планом):

```python
async def start_tcp(self, host: str = "0.0.0.0", port: int = 0) -> tuple[str, int]:
    self._server = await asyncio.start_server(self._handle_client, host, port)
    socks = self._server.sockets
    if not socks:
        raise RuntimeError("writer TCP server has no sockets")
    bound = socks[0].getsockname()
    return bound[0], int(bound[1])

async def run_tcp(self, host: str = "0.0.0.0", port: int = 9009) -> None:
    await self.start_tcp(host, port)
    try:
        await self.writer_loop()
    finally:
        await self.shutdown()
```

`__main__.py` продолжает `await service.run_tcp(...)` — поведение compose не меняется.

### 3.5 Collector wiring в L1 (без полного CollectorApp — допустимо)

Для MQTT L1 **reuse pattern** из `test_mqtt_e2e.py`:
- `MqttConnector` + `RawConsumer` + `Normalizer` + `SourceSupervisor` + `RestartPolicy`
- Sink = **`IpcCanonicalSink((host, port))`** вместо `MockSink`
- Publisher = `aiomqtt.Client` publish fixture **или** `MqttPublisherAdapter.publish_loop(iterations=N)`

Для Modbus L1 — reuse `modbus_integration` fixture pattern, но sink → `IpcCanonicalSink`.

**Полный `CollectorApp` / bootstrap** — Phase C (L1b): один тест, который вызывает `build_collector_app` / runtime bootstrap с temp sources YAML указывающим на testcontainer broker + writer endpoint. Это закрывает «production entrypoint» gap; Phase A/B могут остаться на explicit wiring (быстрее debug).

### 3.6 Compose L2 smoke

#### Default stack (Modbus path)

```bash
docker compose up -d --build db writer emulator collector
# wait healthy
docker compose exec -T db psql -U shipsense -d shipsense -c \
  "SELECT count(*) AS n FROM samples;" 
# expect n > 0 within 60s poll
```

Collector env уже: `SHIPSSENSE_WRITER_ENDPOINT=writer:9009`, `SHIPSSENSE_SMOKE_SOURCES=aps_main` (BUGFIX).

#### mqtt-dev profile

```bash
docker compose --profile mqtt-dev up -d --build db writer mosquitto collector-mqtt emulator-mqtt
# wait healthy
docker compose exec -T db psql -U shipsense -d shipsense -c \
  "SELECT tag_id, count(*) FROM samples GROUP BY 1 ORDER BY 1;"
# expect TAI4101 and/or TGEU4101 rows
```

**Script:** `scripts/smoke-pipeline-db.sh` — exit 0/1, poll interval 2s, timeout 60s, печатает last COUNT. Pytest wrapper optional: `tests/pipeline/test_compose_db_smoke.py` помечает `@pytest.mark.slow` и вызывает script через subprocess **или** дублирует poll на localhost:5432.

**Зависимость:** `collector-mqtt` в compose сейчас `depends_on: writer` + mosquitto, но **не** `db` напрямую — OK, т.к. writer depends on db healthy и делает alembic upgrade. Проверить, что writer успевает migrate до первого flush (start_period). При flaky — добавить `collector-mqtt depends_on db: service_healthy` (минимальный compose tweak, разрешён).

### 3.7 Semantic / quarantine в E2E

По умолчанию L0/L1 **без** ship-pack load (`quarantined_tags=None`) — проще assert quality=GOOD.  
Один optional тест L1c: load `ship-pack/makarov` → убедиться, что known-good tags всё ещё пишутся; quarantine dual-path не ломает COUNT. Не блокирует DoD Phase A/B.

---

## 4. Требования (детализация)

### 4.1 Functional

| ID | Требование |
|----|------------|
| FR-1 | Emulator MQTT публикует ≥1 analog payload; после flush в БД есть строка `samples` с `tag_id='TAI4101'` |
| FR-2 | Значение `samples.value` соответствует payload (approx float, tol 1e-6 или pytest.approx) |
| FR-3 | `quality` ∈ {0,1,2,3,4} и для happy-path analog без dirt = 0 (GOOD) |
| FR-4 | Lifecycle MQTT transition → ≥1 row в `events` с ожидаемым `event_name` (напр. `aps.threshold.exceeded`) при том же сценарии, что `test_mqtt_e2e` |
| FR-5 | Modbus emulator constant temp → ≥1 `samples` row для mapped tag |
| FR-6 | Compose L2: после healthy stack `count(*) FROM samples` > 0 |
| FR-7 | Idempotent / conflict: повторная отправка того же `(tag_id, ts)` не создаёт дубликат PK (ON CONFLICT path) |
| FR-8 | Ошибка БД / отказ migrate → тест падает с явной ошибкой (не silent skip кроме Docker-unavailable) |

### 4.2 Non-functional

| ID | Требование |
|----|------------|
| NFR-1 | L0 < 30 s wall; L1 MQTT < 90 s; L2 compose smoke < 120 s poll window |
| NFR-2 | Тесты изолированы: уникальный DB per testcontainer session; truncate или fresh container между module |
| NFR-3 | Не требуют ручного `PYTHONPATH=…` — `pyproject.toml` pythonpath достаточен |
| NFR-4 | Marker: `integration` + `slow`; опционально новый `e2e` в `pyproject.toml` / root conftest |
| NFR-5 | CI: L0+L1 запускаются когда Docker доступен; L2 — manual/parent или nightly job |

### 4.3 Out of scope (явный отказ)

- Точный Hz = 586 в L1/L2 (это `test_load_586hz` + nightly)
- Проверка compression/retention policies (s16) в E2E
- UI / API query trend endpoint
- Multi-host distributed broker

---

## 5. Acceptance Criteria

### 5.1 Новые AC

| ID | Критерий | Verify |
|----|----------|--------|
| **AC-PIPE-01** | L0: framed IPC sample → `samples` row exists | pytest |
| **AC-PIPE-02** | L0: framed IPC event → `events` row exists | pytest |
| **AC-PIPE-03** | L1 MQTT: publisher → mosquitto → collector stack → writer → `samples.tag_id='TAI4101'` COUNT≥1 | pytest + testcontainers |
| **AC-PIPE-04** | L1 MQTT: lifecycle exceeded → `events` COUNT≥1 с ожидаемым `event_name` | pytest |
| **AC-PIPE-05** | L1 Modbus: emulator → connector → writer → `samples` COUNT≥1 | pytest |
| **AC-PIPE-06** | L1: `WriterService.start_tcp` / bound ephemeral port работает; `__main__` run_tcp не сломан | unit + L0 |
| **AC-PIPE-07** | L2 compose default: `scripts/smoke-pipeline-db.sh` exit 0, samples count>0 | script / parent |
| **AC-PIPE-08** | L2 compose mqtt-dev: samples содержат `TAI4101` или `TGEU4101` | script |
| **AC-PIPE-09** | Документ матрицы доказательств в implement step / README fragment | docs |
| **AC-PIPE-10** | Existing suites зелёные: `tests/storage/` + mqtt e2e + emulator mqtt tests | regression |

### 5.2 Inherited AC (переоткрыть / закрыть)

| AC | Было | Этим планом |
|----|------|-------------|
| AC-INT-01 (IPC framing) | unit + stub | **+ live writer + DB** |
| AC-INT-03 (day-1 count) | ослаблен до samples/sec | **SQL count > 0** на compose |
| AC-MQTT-30 | compose samples/sec | **+ DB rows for MQTT tags** |
| s17 «persisted count совпадает» | wiring only | **реально проверить** |

---

## 6. Компоненты и файлы

### 6.1 Create

| Путь | Назначение |
|------|------------|
| `tests/pipeline/__init__.py` | пакет pipeline E2E |
| `tests/pipeline/conftest.py` | fixtures: timescale container, alembic upgrade, async engine/session, writer_tcp, mqtt_broker (reuse/import or wrap collector conftest) |
| `tests/pipeline/test_writer_ipc_db.py` | L0: IPC frame → samples/events |
| `tests/pipeline/test_mqtt_pipeline_db.py` | L1 Contour A |
| `tests/pipeline/test_modbus_pipeline_db.py` | L1 Contour B |
| `tests/pipeline/test_compose_db_smoke.py` | L2 optional pytest wrapper (skip if no compose) |
| `scripts/smoke-pipeline-db.sh` | L2 compose poll COUNT |
| `memory-bank/back/implement/implement-v1-p1-pipeline-db-e2e/` | после DECOMPOSE/IMPLEMENT |

### 6.2 Modify

| Путь | Изменение |
|------|-----------|
| `apps/edge/storage/writer.py` | `start_tcp` + рефактор `run_tcp` (ADR-PIPE-003) |
| `pyproject.toml` | `testpaths += "tests/pipeline"`; marker `e2e` (optional); dev dep уже имеет `testcontainers` |
| `tests/conftest.py` / `tests/storage` markers | register `e2e` если добавлен |
| `docker-compose.yml` | при необходимости: `collector-mqtt.depends_on.db`; без ломки mqtt-dev |
| `apps/edge/collector/README.md` и/или `infra/timescale/README.md` | команды L2 smoke + expected SQL |
| `tests/storage/test_s17_integration.py` | опционально ссылка/не дублировать static asserts |

### 6.3 Без изменений (reuse)

- `IpcCanonicalSink` framing
- `MqttPublisherAdapter` / `emulator.mqtt_publish`
- `MqttConnector`, channel maps, Normalizer
- Alembic revisions 001–006
- `SamplesRepo` / `EventsRepo` SQL
- Compose services emulator / writer / db / mosquitto / collector-mqtt / emulator-mqtt

### 6.4 Dependencies (Python)

Уже в `pyproject.toml` optional `dev`: `pytest`, `pytest-asyncio`, `testcontainers>=4`.  
Проверить наличие образа Timescale через Docker; при отсутствии community module для Timescale — использовать `PostgresContainer` **нельзя** (нет hypertable). Использовать generic `DockerContainer("timescale/timescaledb:2.14.2-pg16")` + wait `pg_isready` + env `POSTGRES_*`.

Пример каркаса фикстуры:

```python
@pytest.fixture(scope="session")
def timescale_url() -> Iterator[str]:
    if shutil.which("docker") is None:
        pytest.skip("Docker required for pipeline DB E2E")
    container = DockerContainer("timescale/timescaledb:2.14.2-pg16")
    container.with_env("POSTGRES_USER", "shipsense")
    container.with_env("POSTGRES_PASSWORD", "shipsense")
    container.with_env("POSTGRES_DB", "shipsense")
    container.with_exposed_ports(5432)
    container.start()
    host = container.get_container_host_ip()
    port = container.get_exposed_port(5432)
    # wait ready...
    url = f"postgresql+asyncpg://shipsense:shipsense@{host}:{port}/shipsense"
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        env={**os.environ, "DATABASE_URL": url.replace("+asyncpg", "+psycopg")},
        cwd=ROOT,
    )
    yield url
    container.stop()
```

---

## 7. Стратегия внедрения (фазы)

### Phase A — L0 Writer IPC → DB (фундамент)

**Цель:** один framed sample/event → rows без emulator/collector.

**Шаги IMPLEMENT (черновик):**
1. `start_tcp` в `WriterService`.
2. Fixture Timescale + alembic.
3. Тест: открыть TCP, отправить length-prefixed JSON envelope sample, wait flush, `SELECT`.
4. Тест: event envelope → `events`.

**Prove:** `AC-PIPE-01`, `AC-PIPE-02`, `AC-PIPE-06`.

### Phase B — L1 MQTT full cycle

**Цель:** emulator publisher → DB.

1. Reuse mosquitto fixture из collector conftest (или дублировать в `tests/pipeline` чтобы не тянуть collector tests package quirks).
2. Wire connector/consumer/supervisor + `IpcCanonicalSink`.
3. Publish APS analog fixture / `MqttPublisherAdapter` iterations=3.
4. Assert `TAI4101` in samples; value ≈ payload.
5. Lifecycle publish → events assert.

**Prove:** `AC-PIPE-03`, `AC-PIPE-04`.

### Phase C — L1 Modbus cycle

1. Поднять `ModbusServerAdapter` (как integration fixture).
2. Connector + Normalizer + IPC sink + writer.
3. Assert sample count ≥1.

**Prove:** `AC-PIPE-05`.

### Phase D — L2 Compose smoke + docs

1. `scripts/smoke-pipeline-db.sh` (default + mqtt-dev modes via args).
2. Optional pytest wrapper.
3. README / timescale README commands.
4. Compose depends_on tweak if flaky.

**Prove:** `AC-PIPE-07`, `AC-PIPE-08`, `AC-PIPE-09`.

### Phase E — Hardening (QA)

1. Conflict/idempotency FR-7.
2. Regression full suite.
3. Optional bootstrap/`CollectorApp` single test.
4. BACK QA artifact.

---

## 8. Decompose (трекер)

**Канон статусов / очереди:** только [`decompose-v1-p1-pipeline-db-e2e/index.md`](decompose-v1-p1-pipeline-db-e2e/index.md) (`s01`…`s08`).  
План **не** хранит checkbox-чеклисты sNN.

| step | title (ссылка в index) | code_surface | AC |
|------|------------------------|--------------|-----|
| s01 | WriterService.start_tcp | service | AC-PIPE-06 |
| s02 | Timescale testcontainer fixture | infra | ADR-PIPE-002 |
| s03 | L0 IPC → samples/events | test | AC-PIPE-01/02 |
| s04 | L1 MQTT → samples | test | AC-PIPE-03 |
| s05 | L1 MQTT lifecycle → events | test | AC-PIPE-04 |
| s06 | L1 Modbus → samples | test | AC-PIPE-05 |
| s07 | compose smoke script | infra | AC-PIPE-07/08 |
| s08 | docs matrix + markers | infra | AC-PIPE-09/10 |

---

## 9. Детальные тест-сценарии (код-уровня для IMPLEMENT)

### 9.1 L0 sample (обязательный скелет)

```python
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_ipc_sample_persists_to_samples(writer_endpoint, db_session):
    sink = IpcCanonicalSink(writer_endpoint, connect_attempts=10, retry_delay=0.05)
    await sink.connect()
    ts = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
    sample = TelemetrySample(
        tag_id="TAI4101",
        value=82.5,
        unit="degC",
        source_ts=ts,
        edge_ts=ts,
        quality=Quality.GOOD,
        source_id="pipeline-l0",
    )
    await sink.write_sample(sample)
    await sink.flush()
    await asyncio.sleep(0.3)  # flush_interval
    row = await db_session.execute(
        text("SELECT value, quality FROM samples WHERE tag_id=:t AND ts=:ts"),
        {"t": "TAI4101", "ts": ts},
    )
    got = row.one()
    assert float(got.value) == pytest.approx(82.5)
    assert int(got.quality) == 0
```

### 9.2 L1 MQTT (обязательный скелет)

```python
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_mqtt_emulator_persists_analog_to_db(
    mqtt_broker, writer_endpoint, db_session
):
    # setup connector/consumer/supervisor as in test_mqtt_e2e
    # sink = IpcCanonicalSink(writer_endpoint)
    # publish APS.TAI4101 analog.json OR MqttPublisherAdapter iterations=2
    # wait until SELECT count(*) FROM samples WHERE tag_id='TAI4101' >= 1
    ...
```

### 9.3 L2 script contract

```bash
#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-default}"  # default | mqtt
TIMEOUT="${TIMEOUT:-60}"
# compose up ...
# loop: n=$(docker compose exec -T db psql -U shipsense -d shipsense -Atc 'SELECT count(*) FROM samples')
# [[ "$n" -gt 0 ]] && exit 0
# timeout → echo "FAIL: samples still 0 after ${TIMEOUT}s" >&2; exit 1
```

**Запрещено:** `exit 0` при пустой таблице; запрещён fallback «если БД недоступна — skip success».

---

## 10. Риски и решения

| ID | Риск | P | I | Решение |
|----|------|---|---|---------|
| R1 | testcontainers + Timescale медленный pull | M | M | session-scoped fixture; document `docker pull` в README |
| R2 | Flaky flush timing | H | M | `flush_interval_ms=50` + poll loop (не fixed sleep-only); timeout явный AssertionError |
| R3 | `run_tcp` blocks / port 0 API отсутствует | H | H | Phase A `start_tcp` (ADR-PIPE-003) |
| R4 | Writer `__main__` держит одну session на всё время — ok for compose; tests need own session | M | M | test harness не использует `__main__`, только WriterService |
| R5 | MQTT tag map mismatch publisher channel_id | L | H | reuse maps из `config/maps/mqtt_channels_*.yaml`; assert known IDs |
| R6 | Compose collector restart / duplicate native_id | M | H | уже BUGFIX `SHIPSSENSE_SMOKE_SOURCES=aps_main`; L2 default path relies on it |
| R7 | alembic URL driver mismatch | L | H | reuse `migration_database_url()` (+psycopg) |
| R8 | Parallel pytest modules share one DB | M | M | session scope + truncate between tests OR function-scoped schema; выбрать truncate `samples`/`events` в autouse fixture |
| R9 | CI без Docker | M | M | skip with clear reason; parent/QA documents Docker-required gate |
| R10 | Semantic quarantine flips quality unexpectedly | L | M | L0/L1 default without pack; optional separate test |

---

## 11. Test strategy (сводка)

| Уровень | Tooling | Markers | Когда |
|---------|---------|---------|-------|
| Unit | pytest | default | `start_tcp` bound port |
| L0/L1 Integration | pytest + testcontainers + aiomqtt | `integration`, `slow`, optional `e2e` | каждый IMPLEMENT step |
| L2 Compose | bash script + optional pytest | `slow` / manual | после s07; BACK QA |
| Regression | `.venv/bin/pytest tests/storage apps/edge/collector/tests apps/edge/emulator/tests -q` | — | FINISH / QA |
| Load | existing `test_load_586hz` | `load` | **не** блокирует этот план |

**TDD order на каждый step:** red (failing assert / missing API) → green → refactor.  
**pytest runner HARD:** cwd = repo root, `.venv/bin/pytest …`.

**FRONT:** N/A. Subagent HARD RULE front-tests — N/A для этого BACK плана; если spawn explorer — вставить HARD RULE строку всё равно.

---

## 12. CREATIVE need

**Нет.**

Обоснование: framing IPC, WriterService, Timescale schema, MQTT publisher, compose topology — уже спроектированы (T-001/T-002/T-008 + CREATIVE CR-STO-*). Этот план — **test harness + минимальный `start_tcp` API**, не новое архитектурное решение. ADR ниже фиксируют test-layer choices без CREATIVE batch.

Если в DECOMPOSE всплывёт необходимость менять wire-контракт envelope — тогда отдельный CREATIVE; сейчас не ожидается.

---

## 13. ADR summary

| ID | Решение |
|----|---------|
| **ADR-PIPE-001** | Layered gates L0 (IPC→DB) → L1 (emulator→DB in-proc) → L2 (compose SQL). Не только compose и не только mocks. |
| **ADR-PIPE-002** | Timescale via testcontainers `timescale/timescaledb:2.14.2-pg16` + alembic upgrade; не SQLite/vanilla Postgres. |
| **ADR-PIPE-003** | Добавить `WriterService.start_tcp` (port 0) для тестов; `run_tcp` делегирует. |
| **ADR-PIPE-004** | Новый пакет `tests/pipeline/` отдельно от `tests/storage/` mocks — явная граница «persistence E2E». |
| **ADR-PIPE-005** | MQTT Contour A + Modbus Contour B оба в DoD; OPC optional Phase E. |
| **ADR-PIPE-006** | Compose smoke через `scripts/smoke-pipeline-db.sh` с fail-loud на count=0. |

---

## 14. Зависимости

| Направление | Task / Plan | Связь |
|-------------|-------------|-------|
| Upstream | T-002 s01–s18 | **hard** — WriterService, repos, migrations, compose writer |
| Upstream | T-008 + mqtt-smoke | **hard** — publisher, mosquitto profile, collector-mqtt |
| Upstream | T-001 runtime / edge-runtime-smoke | **hard** — IpcCanonicalSink, Modbus connector, bootstrap |
| Upstream | BUGFIX 20260729 package-path | **hard** — pytest pythonpath, healthy compose |
| Parallel | T-002 BACK QA re-run | после этого плана L2 закрывает live acceptance gap |
| Downstream | T-003 API | сможет читать реальные samples в dev |

---

## 15. Skills (workflow)

- `writing-plans` — атомарность, files, TDD boundaries, no placeholders
- `python-testing-patterns` — fixtures, markers, async, AAA, isolation
- `architecture-patterns` — test boundary ports (IPC/DB as driven adapters)
- `supabase-postgres-best-practices` — count/index aware asserts; no full-table scans in poll beyond `count(*)` / PK lookup
- `brainstorming` — batch options L0/L1/L2 (зафиксированы ADR); без HARD-GATE пауз
- `grill-me` — блокеров нет на момент PLAN

---

## 16. Self-review (writing-plans checklist)

1. **Spec coverage:** user request «эмулятор → приём → запись в БД» → FR-1..8, AC-PIPE-01..10, Contour A+B, L0–L2 — покрыто.
2. **Placeholder scan:** нет TBD/TODO; конкретные пути, tag_id, image tag, script contract.
3. **Type consistency:** `IpcCanonicalSink`, `WriterService.start_tcp`, `TelemetrySample`, `SamplesRepo` — совпадают с кодовой базой.
4. **Gap vs mqtt-smoke:** mqtt-smoke явно исключал PSQL; этот план — следующий слой persistence.

---

## 17. Следующий режим

→ **BACK IMPLEMENT** s01 (`WriterService.start_tcp`) — новый чат  
→ s02…s08 по [`decompose index`](decompose-v1-p1-pipeline-db-e2e/index.md)  
→ **BACK QA** (L2 compose SQL + regression)  
→ при необходимости повторный QA storage (live acceptance)

**CREATIVE:** нет.

**FINISH BACK DECOMPOSE:** `code_changed: no` — только memory-bank artifacts.

---

## 18. Handoff

- **Артефакт плана:** `memory-bank/back/plan/plan-v1-p1-pipeline-db-e2e.md`
- **Decompose:** [`decompose-v1-p1-pipeline-db-e2e/index.md`](decompose-v1-p1-pipeline-db-e2e/index.md)
- **Следующая команда:** `BACK IMPLEMENT` → `s01-writer-start-tcp.md`
- **Ключевой deliverable:** `tests/pipeline/*` + `scripts/smoke-pipeline-db.sh` + `WriterService.start_tcp`
- **Уровень:** L3 · CREATIVE: нет

---

*2026-07-29 — T-002 gap-close Pipeline DB E2E. DECOMPOSE s01–s08. Emulator → collector → writer → Timescale assert.*
