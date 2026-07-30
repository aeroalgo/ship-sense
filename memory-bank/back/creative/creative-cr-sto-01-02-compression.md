# CR-STO-01 / CR-STO-02 — Hypertable chunk interval and compression policy design

**Creative ID:** CR-STO-01, CR-STO-02
**Decompose steps:** [s16-compression-policy.md](../plan/decompose-v1-p1-storage/s16-compression-policy.md)
**Plan:** [plan-v1-p1-storage.md](../plan-v1-p1-storage.md) (§527–538, §958, §973)
**Дата:** 2026-07-29
**Режим:** BACK CREATIVE
**Уровень:** L4 (T-002 v1-p1 storage + semantic)
**AC:** AC-STO-S16
**Unblocks:** s16 (compression & retention policy) → s17 (integration) → s18 (tests)

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `supabase-postgres-best-practices` | Оптимальные параметры сжатия и чанков TimescaleDB, избежание деградации планировщика при избыточном числе чанков. |
| `brainstorming` | Выбор компромисса между гранулярностью drop_chunks и степенью сжатия Gorilla. |

## 1. Результаты бенчмарков

Для 100 тегов, генерирующих данные каждые 30 секунд (всего 864,000 строк за 3 дня):

### А. Сравнение интервалов чанков (CR-STO-01)

| Chunk Interval | Chunks | Size Pre (MB) | Size Post (MB) | Ratio | Insert (s) | Drop (s) | Q1 Post (ms) | Q3 Post (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1 Hour** | 72 | 220.55 | 25.36 | 8.70x | 11.956 | 0.171 | 8.08 | 20.23 |
| **1 Day** | 3 | 224.54 | 7.92 | 28.34x | 10.213 | 0.028 | 1.36 | 12.59 |
| **7 Days** | 1 | 225.27 | 7.42 | 30.35x | 15.010 | 0.001 | 0.97 | 11.50 |

* Q1 (Point Query / Recent 100): Получение последних 100 точек по тегу.
* Q3 (Trend Query): Получение всех точек по тегу за весь период.

### Б. Сравнение параметров сжатия (CR-STO-02)

| Configuration | Size Pre (MB) | Size Post (MB) | Ratio | Query (ms) | Описание |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A: segmentby tag_id, orderby ts DESC** | 48.64 | 2.62 | 18.53x | 5.14 | Рекомендуемая конфигурация |
| **B: segmentby tag_id, quality, orderby ts DESC** | 48.64 | 3.29 | 14.79x | 5.42 | Избыточное деление по качеству |
| **C: no segmentby, orderby ts DESC** | 48.64 | 2.81 | 17.29x | 25.99 | Медленные запросы (декомпрессия всего чанка) |

## 2. Анализ и принятые решения

### CR-STO-01: Выбор интервала чанка (chunk_time_interval)
1. **Накладные расходы мелких чанков:** Интервал `1 hour` генерирует слишком много чанков (72 за 3 дня, 168 за неделю). Это раздувает системный каталог и замедляет планировщик запросов. Сжатие падает до 8.70x из-за коротких серий данных на один тег внутри чанка (всего 120 точек) и накладных расходов метаданных чанка.
2. **Гранулярность удаления (drop_chunks):** Интервал `7 days` обеспечивает максимальное сжатие (30.35x), но имеет плохую гранулярность drop_chunks. Чанк удаляется только целиком. При soft-retention в 7 дней реальные данные будут храниться на диске до 14 дней от даты начала чанка, удваивая пиковое потребление диска.
3. **Решение:** Выбран интервал **`1 day`** (соответствует миграции 002). Он дает практически пиковую степень сжатия (28.34x), отличную скорость запросов, минимизирует количество чанков и обеспечивает погрешность хранения при очистке не более 1 дня (14% перерасхода диска вместо 100%).

### CR-STO-02: Выбор параметров сжатия (Compression Policy)
1. **Сегментация по тегу:** Отсутствие `segmentby = tag_id` (вариант C) приводит к замедлению выборки истории тега в 5 раз (с 5 ms до 26 ms), так как TimescaleDB вынужден читать и распаковывать весь чанк целиком для извлечения точек одного тега.
2. **Влияние качества в segmentby:** Добавление `quality` в `segmentby` (вариант B) ухудшает сжатие с 18.53x до 14.79x из-за дробления последовательностей на более короткие подгруппы при смене качества.
3. **Решение:** Настроить сжатие строго со следующими параметрами:
   - `timescaledb.compress = true`
   - `timescaledb.compress_segmentby = 'tag_id'`
   - `timescaledb.compress_orderby = 'ts DESC'`
4. **Retention Policy:**
   - Soft-retention: удаление чанков старше **1095 дней** (3 года) через `drop_chunks`.
   - Сжатие: чанки сжимаются через **7 дней** (`compress_after => INTERVAL '7 days'`), чтобы оперативные горячие данные за неделю оставались в несжатом виде для быстрых вставок с отставанием во времени.

## 3. Детали миграции `006_compression_retention.py`

Миграция должна применять следующие SQL-команды:

```sql
-- Включение сжатия
ALTER TABLE shipsense.samples SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tag_id',
    timescaledb.compress_orderby = 'ts DESC'
);

-- Добавление политик
SELECT add_compression_policy('shipsense.samples', INTERVAL '7 days');
SELECT add_retention_policy('shipsense.samples', INTERVAL '1095 days');
```

В `downgrade()` необходимо удалить политики перед отключением сжатия:
```sql
SELECT remove_retention_policy('shipsense.samples', if_exists => true);
SELECT remove_compression_policy('shipsense.samples', if_exists => true);
ALTER TABLE shipsense.samples SET (timescaledb.compress = false);
```

## 4. Верификация
- Проверка наличия настроек в `timescaledb_information.compression_settings`.
- Проверка политик в `timescaledb_information.jobs`.