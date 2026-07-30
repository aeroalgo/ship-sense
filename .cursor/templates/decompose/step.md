# Шаг sNN: <title>
**Plan ID:** <plan_id>
**Next Phase:** BACK IMPLEMENT | BACK CREATIVE | FRONT IMPLEMENT | FRONT CREATIVE
**needs_creative:** no | yes (CR-…) | yes (CR-…) — **closed**
**Creative:** (если needs_creative) markdown-ссылка на `memory-bank/<role>/creative/…` — **обязательна после FRONT/BACK CREATIVE FINISH**; до закрытия — путь-плейсхолдер или «pending»

> **Policy:** статус шага здесь не хранить. Статус живёт только в `implement/sNN|eNN-*.md` и `decompose/index.md`.

---

## Skills meta (HARD — канон для IMPLEMENT)

Карта: `workflow-decompose.mdc` (BACK / FRONT). Пути копировать целиком. IMPLEMENT: **Read** все пути из блоков ниже **до** кода (Design — до UI-кода); **не** копировать этот список в implement-артефакт.

### BACK

**code_surface:** service | api | sql | model | infra | test

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- (service|api) `.agents/skills/python-anti-patterns/SKILL.md`
- (api) `.agents/skills/fastapi-templates/SKILL.md`
- (sql) `.agents/skills/supabase-postgres-best-practices/SKILL.md`
- (infra + lifecycle/deps) `.agents/skills/python-anti-patterns/SKILL.md`

FRONT — omit весь блок BACK (`code_surface` / BACK Impl skills).

### FRONT

**visible_ui:** yes | no

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/frontend-testing/SKILL.md`
- `.agents/skills/frontend-patterns/SKILL.md`
- `.agents/skills/next-best-practices/SKILL.md`
- `.agents/skills/vercel-react-best-practices/SKILL.md`
- `.agents/skills/vercel-composition-patterns/SKILL.md`
- (E2E / scenario) `.agents/skills/playwright-best-practices/SKILL.md`
- (новый E2E с нуля) `.agents/skills/playwright-generate-test/SKILL.md`

**Design skills (REQUIRED Read до UI-кода):** (если `visible_ui: yes`; иначе: `**Design skills:** — (причина)`)
- `.agents/skills/frontend-design/SKILL.md`
- `.agents/skills/design-taste-frontend/SKILL.md`
- `.agents/skills/emil-design-eng/SKILL.md`
- `.agents/skills/impeccable/SKILL.md`
- `.agents/skills/high-end-visual-design/SKILL.md`
- `.agents/skills/ui-ux-pro-max/SKILL.md`

BACK — omit весь блок FRONT (`visible_ui` / FRONT Impl / Design skills).

---

## Цель
<одна-две строки: что должен дать шаг после одного захода IMPLEMENT>

## Контекст
- **Consumes:** шаги декомпозиции (sNN), API/эндпоинты, `[creative-*.md](…)` (кликабельно после CREATIVE), env, внешние сервисы — что уже должно существовать до старта.
- **Produces:** файлы, контракты, UI-состояния, интеграции — что появится после шага.

## Файлы
- `path/to/file` (Создание | Модификация) — назначение файла

## Интерфейсы (lean — без кода)

Только объявления и якоря. **Запрещено:** тела методов, полные type/class с типами полей, copy-paste готовых файлов. Типы/реализацию пишет IMPLEMENT по паттерну соседних модулей.

**BACK (пример):**
- model: `ProviderApplication(Base)` — поля: `user_id`, `status`, `provider_type`, … (список имён; типы — из plan/s01)
- schema: `ProviderApplicationICreate|IRead|IUpdate|IFilter` — как у `supplier_request`
- crud: `CRUDProviderApplication(CRUDBase[…])` — методы: `get_active_for_user`, `get_by_user`

**FRONT (пример):**
- component: `ApplicationWizard` — props: `applicationId?`, `onSubmitted`
- hooks/api: `useProviderApplication`, `submitApplication` — как у соседних portal hooks
- types: расширить `ApiX` полями из plan (имена), без полного `interface {…}`

Если контракта нет (infra/seed/config) — одна строка: `n/a`.

## TDD (красная → зелёная)
1. **Тест:** `path/to/test` — что проверяем (Vitest/RTL, pytest, Playwright).
2. **Запуск:** тесты падают (файлов/реализации нет).
3. **Реализация:** …
4. **Запуск:** тесты проходят.

Если `tdd: no` в index — заменить блок на:
## TDD (нет)
- **Причина:** scaffold / infra / финальный QA без новой бизнес-логики.
- **Верификация:** smoke / build / E2E (указать команды).

`Impl skills` в Skills meta **оставляй** (слой B для Cursor / Claude Code). Фильтр «не читать tdd при docs-only» — в workflow A, не вырезанием списка из step.

## Подробный процесс выполнения
1. …
2. …

## Чекпоинт верификации
- …
