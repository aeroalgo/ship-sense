# [T-001 | v1-p1-collector] BACK QA

**Дата:** 2026-07-27  
**Reviewer:** BACK QA  
**Verdict:** **fail** (backend regression зелёный, edge-stack compose smoke заблокирован)

## Scope

- task: T-001 / v1-p1-collector
- план: `memory-bank/back/plan/plan-v1-p1-collector.md`
- decompose index: `memory-bank/back/plan/decompose-v1-p1-collector/index.md`
- проверенные области: collector unit/integration/soak, emulator unit/integration, Docker Compose, IPC peer, runtime healthchecks, §0.11 integration refs, базовый OWASP review
- связанные последние изменения: s13 Normalizer, s23 Docker Compose, s24 stub plugin, s25 soak, emulator Modbus overlap bugfix

## Checks

| Проверка | Результат | Доказательство |
|---|---:|---|
| Полный collector + emulator pytest | **PASS** | `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src .venv/bin/python -m pytest apps/edge/collector/tests apps/edge/emulator/tests -q` → **259 passed in 75.62s** |
| Короткий soak fragment | **PASS** | `SHIPSENSE_SOAK_DURATION_SEC=2 SHIPSENSE_SOAK_DROP_INTERVAL_SEC=0.5 SHIPSENSE_SOAK_DROP_DURATION_SEC=0.05 ... pytest ... -m slow` → **1 passed in 2.48s** |
| Python compile check | **PASS** | `python -m compileall -q apps/edge/collector/src apps/edge/collector/tests apps/edge/emulator/src apps/edge/emulator/tests` → exit 0 |
| Ruff | **BLOCKED / не установлен** | `ruff` и `.venv/bin/ruff` отсутствуют; в `apps/edge/collector/pyproject.toml` lint tool не задан |
| Compose syntax | **PASS** | `docker compose config --quiet` → exit 0 |
| Compose build | **PASS** | `docker compose build emulator collector writer` завершился успешно |
| writer healthcheck | **PASS** | TCP `127.0.0.1:9009`, контейнер healthy |
| emulator healthcheck | **PASS после rebuild** | TCP `127.0.0.1:5020`, контейнер healthy после overlap bugfix |
| collector healthcheck | **FAIL** | контейнер остаётся `unhealthy`; `/var/lib/shipsense/health/collector.json` отсутствует во время работы |
| compose all-services smoke | **FAIL** | первый `up` до rebuild падал на overlap; после rebuild emulator/writer healthy, collector unhealthy |
| IPC endpoint counterpart | **FAIL integration** | compose задаёт `SHIPSSENSE_WRITER_ENDPOINT=writer:9009`, но collector runtime не читает этот env и запускается с `NullSink`; writer видит только healthcheck TCP connect/disconnect |
| OPC UA full-profile runtime | **FAIL runtime quality** | логи emulator содержат повторяющиеся `Write refused ... does not have expected type` для `Double→Float` и `Int64→Int16/Int32` |
| Security baseline | **PASS с dev caveat** | collector/emulator не добавляют новые web routes/DB columns; OPC UA adapter выставляет read-only nodes; compose DB stub использует dev credentials и публичный bind только в `full` profile — не production config |

## Issues

