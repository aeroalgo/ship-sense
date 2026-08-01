# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-09 vessel state и setpoints changelog

**Creative ID:** CR-P2-09  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [s11-api-vessel-setpoints.md](../../plan/decompose-v1-p2-ship/s11-api-vessel-setpoints.md)  
**Зависимый шаг:** [s11-api-vessel-setpoints.md](../../plan/decompose-v1-p2-ship/s11-api-vessel-setpoints.md)  
**Дата:** 2026-07-31  
**Режим:** BACK CREATIVE  
**Уровень:** L3  
**Типы решений:** Architecture + Algorithm  
**Статус:** closed

## Skills gate

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/architecture-patterns/SKILL.md`
- `.agents/skills/improve-codebase-architecture/SKILL.md`
- `.agents/skills/python-design-patterns/SKILL.md`
- `.agents/skills/property-based-testing/SKILL.md`
- `.agents/skills/async-python-patterns/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture`: vessel state связывает конфигурацию, latest-value read и HTTP seam; нужен один глубокий domain seam вместо логики в endpoint.
- `python-design-patterns`: требуется небольшая композиция reader/override store без преждевременной иерархии адаптеров.
- `property-based-testing`: пороги, UTC-времена и TTL имеют инварианты на границах, которые лучше закрепить свойствами.
- `async-python-patterns`: latest signal и Redis override читаются через async I/O; нельзя блокировать FastAPI handler.

## Контекст и инварианты

s11 добавляет read-only vessel state, ограниченный manual override и полный read-only changelog изменения уставок. Существующие `GET /api/setpoints` и `GET /api/setpoints/history` сохраняются. Ни один endpoint под `/api/setpoints` не получает POST/PATCH/PUT/DELETE.

Канонический источник режима — dedicated `ship-pack/<vessel>/vessel.yaml`, а не эвристика по названию warning. Для Makarov baseline используется rpm tag `SKT001` из существующего tag map; имя тега и threshold должны быть конфигурируемыми, чтобы не зашить конкретный корабль в API.

Безопасные правила:

1. `rpm >= threshold_transit` означает автоматический `transit`; `rpm < threshold_transit` — `anchorage`.
2. Отсутствующий, нечисловой или явно stale rpm не считается ходом: автоматический режим fail-closed = `anchorage`, `rpm_ge1 = null`.
3. Manual override имеет конечный `expires_at`. Истёкший override игнорируется при каждом GET и удаляется лениво; фоновая задача для reset не нужна.
4. Все timestamps на API seam — timezone-aware UTC. Naive timestamp в конфигурации нормализуется к UTC только по существующему правилу pack loader; входной query без timezone отклоняется.
5. `setpoint_changed` — append-only event. Changelog только читает события и не строит искусственные записи из текущего YAML.
6. Ошибка конфигурации (`rpm_tag` отсутствует, threshold не положительный, unit не `rpm`) — startup/config error, а не silent fallback.

## Компонент A — vessel configuration (Architecture)

### Вариант 1: отдельная секция в `vessel.yaml` (рекомендуется)

```yaml
vessel:
  id: makarov
  name: Адмирал Макаров
  imo: XXXXXXX
  pack_version: 1.0.0-emulator
vessel_state:
  rpm_tag: SKT001
  rpm_unit: rpm
  transit_threshold_rpm: 400
  signal_max_age_seconds: 120
  policies:
    transit:
      sound_enabled: false
      night_dim: true
    anchorage:
      sound_enabled: true
      night_dim: false
