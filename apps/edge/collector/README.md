# Collector (apps/edge/collector)

Edge-судовой сбор телеметрии (T-001). Производит канонический поток
`TelemetrySample` / `Event` и отдаёт его процессу **writer** (T-002) по IPC.

## Ownership (RF-01 r04)

Канонические модели (`TelemetrySample`, `Event`, `EventSeverity`, `Quality`) принадлежат **FastAPI-приложению** (`apps/api/app/telemetry`, `apps/api/app/events`).  
Collector владеет только Raw* (`RawSample`, `RawTagDescriptor`) и health-моделями (`HealthStatus`, `SourceState`, `CollectorHealthSnapshot`) внутри `collector.domain`.

- **Разрешено:** collector core / sink / mapper (lifecycle_tracker, mapper) импортируют `app.telemetry` / `app.events`.
- **Запрещено:** плагины (`collector/plugins/*`) импортируют `app.telemetry` / `app.events` (только Raw* + health).
- **Запрещено:** storage и pipeline импортируют `collector.domain` (кроме Raw*/health).

Regression: `apps/api/tests/unit/test_domain_no_fastapi.py`, `tests/storage/test_no_collector_domain_canonical.py`, `apps/edge/collector/tests/unit/test_plugins_no_app_canonical.py`.

## IPC framing — collector → writer (стык T-002 §21.1)

Collector и writer — **разные процессы** (ADR-COL-001: collector ‖ writer ‖ api).
В unit-тестах sink = in-proc `asyncio.Queue`; в compose sink = IPC client.

### Транспорт

| Endpoint | Транспорт | Когда |
|----------|-----------|-------|
| `str` / `PathLike` | Unix domain socket (файл) | compose sidecar, одна машина |
| `(host, port)` | localhost TCP | кросс-контейнер в compose |

`IpcCanonicalSink(endpoint=...)` выбирает транспорт по типу `endpoint`.

### Wire-контракт (framing)

**Length-prefixed JSON envelope.** Binary-safe — без delimiter-ambiguity NDJSON.

```
+--------------------+--------------------------------+
| 4-byte BE length   | UTF-8 JSON envelope (N bytes)  |
+--------------------+--------------------------------+
```

- **length** — `struct.pack(">I", N)`, беззнаковый 32-бит big-endian.
- **envelope** — `{"type": "sample" | "event", "payload": {...}}`.
- **payload** — `model.model_dump(mode="json")` соответствующей pydantic-модели
  (`TelemetrySample` из `app.telemetry.models` / `Event` из `app.events.models`):
  - `datetime` → ISO-8601 строка;
  - `StrEnum` (`Quality`, `EventSeverity`) → строковое значение (`"good"`, `"alarm"`).

Реализация framing — `collector/sink/ipc_sink.py` (`_LEN` + `_send`).
Серверная сторона (parser) — задача T-002 writer; stub для интеграционных тестов
читает frames через `asyncio.StreamReader.readexactly(4)` → unpack → `readexactly(N)`.

### Политика потери связи

Потеря стыка writer — **явная ошибка**, не silent drop данных:

- `connect()` / `write_*` выполняют bounded reconnect (`connect_attempts`,
  backoff `retry_delay`). При истечении попыток → **`SinkUnavailable`**.
- Обрыв mid-stream (`ConnectionError` / `OSError` на `drain`) → drop сокета,
  reconnect, ровно один retry того же frame. Retry не удался → `SinkUnavailable`.
- `CancelledError` всегда прокидывается (graceful stop).

В compose peer sink'а — сервис **`writer`** (см. decompose `s23-docker-compose`).
Конфиг endpoint'а: `sources.yaml` / env (wire в шаге `s06`).

## Docker / Compose (s23)

### Порты

| Порт (контейнер → host) | Назначение |
|--------------------------|------------|
| `9009` (writer) | IPC framing collector → writer, length-prefixed JSON (AC-INT-01) |
| `9008` (collector) | зарезервирован под future HTTP/health-порт |

Сетевой путь collector → writer внутри compose: `writer:9009` (env `SHIPSSENSE_WRITER_ENDPOINT`).

### Запуск (smoke s23)

```bash
docker compose up -d emulator writer collector
docker compose ps                 # все (healthy)
docker compose logs -f collector  # "collector started"
docker compose stop collector     # SIGTERM → exit 0 (AC-HLT-05)
```

Health snapshot: `/var/lib/shipsense/health/collector.json` (volume `collector-health`),
обновляется каждые 5s (`SnapshotWriter`).

### Образ

```bash
docker build -t shipsense/collector:dev apps/edge/collector
docker run --rm shipsense/collector:dev --help
```

