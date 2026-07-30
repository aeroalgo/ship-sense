# [T-001 | s23 | docker-compose] IMPLEMENT
**Plan ID:** v1-p1-collector
**Decompose step:** [s23-docker-compose.md](../../plan/decompose-v1-p1-collector/s23-docker-compose.md)
**Дата:** 2026-07-27
**Уровень:** L2 по atomic infra step (scaffold, `tdd: no`)
**Статус:** done (с caveat — см. §Известные ограничения)

## Сделано
- Создан edge-Dockerstack: Dockerfiles для `collector` / `emulator` + новый stub-сервис `writer` + корневой `docker-compose.yml`. AC-I3-16, AC-INT-03 (writer peer в compose), AC-HLT-05 (SIGTERM → exit 0).
- `apps/edge/writer-stub/` — T-002 day-1 заглушка writer: drain-only framing-сервер (length-prefixed JSON по контракту collector→writer, README collector §framing). Принимает frames, считает samples/events, логирует samples/sec каждые 5s. Реальный writer (T-002) заменит модуль — здесь только контейнер-peer, чтобы IPC sink collector'а (AC-INT-01) имел живого peer'а и не падал с `SinkUnavailable`.
- Compose: `emulator` (Modbus 5020 + OPC UA 4840), `writer` (9009), `collector` (depends_on emulator+writer healthy), `db`/`api`/`web` — stubs под профиль `full` (полный edge stack в T-003/T-004). Healthchecks на всех рабочих сервисах.
- Порты задокументированы: collector README (§Docker/Compose — порты 9009/9008, env `SHIPSSENSE_WRITER_ENDPOINT`, образ), emulator README (создан — порты 5020/4840, профили, сценарии).
- Runtime-deps зафиксированы pin'ом к рабочим версиям venv (`pymodbus==3.14.0`, `asyncua==2.0.1`, `pydantic==2.13.4`, `PyYAML==6.0.3`) — воспроизводимый build, совпадает с тем, на чём проходят integration-тесты s19–s22.

## Файлы
- `docker-compose.yml` (создание) — emulator / writer / collector / db / api / web (stubs).
- `apps/edge/collector/Dockerfile` (создание) — python:3.12-slim, PYTHONPATH=/app/src, ENTRYPOINT `python -m collector`, STOPSIGNAL SIGTERM, EXPOSE 9009, volume `/var/lib/shipsense/health`.
- `apps/edge/collector/requirements.txt` (создание) — pinned runtime deps.
- `apps/edge/emulator/Dockerfile` (создание) — python:3.12-slim, PYTHONPATH=/app/src, EXPOSE 5020 4840.
- `apps/edge/emulator/requirements.txt` (создание) — pinned runtime deps.
- `apps/edge/emulator/README.md` (создание) — порты, профили, сценарии, образ.
- `apps/edge/writer-stub/Dockerfile` (создание) + `src/writer_stub/__main__.py` (создание) + `src/writer_stub/__init__.py` (создание) — stub peer.
- `apps/edge/collector/README.md` (модификация) — добавлен §Docker/Compose (порты, запуск, образ).

## TDD
- **Пропущен по плану:** `tdd: no` — scaffold / infra / compose без новой бизнес-логики. Верификация = smoke (не pytest business).
- Skills A∪B (tdd, python-testing-patterns, modern-python) читаны в предыдущих заходах s01–s22; слой B из decompose step s23 совпадает (tdd/python-testing/modern-python). Для infra-слоя prod-код правок бизнес-логики нет.

## Верификация (smoke — чекпоинт шага)
- ✅ `docker compose config --quiet` — compose валиден.
- ✅ `docker compose build emulator writer collector` — все 3 образа собираются (python:3.12-slim + pinned deps).
- ✅ `writer` — **healthy** (TCP-коннект healthcheck на 127.0.0.1:9009 внутри контейнера).
- ✅ `collector` standalone: `docker stop` (SIGTERM) → **exit 0** (AC-HLT-05) — подтверждено прямым `docker run` + `docker inspect .State.ExitCode=0`. ENTRYPOINT ловит SIGTERM через `install_signal_handlers` → `CollectorApp.request_stop` → drain + disconnect.
- ⚠️ `emulator` — **падает** (см. §Известные ограничения).

