# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-06 B11 роли и session authorization

**Creative ID:** CR-P2-06  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [decompose-v1-p2-ship/index.md](../../plan/decompose-v1-p2-ship/index.md)  
**Зависимые шаги:** [s14-i7-hardening-audit.yaml](../../plan/decompose-v1-p2-ship/s14-i7-hardening-audit.yaml), [s16-admin-api-storage-ota.yaml](../../plan/decompose-v1-p2-ship/s16-admin-api-storage-ota.yaml)  
**Дата:** 2026-07-31  
**Режим:** BACK CREATIVE  
**Уровень:** L4  
**Типы решений:** Architecture + Algorithm  
**Статус:** closed

## Skills gate

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/architecture-patterns/SKILL.md`
- `.agents/skills/improve-codebase-architecture/SKILL.md`
- `.agents/skills/python-design-patterns/SKILL.md`
- `.agents/skills/property-based-testing/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture` — role policy должна быть глубоким seam между roster/session и admin endpoint; endpoint не должен сам разбирать rank или список строк.
- `python-design-patterns` — KISS/SRP: явная permission matrix и один injected `RoleGate`; не вводить generic RBAC registry до появления третьей независимой ролевой подсистемы.
- `property-based-testing` — role claims и permission matrix имеют конечные инварианты: неизвестная роль не даёт доступ, пустые/лишние claims не эскалируют права, изменение roster не меняет уже созданную сессию.

## Контекст и ограничения

B11 нужен для I5/I6/I7 admin surface. В текущем session seam уже есть `roster.yaml`, `SessionState`, cookie `shipsense_session`, `SessionService` и append-only `access_audit`. В roster пока есть `person_id`, `name`, `rank`, `active`, `default_screen`, но нет отдельного authorization claim. План требует:

- `chief_engineer` для OTA approve;
- admin read API для storage/OTA/access audit;
- role gate для `chief_engineer` и `electromechanic`;
- localhost bind и отсутствие WAN exposure;
- backward-compatible additive API, без вывода прав из `rank`.

Security invariant: **rank — display metadata, role — explicit authorization data**. Никогда не считать `rank == chief engineer` достаточным основанием для права.

## 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

**Decompose steps:** [s14-i7-hardening-audit.yaml](../../plan/decompose-v1-p2-ship/s14-i7-hardening-audit.yaml), [s16-admin-api-storage-ota.yaml](../../plan/decompose-v1-p2-ship/s16-admin-api-storage-ota.yaml)

### Компонент 1 — источник role claims

#### Вариант A — явные `roles` в `roster.yaml` (выбран)

Пример контракта для person entry:

```yaml
- person_id: ivanov
  name: Иванов И.И.
  rank: chief engineer
  roles: [chief_engineer]
  tile_order: 1
  active: true
  default_screen: 1