Runtime-зависимости: `requirements.txt` (pydantic / PyYAML / pymodbus / asyncua).
`PYTHONPATH=/app/src` соответствует dev-запуску (`PYTHONPATH=src python -m collector`).

## Soak T1 — leak check

Тест `tests/soak/test_24h_fragment.py` поднимает реальный Modbus emulator и collector
supervisor, периодически рвёт соединение и проверяет, что число живых asyncio-задач и
socket descriptors не растёт. Тест помечен `slow`, поэтому обычный targeted/regression
запуск его не включает.

### Короткий CI-фрагмент

Default suite (`pyproject` `addopts`) исключает `slow`. Soak нужно запускать явно.
Default длительности soak = **5 с** (`SHIPSENSE_SOAK_DURATION_SEC`); для CI-фрагмента 60 с задайте env:

```bash
PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src \
  SHIPSENSE_SOAK_DURATION_SEC=60 \
  SHIPSENSE_SOAK_DROP_INTERVAL_SEC=5 \
  .venv/bin/pytest -q apps/edge/collector/tests/soak/test_24h_fragment.py \
  -m slow --override-ini="addopts="
```

Быстрый локальный smoke (default 5 с или короче):

```bash
PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src \
  SHIPSENSE_SOAK_DURATION_SEC=5 \
  .venv/bin/pytest -q apps/edge/collector/tests/soak/test_24h_fragment.py \
  -m slow --override-ini="addopts="
```

### Полный ручной прогон 24h

Запускать на выделенном edge-хосте после проверки места под логи и открытых локальных
портов. `SHIPSENSE_SOAK_DROP_INTERVAL_SEC` задаёт период drops; `SHIPSENSE_SOAK_DROP_DURATION_SEC`
— окно, в котором peer недоступен:

```bash
PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src \
  SHIPSENSE_SOAK_DURATION_SEC=86400 \
  SHIPSENSE_SOAK_DROP_INTERVAL_SEC=300 \
  SHIPSENSE_SOAK_DROP_DURATION_SEC=3 \
  .venv/bin/pytest -q apps/edge/collector/tests/soak/test_24h_fragment.py \
  -m slow --override-ini="addopts=" \
  2>&1 | tee soak-24h-$(date -u +%Y%m%dT%H%M%SZ).log
```

Критерии pass: тест завершился с exit code 0, в каждом цикле после восстановления
появились samples, а live task/socket counts не превысили допуск. При падении сохранять
лог и значение окружения для воспроизведения.

## Локальный MQTT-dev профиль

Профиль `mqtt-dev` поднимает Mosquitto 2.x на обычном MQTT-порту `1883` и отдельный collector с двумя subscribe-only источниками: `panel_aps` (`shipsense/v1/aps/#`) и `panel_geu` (`shipsense/v1/geu/#`). Брокер намеренно разрешает анонимный доступ только для локальной разработки; production ACL/TLS в этот профиль не входят.

```bash
cp .env.example .env
# Собрать и запустить broker, writer и MQTT collector:
docker compose --profile mqtt-dev up -d --build mosquitto writer collector-mqtt
# Проверить конфигурацию и состояние:
docker compose --profile mqtt-dev config
docker compose --profile mqtt-dev ps
docker compose --profile mqtt-dev logs -f collector-mqtt
# Остановить профиль:
docker compose --profile mqtt-dev down
```

Переменные `.env`: `MQTT_BROKER_HOST` (по умолчанию `mosquitto`), `MQTT_BROKER_PORT` (по умолчанию `1883`), `MQTT_USER` и `MQTT_PASSWORD`. Источники профиля находятся в `config/sources.mqtt-dev.yaml`; переопределить путь можно через `COLLECTOR_SOURCES_PATH`.

### End-to-end smoke (publisher → broker → collector → writer)

Профиль включает publisher-сервис `emulator-mqtt` (deterministic seed 42) и
harness `scripts/smoke-mqtt-stack.sh`. Скрипт поднимает `mosquitto`, `writer`,
`collector-mqtt`, запускает publisher в отдельном контейнере (`docker compose run`)
и проверяет writer log / health snapshot по режиму.

```bash
# Поднять стек целиком (broker + writer + collector + publisher service):
docker compose --profile mqtt-dev up -d --build
docker compose --profile mqtt-dev ps
docker compose --profile mqtt-dev logs -f writer emulator-mqtt

# Smoke-режимы (publisher → broker → collector → writer):
scripts/smoke-mqtt-stack.sh single    # panel_aps only
scripts/smoke-mqtt-stack.sh dual      # panel_aps + panel_geu (health snapshot)
scripts/smoke-mqtt-stack.sh events    # lifecycle events (seed 42, interval 1.0)
scripts/smoke-mqtt-stack.sh sigterm   # SIGTERM drain → collector ExitCode 0

# Graceful shutdown collector (AC-HLT-05):
docker compose --profile mqtt-dev stop collector-mqtt   # → exit 0
```

