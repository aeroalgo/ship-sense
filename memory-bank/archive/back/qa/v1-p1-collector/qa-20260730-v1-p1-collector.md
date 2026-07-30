# [T-001 | v1-p1-collector] BACK QA (re-QA после s26)

**Дата:** 2026-07-30  
**Reviewer:** BACK QA  
**Verdict:** **pass**

## Scope

- task: T-001 / v1-p1-collector
- план: `memory-bank/back/plan/plan-v1-p1-collector.md`
- gap-close: `memory-bank/back/plan/plan-v1-p1-edge-runtime-smoke.md` + implement s26
- предыдущий fail: [qa-20260727-v1-p1-collector.md](qa-20260727-v1-p1-collector.md)
- проверенные области: collector+emulator pytest, soak, compileall, compose build/up, health snapshot, IPC→writer→Timescale samples, OPC UA Write refused, SIGTERM exit 0, §0.11
- связанные изменения: s26 R-1/R-2/R-3 runtime gap-close

## Checks

| Проверка | Результат | Доказательство |
|---|---:|---|
| Полный collector + emulator pytest | **PASS** | `PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src .venv/bin/python -m pytest apps/edge/collector/tests apps/edge/emulator/tests -q` → **333 passed in 78.90s** |
| Короткий soak / slow | **PASS** | `SHIPSENSE_SOAK_DURATION_SEC=2 … pytest … -m slow` → **3 passed, 297 deselected in 3.47s** |
| Python compile check | **PASS** | `compileall` collector+emulator src/tests → exit 0 |
| Ruff | **BLOCKED / не установлен** | `ruff` / `.venv/bin/ruff` отсутствуют (R-4, low, как в QA-20260727) |
| Compose syntax | **PASS** | `docker compose config --quiet` → exit 0 |
| Compose build | **PASS** | `docker compose build emulator collector writer` → Built |
| Compose up edge stack | **PASS** | `docker compose up -d emulator writer collector` → exit 0 |
| emulator / writer / collector healthy | **PASS** | все три `healthy` ≤15s после up |
| collector snapshot running + sources≥1 | **PASS** | `/var/lib/shipsense/health/collector.json`: `collector_state=running`, `sources=[{source_id:aps_main,state:up}]`; log `collector started: sources=1` |
| IPC / writer samples > 0 | **PASS** | Timescale `samples`: live TAI4101/TAI4103/TAI4104 (~1 Hz); delta +15 за 5s; max(ts) ≈ now. Stub `samples/sec` лог writer отсутствует (реальный storage writer) — evidence = SQL |
| OPC UA Write refused | **PASS** | `docker compose logs emulator` → `Write refused` count **0** |
| SIGTERM collector exit 0 | **PASS** | `docker compose stop collector` → ExitCode=0 |
| §0.11 SHIPSSENSE_WRITER_ENDPOINT | **PASS** | compose + `runtime/bootstrap.py:212` `os.getenv("SHIPSSENSE_WRITER_ENDPOINT")` |
| §0.11 periodic SnapshotWriter | **PASS** | snapshot файл существует во время `running`; healthcheck зелёный |
| §0.11 OPC UA coerce | **PASS** | `opcua_server.py` `_coerce_value` / `_value_types`; runtime без Write refused |

## Issues

| ID | sev | file | msg |
|---|---|---|---|
| R-1 | resolved | `app.py` / `snapshot_writer.py` | Periodic snapshot + healthy collector во время работы |
| R-2 | resolved | `runtime/bootstrap.py` / `__main__.py` | Sources≥1 + IPC endpoint из env; live samples в DB |
| R-3 | resolved | `opcua_server.py` | Typed/coerced writes; Write refused = 0 |
| R-4 | **low** | `apps/edge/collector/pyproject.toml` | Ruff/type-check не установлены в `.venv` — статическое качество не подтверждено |
| O-1 | **low** | `domain/interfaces.py` Modbus health | Snapshot `samples_total=0`, `tags_total=0`, `last_ok_ts=null` при живом потоке TAI410*; health file/state=up достаточны для compose healthcheck, но счётчики health не отражают throughput |

## Reproduction (pass evidence)

```bash
# порты 5020/4840/9009 должны быть свободны до pytest
docker compose stop
PYTHONPATH=apps/edge/collector/src:apps/edge/emulator/src \
  .venv/bin/python -m pytest apps/edge/collector/tests apps/edge/emulator/tests -q
# → 333 passed

docker compose build emulator collector writer
docker compose up -d emulator writer collector
docker compose ps   # all healthy
docker compose exec collector cat /var/lib/shipsense/health/collector.json
# collector_state=running, sources≥1

docker compose exec db psql -U shipsense -d shipsense -c \
  "SELECT tag_id, count(*) FROM samples WHERE ts > now() - interval '2 minutes' GROUP BY 1;"
# TAI4101/4103/4104 growing

docker compose logs emulator | grep -c 'Write refused' || true
# 0

docker compose stop collector
docker inspect shipsense-collector --format '{{.State.ExitCode}}'
# 0
```

## Integration rule (§0.11)

- [x] compose services emulator/writer/collector ↔ depends_on + healthchecks + TCP ports
- [x] `SHIPSSENSE_WRITER_ENDPOINT` ↔ `runtime_from_environment` / `IpcCanonicalSink`
- [x] health snapshot path ↔ compose healthcheck ↔ periodic `SnapshotWriter`
- [x] emulator OPC UA declared datatype ↔ `_coerce_value` before `write_value`
- [x] IPC framing ↔ writer TCP 9009 ↔ samples rows (TAI410*)
- [n/a] API routes — вне scope T-001

## Edge cases / performance

- Pytest hang при занятых compose-портах: перед suite нужен `docker compose stop` (иначе integration Modbus/OPC UA блокируются).
- AC-INT-03 «~586» ослаблен day-1 smoke (`SHIPSSENSE_SMOKE_SOURCES=aps_main` + `stub_aps_main_runtime.yaml` = 3 тега @1 Hz) — по `plan-v1-p1-edge-runtime-smoke.md`.
- Полный 24h soak не запускался (короткий fragment green).
- Health counters (O-1) не блокируют smoke; follow-up вне обязательного Fix plan.

## Blockers

Нет.

## Fix plan

Не требуется (verdict pass). Опциональный follow-up (не blocker):

| # | issue | command | subject | scope / files | verify |
|---|-------|---------|---------|---------------|--------|
| — | O-1 / R-4 | out_of_scope | health counters Modbus + ruff bootstrap | `interfaces.py` / Modbus connector; pyproject | snapshot samples_total>0 при live poll; `ruff check` |

## Epic QA

**Epic QA:** `BACK QA`  
**Эпик:** T-001 / `v1-p1-collector`  
**Предмет:** re-QA compose smoke после s26 (R-1/R-2/R-3)  
**Scope:** s01–s26; collector+emulator suite; compose emulator‖writer‖collector  
**Suite:** pytest collector+emulator; slow fragment; compose build/up/ps; SQL samples; stop exit 0  
**Артефакт:** `memory-bank/back/qa/v1-p1-collector/qa-20260730-v1-p1-collector.md`

## Handoff

- **Done:** BACK QA T-001 re-QA PASS; R-1/R-2/R-3 закрыты live evidence.
- **Files:** этот артефакт; evidence suite/compose/SQL.
- **Next:** `BACK REFLECT` T-001 / v1-p1-collector → затем `BACK ARCHIVE NOW`.
- **code_changed:** no
- **New chat:** yes → REFLECT
