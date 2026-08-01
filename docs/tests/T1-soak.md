# T1 soak harness

## Назначение

Harness собирает короткие CI-фрагменты метрик и проверяет критерии длительного T1 soak. Короткий прогон занимает минуты, а лабораторный/ship soak масштабируется до 72 часов без изменения формата snapshots.

## Метрики

`signals` endpoint Prometheus должен отдавать:

- `process_resident_memory_bytes` — RSS процесса;
- `shipsense_write_latency_seconds{quantile="0.99"}` — p99 latency записи в секундах;
- `shipsense_disk_used_ratio` — доля занятого диска от 0 до 1;
- `shipsense_ws_connections` — число активных WebSocket connections.

Скрипт допускает эквивалентные имена `write_latency_seconds`, `disk_used_ratio` и `websocket_connections` для lab exporters.

## CI fragment

```bash
.venv/bin/pytest apps/api/tests/soak/test_t1_fragment.py -m slow -q --tb=line
```

Тест проверяет scrape plumbing, bounded memory slope и отказ при утечке. Обычный pytest запуск исключает `slow` через `pyproject.toml`; CI job, который включает fragment, должен явно указать `-m slow`.

## Сбор snapshots

```bash
python scripts/soak/scrape_metrics.py http://127.0.0.1:9090/metrics
```

Без URL скрипт читает Prometheus text exposition из stdin. Для многократного lab/ship прогона сохраняйте по одному JSON snapshot на строку:

```bash
python scripts/soak/scrape_metrics.py "$METRICS_URL" >> /tmp/t1-snapshots.jsonl
```

## Проверка критериев

```bash
python scripts/soak/assert_pass_criteria.py /tmp/t1-snapshots.jsonl
```

Критерии по умолчанию:

- RSS slope `< 1%/day`;
- write latency p99 `<= 1s`;
- disk used `<= 90%`;
- WebSocket metric присутствует.

Порог можно переопределить аргументами `--max-memory-slope`, `--max-write-latency` и `--max-disk-used`. Exit code `0` означает pass, `1` — нарушение критерия или недостаток данных.

## Длительности

- **CI:** короткий fragment на несколько минут, достаточный для проверки parser/assert plumbing;
- **Lab:** длительный прогон с интервалом scrape 1–5 минут, минимум 24 часа для диагностики;
- **Ship acceptance:** 72 часа, snapshots и stdout/stderr сохраняются как evidence.

Не используйте sleep-цикл в pytest для 24/72 часов: тест должен оставаться быстрым и маркированным `slow`, а длительность задаётся runner-скриптом/лабораторным job.
