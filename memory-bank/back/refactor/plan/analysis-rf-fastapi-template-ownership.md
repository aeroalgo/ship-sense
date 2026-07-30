# Analysis — rf-fastapi-template-ownership

**Дата:** 2026-07-30  
**Команда:** BACK REFACTOR PLAN  
**Scope:** M/L  
**Epic ID:** `rf-fastapi-template-ownership`  
**Канон структуры:** `.agents/skills/fastapi-templates/SKILL.md`  
**Связанный feature:** T-003 / `plan-v1-p1-api` (ещё не IMPLEMENT; путь `apps/edge/api` устаревает)

## 1. Проблема (Architecture)

Текущий monorepo растёт **от edge-процессов и коннекторов**:

```
apps/edge/
  collector/   ← владеет каноническим доменом (Quality, TelemetrySample, Event)
  storage/     ← импортирует модели ИЗ collector (инверсия владения)
  semantic/    ← ship-pack models вне FastAPI-приложения
  emulator/
  writer-stub/
  (api — в плане как apps/edge/api/routers|services|schemas)
```

Целевое приложение по skill — **FastAPI template**:

```
backend/ (= apps/api/)
  app/                 # домен model/schema/service по фичам + main.py
    api/v1/endpoints/  # тонкие HTTP handlers
    core/              # settings, deps, database, middleware
  migrations/
  tests/
```

Сейчас канонические pydantic-модели живут в `collector.domain.models`, а storage/tests тянут их через  
`apps.edge.collector.src.collector.domain.models` — **домен принадлежит коннекторному пакету**.  
План T-003 закрепляет ещё один антипаттерн: API как sibling «обвязка вокруг edge», а не приложение.

## 2. Evidence (graphify + grep)

- `TelemetrySample` degree≈48; импорты: collector sinks/normalizer, `storage/writer.py`, `samples_repo.py`, pipeline/storage tests.
- `storage/events_repo.py` ← `collector.domain.models.Event`.
- Plugins (modbus/opcua/mqtt/stub) корректно используют в основном `RawSample` / `RawTagDescriptor` — **эту часть оставить**.
- `apps/edge/api/` отсутствует; T-003 decompose s01 ещё pending — **окно для смены якоря без миграции живого API-кода**.

## 3. Severity backlog

| ID | Severity | Issue |
|----|----------|-------|
| A1 | **Critical** | Канон домена (`Quality`, `TelemetrySample`, `Event*`) владеет collector |
| A2 | **Critical** | `storage` / pipeline tests зависят от collector path (worker→connector) |
| A3 | **Critical** | T-003 plan §13 = `apps/edge/api` flat routers — **не** fastapi-templates |
| A4 | **High** | `semantic/` вне FastAPI app; API (T-003) будет потребителем №1 |
| A5 | **High** | Нет пакета `apps/api` / `app` — некуда переносить модели |
| A6 | **Medium** | `collector.domain.models` смешивает Raw* (OK) + canonical + health snapshot |
| A7 | **Medium** | `pythonpath` не включает будущий `apps/api` |
| A8 | **Low** | Docs/README collector утверждают «канон из collector.domain.models» |

## 4. Behavior freeze (HARD)

Рефакторинг **не** меняет:

- IPC wire JSON (`type` sample/event, поля TelemetrySample/Event) — только путь импорта Python-классов
- Enum values `Quality` / `EventSeverity`
- Timescale ORM schema (`storage/schemas.py`) и миграции
- Внешний REST/WS контракт T-003 (ещё не реализован) — **меняется только путь пакетов в плане**
- Протокольное поведение коннекторов

Нужна смена поведения → STOP → `BACK IMPLEMENT` / `CREATIVE`.

## 5. Выбранное решение (locked)

**Skill layout as-is** (`fastapi-templates`): корень приложения = `apps/api/`, Python-пакет = `app`.

**Не выбрано:** отдельный `packages/domain`; `apps/edge/api` flat; worker→import HTTP routers.

**Shared Kernel правило:** edge-процессы (`collector` normalizer/sinks, `storage` writer) **могут** импортировать **чистые** pydantic-модели из `app.<feature>.models` (без FastAPI/`Depends`/router).  
**Запрещено:** collector/storage → `app.api.*`, `app.main`, lifespan-only wiring.

## 6. Next

→ полный план: [plan-rf-fastapi-template-ownership.md](plan-rf-fastapi-template-ownership.md)  
→ после PLAN: `BACK REFACTOR DECOMPOSE` → `rNN` execute