| ID | sev | file | msg |
|---|---|---|---|
| R-1 | **high** | [apps/edge/collector/src/collector/app.py](../../apps/edge/collector/src/collector/app.py#L101) / [apps/edge/collector/src/collector/health/snapshot_writer.py](../../apps/edge/collector/src/collector/health/snapshot_writer.py#L30) / [docker-compose.yml](../../docker-compose.yml#L82) | Compose healthcheck ждёт snapshot во время работы, но `SnapshotWriter.write()` вызывается только при `CollectorApp.stop()`; collector поэтому остаётся unhealthy и `depends_on`-based edge smoke не проходит. |
| R-2 | **high** | [apps/edge/collector/src/collector/__main__.py](../../apps/edge/collector/src/collector/__main__.py#L43) / [docker-compose.yml](../../docker-compose.yml#L74) | Compose объявляет `SHIPSSENSE_WRITER_ENDPOINT=writer:9009`, однако entrypoint всегда создаёт `NullSink` и `_noop_source_factory`; runtime collector не подключается к writer и не собирает emulator telemetry. |
| R-3 | **medium** | [apps/edge/emulator/src/emulator/protocols/opcua_server.py](../../apps/edge/emulator/src/emulator/protocols/opcua_server.py#L114) | OPC UA ticker пишет Python values без приведения к объявленному `ua.VariantType`; полный profile генерирует `float/int` типов, несовместимых с node datatype, поэтому обновления отклоняются и подписчики получают устаревшие значения. |
| R-4 | **low** | [apps/edge/collector/pyproject.toml](../../apps/edge/collector/pyproject.toml#L1) | В проекте нет настроенного lint/type-check command; QA не может подтвердить статическое качество, а Ruff не установлен в `.venv`. |

## Reproduction

### R-1 / R-2

```bash
docker compose build emulator collector writer
docker compose up -d emulator writer collector
sleep 8
docker compose ps
```

Наблюдение: `emulator` и `writer` healthy, `collector` остаётся `health: starting`, затем `unhealthy`. В контейнере collector:

```text
/var/lib/shipsense/health/ пуст
```

Лог collector показывает только:

```text
INFO collector.app collector started: sources=0
```

Лог writer показывает только healthcheck-коннекты без frames:

```text
collector connected
collector disconnected
```

Counterpart search по `SHIPSSENSE_WRITER_ENDPOINT` находит compose и README, но не находит runtime consumer в `apps/edge/collector/src`.

### R-3

После успешного запуска emulator:

```text
Write refused: Variant(... VariantType.Double ...) ... expected type: 10
Write refused: Variant(... VariantType.Int64 ...) ... expected type: 4
```

Ошибки повторяются для полного `tags_stub.yaml`; малые unit/integration profiles их не покрывают.

## Integration rule (§0.11)

- [x] `docker-compose.yml` service names `emulator`, `writer`, `collector` ↔ `depends_on`, healthchecks и TCP endpoints найдены.
- [x] `collector` Dockerfile `--snapshot` ↔ `CollectorApp` CLI argument и volume найдены.
- [x] IPC framing `IpcCanonicalSink` ↔ writer-stub `readexactly(4)` / big-endian length найдены и согласованы.
- [x] emulator CLI args ↔ compose `command` paths найдены.
- [ ] `SHIPSSENSE_WRITER_ENDPOINT` ↔ runtime consumer — **не найден**; R-2.
- [ ] health snapshot periodic write ↔ compose healthcheck — **не найдено**; R-1.
- [ ] OPC UA declared datatype ↔ runtime update coercion — **не найдено**; R-3.
- [n/a] DB column ↔ migration, API route ↔ client — scope s23/s24/s25 не добавляет DB/API контрактов.

## Edge cases / performance

- Normalizer dirty matrix, duplicate delivery, unknown native id, NaN/Inf, stale timestamps и discrete events покрыты полным suite; uncaught exceptions не обнаружены.
- Soak fragment проверил reconnect cycle, task count и socket descriptor count: короткий прогон зелёный.
- Полный 24h soak не запускался: это ручной длительный прогон из runbook, не CI verification.
- Full-profile OPC UA update loop генерирует шумные runtime errors; это не падение процесса, но означает потерю обновлений и потенциальный лог-флуд.
- Compose `db` stub имеет dev credentials и host bind; профиль `full` не следует считать production-safe без secrets/network hardening.

## Blockers

1. Исправить R-1: snapshot должен писаться периодически после `start()` либо healthcheck должен проверять реально существующий liveness signal. Предпочтительно исправить причину — запустить periodic `SnapshotWriter` loop и обновлять state.
2. Исправить R-2: runtime должен построить configured `IpcCanonicalSink` и источники из config/env; нельзя считать compose integration проверенной при фактическом `NullSink` и `sources=0`.
3. Исправить R-3: приводить значения к datatype node перед `write_value()` или согласовать генераторы и OPC UA datatype metadata; затем добавить full-profile regression.
4. После фиксов повторить `BACK QA`: полный pytest, compose rebuild/up, все healthchecks, writer frame counter и отсутствие `Write refused`.

## Handoff

- **Done:** BACK QA T-001 выполнен; backend suite и короткий soak зелёные, compose syntax/build зелёные.
- **Files:** `memory-bank/back/qa/v1-p1-collector/qa-20260727-v1-p1-collector.md`; проверенные runtime paths: `apps/edge/collector/src/collector/__main__.py`, `apps/edge/collector/src/collector/app.py`, `apps/edge/collector/src/collector/health/snapshot_writer.py`, `apps/edge/emulator/src/emulator/protocols/opcua_server.py`, `docker-compose.yml`.
- **Next:** `BACK BUGFIX` для R-1/R-2/R-3, затем повторный `BACK QA`; T-001 нельзя объявить закрытым до compose smoke pass.
- **Tool / model:** Claude Code + premium-coding.
- **New chat:** yes — QA выявил несколько независимых runtime blockers.
