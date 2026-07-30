# CREATIVE: Event schema dual-mode (CR-STO-04)

**Role:** BACK CREATIVE  
**Plan:** v1-p1-storage  
**Decompose:** [s07-events-repo.md](../../plan/decompose-v1-p1-storage/s07-events-repo.md)  
**Статус:** решение принято для IMPLEMENT  
**Дата:** 2026-07-29

## Контекст и цель

До закрытия Q4 ShipSense принимает два источника событий: Q4=A/native с полной семантикой и Q4=B/reconstruct с семантикой, восстановленной из битов или неполного payload. Оба должны идти в единый append-only поток без смешивания уровня достоверности.

Ограничения: frozen core в SQL, domain-поля в `params` JSONB, обязательный `reconstructed`, обязательный `idempotency_key`, режим `events.mode: auto|native|reconstruct`, строгая валидация известных event types вне `EventsRepo`.

## Компонент: Architecture

### Вариант 1 — JSONB-only

Все поля хранятся в `params`, SQL содержит только технический envelope.

**Плюсы:** гибкость и отсутствие миграций при расширении Q4.  
**Минусы:** нет frozen contract, сложнее индексация и journal-фильтры, provenance может стать неоднозначным.  
**Решение:** отклонён.

### Вариант 2 — frozen core + JSONB domain envelope

SQL хранит стабильные `event_name`, `source`, timestamps, `idempotency_key`, `severity`, `reconstructed`, `params`.

**Плюсы:** стабильные индексы, dedup по ключу, видимое происхождение, новые event types без миграций, соответствие миграции 003 и `EventsRepo`.  
**Минусы:** нужны validators и policy для неизвестных типов.  
**Решение:** рекомендован.

### Вариант 3 — native/reconstruct в разных таблицах

**Плюсы:** отдельные ограничения и диагностика.  
**Минусы:** две append/dedup реализации, UNION/view для journal и корреляции, параллельный retention.  
**Решение:** отклонён как преждевременная физическая декомпозиция.

## Компонент: Algorithm / contract

### Вариант A — две строгие модели

`AlarmEventParamsQ4A` валидирует native payload, `AlarmEventParamsQ4B` — reconstruct payload. Модель выбирается по `reconstructed`.

**Плюсы:** полнота каждой формы проверяется явно.  
**Минусы:** registry расширяется для каждого нового event type.  
**Решение:** рекомендован.

### Вариант B — одна модель с optional-полями

**Плюсы:** меньше классов.  
**Минусы:** invalid native/reconstruct payload легко принять; слабая проверка полноты.  
**Решение:** отклонён.

### Вариант C — opaque JSONB

**Плюсы:** минимальное coupling.  
**Минусы:** ошибки обнаруживаются поздно, API/journal не имеют надёжного контракта.  
**Решение:** только для явно неизвестных типов, не для известных alarm payload.

## Замороженный контракт v1

### SQL frozen core

`event_id` — UUID PK; `event_name` и `source` — non-empty; `event_ts`, `official_ts`, `received_ts`; `idempotency_key` — NOT NULL UNIQUE; `severity` — текущий range DDL; `reconstructed` — NOT NULL DEFAULT false; `params` — NOT NULL JSONB.

`EventsRepo` не меняет `reconstructed` после вставки. Append-only trigger остаётся политикой неизменности.

### `params` envelope

Для известных типов:

```json
{"schema_version":1,"kind":"alarm","payload":{}}
```

`kind` должен совпадать с `event_name`. `schema_version` нужен для эволюции JSON без SQL migration.

Q4=A/native сохраняет полную семантику (`tag_id`, `lifecycle`, `alarm_code`, `message`, `value`, `limit` — если поставлены источником). Q4=B/reconstruct обязан сохранять исходный признак и метод восстановления:

```json
{"schema_version":1,"kind":"alarm","payload":{"tag_id":"...","lifecycle":"active","alarm_code":"...","raw_bits":4,"reconstruction":{"method":"bit_mapping","source_field":"status_word","confidence":"derived"}}}
```

`AlarmEventParamsQ4B` не заполняет native-only поля синтетическими значениями без явной маркировки.

## Режимы конфигурации

| `events.mode` | Native | Reconstruct |
|---|---|---|
| `auto` | принимает | принимает |
| `native` | принимает | отклоняет |
| `reconstruct` | отклоняет | принимает |

Режим применяется на ingress/normalizer boundary. `EventsRepo` получает нормализованный `Event`, проверяет envelope invariants и выполняет append; Q4-правила не протекают в storage.

## Инварианты

- `reconstructed` совпадает с выбранной моделью;
- `event_name == params.kind`;
- известный event type с неверным payload даёт hard validation error, без silent fallback;
- известный `schema_version` поддерживается явно;
- duplicate `idempotency_key` — no-op, без update первой строки;
- journal фильтрует по frozen columns и стабильным JSONB paths (`tag_id`, `lifecycle`);
- correlation использует `official_ts ± window_ms`, а не timestamp из reconstruction payload.

## Руководство по s07

1. Ввести `EventFilters`, `EventRow`, `EventWithSample` вокруг frozen contract.
2. `insert_batch` — PostgreSQL `ON CONFLICT DO NOTHING`, без мутации payload.
3. `query_journal` — frozen filters + стабильные JSONB paths, детерминированная сортировка `official_ts`, затем `event_id`.
4. `get_with_sample` — корреляция по `official_ts ± window_ms`; отсутствие sample валидно.
5. Validators держать на domain/normalization boundary; не добавлять registry/framework в repo без требования s07.

## Верификация

- native/reconstruct payload проходят соответствующие модели;
- mismatch mode / `reconstructed` / `kind` отклоняется;
- property-based: valid envelope сохраняет `kind`, `reconstructed`, `schema_version` после JSON round-trip;
- repository: duplicate idempotency вставляется один раз;
- repository: correlation не выходит за official-time window;
- targeted: `.venv/bin/pytest tests/storage/test_events_repo.py -q` из корня.

## Итоговое решение

Зафиксировать **frozen core + JSONB domain envelope**, строгие `AlarmEventParamsQ4A/B` и `auto|native|reconstruct`. CR-STO-04 закрыт для s07; отдельные таблицы не вводятся, а Q4-правила не переносятся в `EventsRepo`.

🎨🎨🎨 EXITING CREATIVE PHASE