## Integration check (§0.11)
- [x] `collector/__main__.py` ENTRYPOINT ↔ Dockerfile `ENTRYPOINT ["python","-m","collector"]`.
- [x] `collector/app.py` `--snapshot` CLI-arg ↔ Dockerfile `CMD ["--snapshot","/var/lib/shipsense/health/collector.json"]` + volume.
- [x] `IpcCanonicalSink` endpoint `(host,port)` TCP ↔ compose env `SHIPSSENSE_WRITER_ENDPOINT=writer:9009` + writer-stub слушает 0.0.0.0:9009.
- [x] Framing contract `IpcCanonicalSink._send` (4-byte BE length + JSON envelope `{type,payload}`) ↔ writer-stub `readexactly(4)`+`unpack(">I")`+`readexactly(n)` — совместим (writer-stub не парсит payload, только `type`-эвристику для счётчика).
- [x] `emulator/__main__.py` CLI-args (`--host/--profile/--scenarios/--modbus-port/--opcua-port`) ↔ compose `command:` (явные пути `/app/config/...`, т.к. дефолт `parents[3]/config` в контейнере = `/config`, не существует).
- [x] `sources.dev.yaml` endpoints `emulator:5020` / `opc.tcp://emulator:4840` ↔ compose service name `emulator` + порты.
- [x] `requirements.txt` pinned ↔ venv версии (grep `pip list`).

## Известные ограничения (НЕ scope s23)
- **Emulator production-start crash:** `docker compose up emulator` падает с `TypeError: SimData address 5 is overlapping!` в `emulator/protocols/modbus_server.py:_build_context` при старте с полным `tags_stub.yaml` (586 тегов). **Воспроизводится локально в venv** (не Docker-специфика): `PYTHONPATH=src python -m emulator --modbus-port 5030 ...` — тот же traceback в `app.run()` → `modbus.start()` → `_build_context` → `SimDevice.__post_init__`. Причина: несколько сигналов в profile имеют перекрывающиеся Modbus-адреса после `_parse_address`; `pymodbus.SimDevice` (3.14.0) отвергает overlap при init. В integration-тестах (s19/s21) не воспроизводится — там `ModbusServerAdapter` стартует с **малым** тестовым profile (3 тега, непересекающиеся адреса), не с 586-теговым `tags_stub.yaml`.
- **Не обхожено фейковым profile / fallback** (по user convention «исправлять причину, не fallback»). Compose использует реальный `tags_stub.yaml`.
- **Корневая причина = bug в `_build_context` (s16) / tag-модели (s15)** — отдельный заход **BACK BUGFIX**, вне scope этого infra-IMPLEMENT. До фикса `docker compose up` полного edge-stack невозможен; `collector`+`writer` работают и валидируют стэндэлон (SIGTERM→0, healthchecks).
- `sources.dev.yaml` ждёт второй Modbus-порт `5021` (skt_geu) — emulator поднимает один Modbus за процесс; multi-port adapter = будущий шаг. dual-source покрывается integration-тестом `test_dual_source_isolation.py`.

## Next
1. **BACK BUGFIX** emulator `_build_context` overlap (блокирует `docker compose up` edge-stack) — новый чат.
2. s24 (stub-plugin demo) / s25 (soak T1) — после BUGFIX, либо параллельно (не зависят от compose-up).
3. Коллектор runtime wiring-from-config (реальные sources из `sources.dev.yaml` вместо `_noop_source_factory`) — будущий шаг; сейчас `__main__` = skeleton (AC-HLT снэпшот/stop проверены).