Writer log format — cumulative summary каждые 5 s
(`writer_stub/__main__.py`):

```
samples/sec=1.0 total_samples=15 total_events=0
```

- `total_samples=[1-9]` — режимы `single`/`dual`, poll до 30 s.
- `samples/sec ...` — cumulative rate (1.0 при `--interval 1.0`).
- `total_events=[1-9][0-9]*` — режим `events`, poll до 60 s (≥13 ticks для
  цикла `_EVENT_STATES` из 3 состояний).

Каждый режим печатает `PASS` / `FAIL` и сносит compose-стек через cleanup trap
(dump логов `writer`/`collector-mqtt`/`emulator-mqtt` при ошибке).

### Known limits (dev-only)

- `aclfile readwrite` — анонимный readwrite, **только** локальная разработка;
  production ACL/TLS в этот профиль не входят.
- Без TLS, без auth.
- writer = stub (`writer_stub/__main__.py`), без PSQL writer.
- publisher deterministic seed 42 (`mqtt_publisher.py`).
- Health snapshot читается из volume `/var/lib/shipsense/health/collector.json`
  через `collector-mqtt` (режимы `dual`/`sigterm`).

## Pipeline DB E2E smoke (L2, AC-PIPE-07/08)

Скрипт `scripts/smoke-pipeline-db.sh` поднимает compose-стек с реальным `writer` (не stub) и TimescaleDB,
и ждёт появления данных в таблице `samples`.

```bash
# Default (Modbus contour): db + writer + emulator + collector
TIMEOUT=60 ./scripts/smoke-pipeline-db.sh default

# MQTT contour: + mosquitto + collector-mqtt + emulator-mqtt
TIMEOUT=120 ./scripts/smoke-pipeline-db.sh mqtt
```

Exit codes:
- `0` — `COUNT(samples) > 0` в пределах TIMEOUT (PASS)
- `1` — timeout, samples всё ещё 0 (FAIL loud, дамп writer логов в trap)
- `2` — неверный MODE

AC-PIPE-08 (mqtt mode): скрипт дополнительно логирует наличие тегов `TAI4101` / `TGEU4101`,
но exit 0 требует только `samples > 0`.

### Expected SQL после smoke

```sql
-- Минимум 1 строка появилась
SELECT count(*) FROM samples;  -- > 0

-- Для mqtt contour: известные теги из карт
SELECT count(*) FROM samples WHERE tag_id IN ('TAI4101','TGEU4101');  -- > 0 (не обязательно)

-- Примеры данных
SELECT tag_id, value, quality, ts FROM samples ORDER BY ts DESC LIMIT 5;
```

### Layer matrix (доказательства)

| Layer | Tool | Маркер | Что доказывает | Команда |
|-------|------|--------|----------------|---------|
| L0 | pytest + testcontainers | `integration`, `slow` | IPC frame → `samples`/`events` | `.venv/bin/pytest tests/pipeline/test_writer_ipc_db.py -q` |
| L1 MQTT | pytest + testcontainers | `integration`, `slow` | publisher → mosquitto → collector → writer → DB | `.venv/bin/pytest tests/pipeline/test_mqtt_pipeline_db.py -q` |
| L1 Modbus | pytest + testcontainers | `integration`, `slow` | emulator → connector → writer → DB | `.venv/bin/pytest tests/pipeline/test_modbus_pipeline_db.py -q` |
| L2 compose | bash + psql poll | — (manual/CI) | full stack up → data in DB | `TIMEOUT=60 ./scripts/smoke-pipeline-db.sh default` |
| L2 mqtt | bash + psql poll | — (manual/CI) | mqtt path → TAI4101/TGEU4101 | `TIMEOUT=120 ./scripts/smoke-pipeline-db.sh mqtt` |
| Regression | pytest | — | соседние suite не сломаны | `.venv/bin/pytest tests/storage apps/edge/collector/tests apps/edge/emulator/tests -q` |

Все L0/L1 тесты используют `WriterService.start_tcp()` (ephemeral port) + bounded poll loop.
L2 smoke — compose + psql, без pytest wrapper (опционально, не требуется для gate).

### pytest runner contract

Из корня репо (НЕ голый `pytest`):

```bash
.venv/bin/pytest tests/pipeline -q -m "integration and slow"
.venv/bin/pytest tests/pipeline -q
```

`pyproject.toml`:
- `pythonpath` включает `.`, `apps/edge/collector/src`, `apps/edge/emulator/src`
- `testpaths` включает `tests/pipeline`
- Маркер `e2e` зарегистрирован (опционален; pipeline suite использует `integration` + `slow`)
