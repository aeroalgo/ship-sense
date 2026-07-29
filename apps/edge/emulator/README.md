# Emulator (apps/edge/emulator)

I3 industrial emulator (T-001 test source) — 586-signal stub profile, корреляции,
сценарии «грязи» (T-3). Поднятие Modbus TCP + OPC UA серверов из одного процесса.

## Протоколы и порты

| Порт (контейнер → host) | Протокол | Назначение |
|--------------------------|----------|------------|
| `5020` | Modbus TCP | aps_main (FC03/04, read-only) |
| `4840` | OPC UA | `opc.tcp://emulator:4840` (Basic256Sha256 / SignAndEncrypt) |

> Emulator поднимает **один** Modbus-порт за процесс. Второй источник (skt_geu, порт
> `5021`) потребует multi-port adapter — будущий шаг; до него dual-source покрывается
> integration-тестами (`test_dual_source_isolation.py`). В контейнере слушает `0.0.0.0`
> (compose CMD), dev-дефолт CLI — `127.0.0.1:502`.

## Запуск

Dev (без Docker):

```bash
PYTHONPATH=src python -m emulator --host 127.0.0.1 --modbus-port 5020 --opcua-port 4840
```

Docker / Compose (s23):

```bash
docker compose up -d emulator
docker compose logs -f emulator
docker compose ps emulator   # (healthy)
```

Healthcheck compose — TCP-коннект на `127.0.0.1:5020` внутри контейнера.

## Профили и сценарии

- `config/tags_stub.yaml` — 586-signal stub profile (генерация тегов + seed).
- `config/scenarios.yaml` — сценарии «грязи» (ScenarioRunner): bad-frame, chatter,
  connection_drop, duplicate, nan_inf, opc_bad_quality, out_of_range, stuck_value,
  tag_map_change, time_jump.

См. decompose `s15` (tag model), `s16`–`s17` (modbus/opcua servers), `s18` (dirt).

## Образ

```bash
docker build -t shipsense/emulator:dev apps/edge/emulator
```

Runtime-зависимости: `requirements.txt` (PyYAML / pymodbus / asyncua).
`PYTHONPATH=/app/src`.