```

**Плюсы:** один явный ship-pack contract; vessel-specific threshold и policies рядом с vessel metadata; loader может fail-fast до запуска API; тестовый fixture легко заменить.  
**Минусы:** появляется новый config block и нужно проверить его против tag map.

### Вариант 2: переиспользовать `warnings.yaml`

Взять первый подходящий rpm warning/tag и его threshold, а sound/night policy держать в API settings.

**Плюсы:** меньше YAML-файлов и повторного чтения tag map.  
**Минусы:** warning threshold — не обязательно operational transit threshold; порядок warning-конфигурации становится частью режима; policy распадается между pack и env. Это создаёт скрытую связность и делает режим недетерминированным при изменении B13 warnings.

**Решение:** вариант 1. `warnings.yaml` и B13 остаются потребителями rpm, но не владельцами vessel mode. Loader проверяет, что `rpm_tag` существует в tag map и имеет `unit: rpm`/analog-compatible type.

## Компонент B — latest rpm и domain service (Architecture)

### Вариант 1: логика непосредственно в FastAPI endpoint

Endpoint загружает YAML, ищет latest sample, сравнивает threshold, читает override и собирает response.

**Плюсы:** мало файлов на старте.  
**Минусы:** HTTP, config, freshness, TTL и mode policy оказываются в одном handler; unit-тесты требуют клиента и сложно проверить fail-closed поведение без transport noise.

### Вариант 2: `VesselStateService` с двумя портами (рекомендуется)

Endpoint делает только parse/validation и вызывает service. Service получает:

- `VesselConfig` — immutable validated config из ship-pack;
- `LatestSignalReader` — async read latest value/quality/timestamp для configured tag;
- `OverrideStore` — async `get/set/delete` с expiry.

Алгоритм service:

1. Прочитать latest signal.
2. Проверить numeric value, unit/quality и `now - sample_ts <= signal_max_age_seconds`.
3. Определить automatic mode по threshold.
4. Прочитать override; если expiry в прошлом — удалить и продолжить automatic mode.
5. Применить override target только при валидном active record.
6. Выбрать sound/night policy и собрать response.

**Плюсы:** endpoint остаётся тонким; fake reader/store дают детерминированные unit-тесты; transport не протекает в domain; одна точка для GET и POST.  
**Минусы:** два явных порта и loader wiring; понадобится найти существующий collector/snapshot seam для adapter.

**Решение:** вариант 2. Не создавать общий `TagRegistry` или generic state framework: это был бы shallow abstraction. Достаточно одного vessel-specific service с узкими Protocol-портами.

## Компонент C — override storage и TTL (Architecture)

### Вариант 1: process-local dictionary

Хранить `{vessel_id: target, expires_at}` в памяти API.

**Плюсы:** нулевая инфраструктура, простые тесты.  
**Минусы:** разные workers/реплики видят разные режимы; restart теряет override; это нарушает смысл ручного override на судовом API.

### Вариант 2: Redis key с native TTL (рекомендуется)

Ключ: `vessel:{vessel_id}:state_override`. Значение — минимальный JSON `{mode, expires_at}`; Redis TTL задаётся тем же `ttl_minutes`. GET использует server-side expiry и дополнительно проверяет `expires_at` для clock-safe ответа. Для тестов используется in-memory fake, реализующий тот же маленький port.

**Плюсы:** одинаковое состояние во всех API workers; restart не превращает активный override в автоматический режим раньше TTL; не нужна Alembic-миграция или новая таблица; native TTL сам удаляет запись.  
**Минусы:** Redis становится обязательным для POST/active override; нужен явный 503/config error вместо опасного local fallback.

### Вариант 3: таблица `vessel_overrides`

Хранить target и expiry в PostgreSQL, выбирать запись с `expires_at > now()`.

**Плюсы:** auditability и транзакционные semantics.  
**Минусы:** для ephemeral TTL добавляет миграцию, cleanup и DB round-trip; audit manual actions не входит в s11 acceptance. Это чрезмерно для текущего scope.

**Решение:** вариант 2. Если Redis недоступен, POST возвращает контролируемую dependency error, а GET без active record следует automatic fail-closed; запрещён тихий переход на process-local storage.

## Компонент D — HTTP contract vessel (Architecture + Algorithm)

### Вариант 1: `mode` содержит только effective mode

GET возвращает `transit`/`anchorage`, а активный override виден только по `override_until`.

**Плюсы:** потребителю всегда сразу понятен effective mode.  
**Минусы:** невозможно отличить manual override от автоматического режима без дополнительного флага; sample plan явно допускает `manual_override`.

### Вариант 2: explicit override state (рекомендуется)

Сохранить plan-поле `mode` со значениями `transit | anchorage | manual_override` и добавить `override_mode: transit | anchorage | null` для однозначности. Во время override `mode=manual_override`, `override_mode` показывает применяемый effective mode; после expiry `mode` снова automatic, `override_mode=null`, `override_until=null`.

Минимальный response:

```json
{
  "mode": "transit|anchorage|manual_override",
  "override_mode": "transit|anchorage|null",
  "rpm_ge1": 120.0,
  "threshold_transit": 400.0,
  "sound_enabled": false,
  "night_dim": true,
  "override_until": null
}
```

`rpm_ge1` — latest value configured by `rpm_tag`; при missing/stale signal равен `null`. `threshold_transit` — configured value, не live warning threshold. Policy применяется к effective mode (`override_mode` при manual override, иначе automatic mode).

POST `/api/vessel/state/override` принимает только `{mode: "transit|anchorage", ttl_minutes: integer}`. `ttl_minutes` ограничен `1..1440`; zero, negative, float/string и неизвестный mode дают 422. Ответ — тот же state response после записи. POST не меняет ship-pack и не создаёт setpoint event.

**Решение:** вариант 2. Дополнительный `override_mode` предотвращает двусмысленность sample contract и не заставляет UI угадывать target.

## Компонент E — setpoints changelog (Architecture)

### Вариант 1: новый специализированный changelog store

Добавить отдельную таблицу/repository и писать туда при каждом изменении setpoint.

**Плюсы:** response оптимизирован под экран уставок.  
**Минусы:** s11 не имеет write setpoints route; второй event log может разойтись с canonical events и потребует миграции/dual-write.

### Вариант 2: read adapter над canonical events (рекомендуется)

`SetpointsService.changelog(from_ts, to_ts)` использует существующий event query seam с `event_name=setpoint_changed`, затем нормализует event params в typed response. Canonical event остаётся источником истины. Поля changelog item: `id`, `ts`, `tag_id`, `old_value`, `new_value`, `unit`, `source`, `actor` (nullable при legacy event). Неизвестные дополнительные params не теряются во внутреннем raw event, но наружу допускаются только контрактные поля.

`from` и `to` — UTC inclusive bounds, совпадающие с существующим `/api/events` filter semantics; `to < from` → 422. Результат стабильно сортируется `ts ASC, id ASC`. Если event store пуст, ответ `{items: []}`; текущая YAML history не подмешивается.

**Плюсы:** нет второго журнала и write path; переиспользуется cursor/filter/query infrastructure; changelog действительно показывает изменения, а не только snapshots.  
**Минусы:** нужно зафиксировать mapping legacy params и обработать неполное событие без утечки DB row.

**Решение:** вариант 2. Для s11 достаточно bounded `limit` (1..200) даже если plan query показывает только from/to; pagination добавляется как additive поле только если существующий events seam требует его.

## Ошибки и fail-closed поведение

- Некорректный `vessel.yaml` → startup/config error с внутренним structured log; не подставлять threshold из warnings.
- Latest rpm отсутствует/stale/bad quality → 200 с `anchorage`, `rpm_ge1=null`; это безопасное состояние, не HTTP 500.
- Redis unavailable на GET → automatic state может быть отдан без override только если отсутствие override явно различимо в adapter; при active override lookup failure лучше 503, чем silently отменить ручной режим. POST при недоступном Redis → 503.
- Unknown tag history → существующий 404 `TAG_NOT_FOUND` сохраняется.
- Changelog event без `tag_id`, `new_value` или timestamp → не ломать весь список: пропустить malformed event и записать metric/log; если canonical query возвращает только malformed records, ответ пустой с диагностикой. Не выдавать неполный item.
- Ошибки не содержат stack trace, SQL или Redis payload в API envelope.

## Тестовая стратегия и свойства

1. `vessel.yaml` fixture валиден и содержит `rpm_tag`, threshold, freshness и обе policies.
2. Threshold: ровно `rpm == threshold` → transit; `threshold - epsilon` → anchorage.
3. Missing/stale/non-numeric rpm → anchorage и `rpm_ge1=null`.
4. Active override заменяет automatic mode, возвращает `mode=manual_override`, `override_mode`, policy и `override_until`.
5. Expired override игнорируется/удаляется и возвращается automatic state; TTL не требует sleep/background worker.
6. POST принимает только transit/anchorage и integer TTL 1..1440; setpoints mutation paths отсутствуют в OpenAPI.
7. Changelog передаёт `from`/`to` в canonical event query, фильтрует только `setpoint_changed`, сортирует и маппит typed items.
8. Changelog не включает current YAML item и не создаёт write event от GET/override.
9. Property-based invariants: mode partition (`< threshold`, `>= threshold`), expiry monotonicity (`now >= expires_at` никогда не active), UTC round-trip, `from <= to` validation, и no mutation route under `/api/setpoints`.
10. Async tests используют fake reader/store; не запускают Redis/DB для domain rules. Один API integration test проверяет dependency wiring и OpenAPI audit.

## Integration check перед IMPLEMENT FINISH

- [ ] `vessel.yaml` loader ↔ `tag_map.yaml` (`rpm_tag`, unit/type) согласованы.
- [ ] Latest-value adapter использует существующий collector/sample seam, не новый параллельный snapshot format.
- [ ] Redis dependency и key/TTL policy согласованы с текущими settings/dependencies; local fallback запрещён.
- [ ] Event query mapping сверен с `apps/api/app/events/queries_events.py` и `EventItem` fields.
- [ ] OpenAPI mutation audit расширен на `/api/setpoints`, `/api/setpoints/history`, `/api/setpoints/changelog`.
- [ ] `s12` может читать `vessel_state.anchorage` без повторной реализации rpm threshold.

## Verification checklist

- [x] Один epic-scoped creative-файл создан для CR-P2-09.
- [x] Core skills и 4 situational skills перечислены в `## Skills gate`.
- [x] CR-P2-09 классифицирован как Architecture + Algorithm.
- [x] Для config, service, override storage, HTTP contract и changelog предложены минимум 2 варианта.
- [x] Выбран dedicated vessel config, service с узкими ports, Redis native TTL и canonical events adapter.
- [x] Зафиксированы missing/stale rpm fail-closed semantics и TTL без background reset.
- [x] Зафиксировано отсутствие любых setpoints mutation routes.
- [x] s11 rewired на этот закрытый artifact и следующий phase = BACK IMPLEMENT.

## Следующая команда

**BACK IMPLEMENT @s11** — реализовать vessel config/state service, bounded manual override TTL и read-only setpoints changelog по закрытому CR-P2-09.