```

**Плюсы:** claim находится рядом с identity, reviewable в ship-pack, не зависит от локализации rank, не требует новой identity-БД; session получает snapshot ролей при login.  
**Минусы:** изменение прав требует доставки ship-pack/операционной процедуры; это приемлемо для edge v1.

#### Вариант B — отдельный `roles.yaml`/policy file

`roster.yaml` содержит только identity, а roles маппятся в отдельном allowlist-файле по `person_id`.

**Плюсы:** permission review отделён от UI roster.  
**Минусы:** два файла образуют опасный split-brain (person удалён/переименован, а role mapping остался), сложнее атомарно проверять пакет и отлаживать onboard.

#### Вариант C — роли в базе данных

При login session service читает person и roles из SQL.

**Плюсы:** централизованное изменение claims.  
**Минусы:** admin login начинает зависеть от БД, усложняет offline edge boot и миграции; это противоречит текущему ship-pack/session seam.

**Рекомендуемый подход:** вариант A. Для backward compatibility отсутствие `roles` означает только безопасный `watch_officer` для уже существующих non-admin roster entries; отсутствие roles никогда не даёт admin permission. Admin roles должны быть перечислены явно и пройти validation.

### Компонент 2 — доменная модель authorization

#### Вариант A — `Role` enum + явная `Permission` matrix (выбран)

Минимальные роли v1:

- `watch_officer` — обычный вахтенный доступ, без admin API;
- `electromechanic` — read-only storage/OTA/audit admin views;
- `chief_engineer` — те же read views, OTA approve и trigger при выполнении OTA policy.

Права v1:

| Permission | watch_officer | electromechanic | chief_engineer |
|---|:---:|:---:|:---:|
| `admin.storage.read` | — | ✅ | ✅ |
| `admin.ota.status.read` | — | ✅ | ✅ |
| `admin.access_audit.read` | — | ✅ | ✅ |
| `admin.ota.approve` | — | — | ✅ |
| `admin.ota.trigger` | — | — | ✅ |

`RoleGate` принимает immutable session claims и требуемое permission; неизвестная роль/permission → deny. Endpoint получает результат gate, но не знает, как роль хранится.

**Плюсы:** небольшая закрытая matrix, deny-by-default, тестируется без FastAPI/БД; новые endpoint должны явно выбрать permission.  
**Минусы:** matrix надо обновлять при добавлении admin operation; это полезная точка review, а не скрытая магия.

#### Вариант B — иерархический rank-based RBAC

`chief_engineer` наследует права `electromechanic`, а роли сравниваются по numeric level.

**Плюсы:** меньше строк при росте ролей.  
**Минусы:** создаёт неявные права и опасную зависимость от порядка ролей; `trigger` и `approve` не обязаны быть линейными. Для v1 запрещён.

#### Вариант C — свободный список capability strings без enum

Каждый roster entry получает `permissions: [...]` напрямую.

**Плюсы:** гибкость.  
**Минусы:** опечатка становится policy bug, ship-pack теряет понятные roles, трудно проверить least privilege. Не выбран.

**Рекомендуемый подход:** вариант A. Уровни и inheritance не вводить; permission matrix должна быть короткой и видимой в тестах/документации.

## 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

### Компонент 3 — граница session и admin endpoint

#### Вариант A — session snapshot + injected `RoleGate` (выбран)

При `SessionService.start()` claims из активного roster entry валидируются и копируются в `SessionState.roles: frozenset[Role]`. `SessionResponse` может additive вернуть `roles` для UI-индикации, но UI не является источником authorization. `get_current()` возвращает только неистёкшую сессию; role dependency делает:

1. извлечение cookie;
2. lookup текущей сессии и проверку idle/max expiry;
3. проверку permission через `RoleGate`;
4. `403` с одним стабильным кодом при недостатке права.

Claims не перечитываются из roster на каждый запрос: права уже начавшейся сессии стабильны до logout/expiry. После изменения roster новый login получает новый snapshot. Session service остаётся edge-local и не получает JWT/внешний IdP.

**Плюсы:** locality и auditability; endpoint тонкий; отзыв claims гарантируется следующим login, а текущая сессия не меняет смысл посреди операции; unit tests не требуют сети.  
**Минусы:** экстренный revoke требует logout/expiry или явного session invalidation, который не входит в B11 v1.

#### Вариант B — читать roster roles на каждый admin request

**Плюсы:** быстрый revoke после изменения файла.  
**Минусы:** authorization становится зависимым от YAML I/O на hot path, возможны разные права внутри одной сессии, сложнее объяснить audit; не выбран.

#### Вариант C — JWT с role claims

**Плюсы:** stateless dependency и горизонтальное масштабирование.  
**Минусы:** на edge v1 нет нужды в stateless multi-node auth, отзыв требует key rotation/denylist, а текущий cookie/session contract пришлось бы ломать. Не выбран.

**Рекомендуемый подход:** вариант A, с явным `roles` snapshot и одной dependency factory `require_permission(...)`.

## 🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm

### Компонент 4 — order of checks и fail-closed

Для admin request алгоритм фиксируется так:

1. Если listener/request не проходит localhost-only deployment boundary, запрос недоступен независимо от роли.
2. Если cookie отсутствует, сессия отсутствует или истекла — `401 SESSION_REQUIRED`.
3. Если session существует, но permission не входит в `RoleGate` matrix — `403 FORBIDDEN` и append audit action `admin_access_denied` с `person_id`, `session_id`, `source_ip`, permission и stable reason.
4. Для `POST /api/admin/ota/approve` после permission check вызывается OTA coordinator; endpoint не меняет OTA state напрямую.
5. Для `POST /api/admin/ota/trigger` сначала проверяется permission, затем `update_allowed`/anchorage/health policy в OTA coordinator. Role alone не может обойти safety gate.
6. Неизвестные claims, malformed roster roles и policy lookup error дают deny/startup validation error; тихого возврата к rank или `watch_officer` для явно заданного malformed admin claim нет.

Denied audit — часть access trail, но ошибка самого audit storage не должна превращать `403` в успешный доступ: при требуемом для security deployment audit failure request считается failed-closed (`503 AUDIT_UNAVAILABLE`) и действие не выполняется.

### Стабильные коды

| Ситуация | HTTP | Код |
|---|---:|---|
| cookie/session отсутствует или expired | 401 | `SESSION_REQUIRED` |
| роль не имеет permission | 403 | `FORBIDDEN` |
| malformed explicit roles в roster | startup/config error | `INVALID_ROLES_CONFIG` |
| OTA policy не разрешает trigger | 409 | `OTA_UPDATE_NOT_ALLOWED` |
| audit append недоступен | 503 | `AUDIT_UNAVAILABLE` |

`403` не раскрывает, какие другие роли существуют. Internal structured log/audit может хранить permission и stable reason.

### Инварианты для реализации и тестов

- неизвестная роль никогда не превращается в известную роль;
- `watch_officer` не получает ни одного `admin.*` permission;
- `electromechanic` не получает `admin.ota.approve` или `admin.ota.trigger`;
- `chief_engineer` не обходится вокруг `update_allowed`;
- пустой/отсутствующий roles claim безопасен для обычной сессии, но никогда не admin;
- claims в `SessionState` не меняются от последующей правки roster;
- logout/expiry лишает все permissions;
- каждый admin POST с разрешённым или отклонённым решением имеет audit trail; denied action не доходит до OTA/storage writer;
- permission matrix детерминирована и не зависит от порядка ролей в YAML.

## Рекомендации по реализации

1. Расширить typed roster/session schemas моделями `Role` и `Permission`; roles нормализовать как lowercase exact identifiers, без fuzzy matching.
2. Загрузчик roster валидирует `roles`: неизвестные значения и дубликаты — config error; legacy entry без поля получает только `watch_officer`.
3. Расширить `RosterPerson`, `SessionState`, `SessionResponse` additive-полем `roles`; не переименовывать текущие поля и не менять cookie contract.
4. Вынести matrix и проверку в узкий модуль `app/session/authorization.py`; API dependency импортирует только policy seam.
5. Добавить `require_permission` dependency для admin routers. Не дублировать проверки rank в `admin_ota.py`, `admin_storage.py`, `admin_audit.py`.
6. Session middleware/writer передаёт `session_id`, `person_id`, role snapshot и source IP в access audit. События login/logout остаются canonical events.
7. Admin routers bind only on localhost/internal API listener в compose/config; role gate — второй независимый барьер, не замена network boundary.
8. Для approve/trigger использовать injected OTA coordinator port из s12; authorization не знает RAUC/U-Boot, shell, DB или storage details.
9. Не добавлять user management, password reset, external IdP, JWT refresh или role hierarchy в v1.

## Integration check перед IMPLEMENT FINISH

- [ ] `roster.yaml` fixture и production ship-pack имеют explicit `roles` для admin persons; legacy fixtures получают только `watch_officer`.
- [ ] `SessionState` snapshot передаёт roles в admin dependency; expiry и cookie mismatch дают `401`.
- [ ] `RoleGate` matrix покрыта unit/property tests для неизвестных, дубликатов и permutation roles.
- [ ] s14 access_audit сохраняет login/logout и denied admin attempts без update/delete API.
- [ ] s16 admin routes используют permission dependency, а не `rank` string или прямой `roles` parsing.
- [ ] `/api/admin/ota/approve` требует `chief_engineer`; `/api/admin/ota/trigger` требует ту же роль и остаётся за OTA `update_allowed` gate.
- [ ] `electromechanic` имеет только read permissions из matrix.
- [ ] compose/listeners подтверждают localhost-only admin exposure и отсутствие WAN port.
- [ ] OpenAPI показывает admin tag и additive `roles` response field без удаления p1 contract.

## Rewire

- [x] s14: CR-P2-06 закрыт; ссылка на этот artifact добавлена; `Next Phase: BACK IMPLEMENT`.
- [x] s16: CR-P2-06 закрыт; ссылка на этот artifact добавлена; `Next Phase: BACK IMPLEMENT`.
- [x] decompose index: CR-P2-06 отмечен ✅; s14 и s16 → `needs_creative: yes (CR-P2-06) ✅` / step `yes (CR-P2-06) — **closed**`; next phase — `BACK IMPLEMENT`.

## Verification checklist

- [x] Один epic-scoped creative artifact создан для CR-P2-06.
- [x] `## Skills gate` содержит 2 core и 3 situational skills из allowlist.
- [x] Решения классифицированы как Architecture + Algorithm.
- [x] Для источника claims, permission model и session boundary предложено минимум 2 варианта с pros/cons.
- [x] Выбраны explicit roster roles, closed permission matrix и session snapshot с fail-closed dependency.
- [x] Зафиксированы least privilege, localhost boundary, stable errors и OTA safety gate.
- [x] Зависимые s14/s16 и decompose index rewired.

## Handoff

- **Done:** BACK CREATIVE CR-P2-06 — explicit roster roles, `Role`/`Permission` matrix, session claims snapshot и fail-closed admin authorization для I7/s16.
- **Files:** [creative-b11-roles.md](creative-b11-roles.md); rewired [s14-i7-hardening-audit.yaml](../../plan/decompose-v1-p2-ship/s14-i7-hardening-audit.yaml), [s16-admin-api-storage-ota.yaml](../../plan/decompose-v1-p2-ship/s16-admin-api-storage-ota.yaml), [decompose index](../../plan/decompose-v1-p2-ship/index.md).
- **Next:** `BACK IMPLEMENT` @s14; после s14 — @s15, затем @s16 по очереди.
- **Tool / model:** Claude Code + GPT для CREATIVE; implementation — в новой сессии.
- **New chat:** yes — один чат = один atomic subtask.
- **code_changed:** no.
