# Шаг r01: Scaffold `apps/api` per fastapi-templates
**Epic ID:** rf-fastapi-template-ownership  
**Next Phase:** BACK REFACTOR  
**needs_creative:** no  
**Creative:** —  
**tdd:** yes  
**Priority:** Critical  
**Depends:** —  
**code_changed:** yes  
**AC:** plan §5.1 AC A

> **Policy:** статус шага здесь не хранить. Статус — в `decompose/index.md` и `implement/rNN-*.md`.

---

## Skills meta (HARD — канон для REFACTOR execute)

**code_surface:** api

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`
- `.agents/skills/fastapi-templates/SKILL.md`

---

## Цель
Появиться пакету `app` под `apps/api/` по skill layout: `create_app`, settings, `api/v1` + stub health; pythonpath/testpaths включают `apps/api`. Без переноса домена.

## Контекст
- **Consumes:** plan §2.1 tree, §8 packaging, §17 URL freeze (`/api/...` без обязательного `/v1` в URL); skill fastapi-templates Pattern 1.
- **Produces:** importable `from app.main import app`; stub `GET` health; пустые feature packages `telemetry`/`events` (placeholders OK).

## Файлы
- `apps/api/README.md` (Создание)
- `apps/api/app/__init__.py` (Создание)
- `apps/api/app/main.py` (Создание) — `create_app()` + lifespan
- `apps/api/app/api/__init__.py` (Создание)
- `apps/api/app/api/deps.py` (Создание) — stub OK
- `apps/api/app/api/v1/__init__.py` (Создание)
- `apps/api/app/api/v1/api.py` (Создание) — сборка `APIRouter`
- `apps/api/app/api/v1/endpoints/__init__.py` (Создание)
- `apps/api/app/api/v1/endpoints/health.py` (Создание) — stub
- `apps/api/app/core/__init__.py` (Создание)
- `apps/api/app/core/settings.py` (Создание) — каркас `ApiSettings`
- `apps/api/app/core/exceptions.py` (Создание) — stub OK
- `apps/api/app/core/dependencies.py` (Создание) — stub OK
- `apps/api/app/core/middleware.py` (Создание) — stub/minimal OK
- `apps/api/app/core/database/__init__.py` (Создание) — stub OK
- `apps/api/app/telemetry/__init__.py` (Создание)
- `apps/api/app/events/__init__.py` (Создание)
- `apps/api/app/health/__init__.py` (Создание) — опц.
- `apps/api/tests/conftest.py` (Создание)
- `apps/api/tests/api/test_health_stub.py` (Создание)
- `pyproject.toml` (Модификация) — `pythonpath` += `apps/api`; `testpaths` += `apps/api/tests`

**Не создавать:** `apps/edge/api/`; полный набор business endpoints (T-003).

## Интерфейсы (lean — без кода)
- settings: `ApiSettings` — поля-каркас из plan T-003 §21 / rf-plan (имена: DATABASE_URL, SHIP_PACK_PATH, API_HOST, API_PORT, API_V1_STR или эквивалент mount prefix); defaults допустимы
- app: `create_app() -> FastAPI` — include `api_router`; openapi/docs под `/api/...` (plan §17: URL product freeze)
- router: mount prefix = `/api` (папка пакета `v1` ≠ обязательный URL `/api/v1`)
- route: stub health — `GET` путь согласован с будущим T-003 (`/api/health` предпочтительно)
- packages: `app.telemetry`, `app.events` — пустые/`__init__` до r02

## TDD (красная → зелёная)
1. **Тест:** `apps/api/tests/api/test_health_stub.py` — `from app.main import app`; ASGI client: health → 200; OpenAPI доступен.
2. **Запуск:** FAIL — пакета/`app` нет.
3. **Реализация:** дерево §2.1 минимум + pythonpath.
4. **Запуск:** `.venv/bin/pytest apps/api/tests -q` PASS.

## Подробный процесс выполнения
1. Baseline: убедиться что `apps/api` отсутствует.
2. Создать дерево каталогов skill (подпакеты `app.api`, `app.core` — **не** siblings `apps/api/api`).
3. `ApiSettings` + `create_app` + lifespan no-op/optional.
4. Stub health endpoint; собрать `api_router`.
5. Обновить корневой `pyproject.toml` pythonpath/testpaths.
6. Тесты ASGI; README кратко: канон = fastapi-templates, домен переносится в r02+.

## Чекпоинт верификации
- `from app.main import app` из pytest
- Нет `apps/edge/api`
- Структура ≥ main, api/v1, core, telemetry, events
- Behavior freeze: нет бизнес-логики T-003
