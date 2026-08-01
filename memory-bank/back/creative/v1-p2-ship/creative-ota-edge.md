# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-10 и CR-P2-12

**Creative IDs:** CR-P2-10 · CR-P2-12  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [decompose-v1-p2-ship/index.md](../../plan/decompose-v1-p2-ship/index.md)  
**Связанный шаг:** [s12-i5-ota-rauc.md](../../plan/decompose-v1-p2-ship/s12-i5-ota-rauc.md)  
**Дата:** 2026-07-31  
**Режим:** BACK CREATIVE  
**Уровень:** L4  
**Статус:** closed

## Skills gate

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/architecture-patterns/SKILL.md`
- `.agents/skills/improve-codebase-architecture/SKILL.md`
- `.agents/skills/python-design-patterns/SKILL.md`
- `.agents/skills/property-based-testing/SKILL.md`
- `.agents/skills/async-python-patterns/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture` — удержать глубокий seam между pure health policy и системными probe/RAUC adapters; не смешивать shell, HTTP и доменные решения.
- `python-design-patterns` — оставить KISS/SRP: policy и state transitions — pure functions, внешние вызовы — узкие injected ports, без generic plugin registry.
- `property-based-testing` — проверить инварианты fail-closed, unknown signal и переходы A/B; примерных сценариев T5 недостаточно для всех комбинаций сигналов.
- `async-python-patterns` — health probes вызывают несколько I/O источников и должны иметь явные timeout/cancellation boundaries; параллелить только независимые probe, не скрывая ошибку.

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture — CR-P2-10 OTA health policy

## Проблема и границы

OTA healthcheck не должен отвечать на вопрос «процесс запущен?». Для `mark_good` нужно доказать, что после загрузки нового слота продолжается сбор данных, API отвечает и база принимает запись. Любой missing, malformed, timeout или неоднозначный сигнал трактуется как `unknown`, а `unknown` не даёт разрешения.

CR-P2-10 фиксирует v1 policy contract, но не привязывает pure rules к `systemd`, PostgreSQL client, FastAPI client или RAUC CLI. Эти зависимости остаются adapters в `apps/edge/ota/`.

## Вариант 1 — один shell healthcheck с exit code

**Плюсы:** минимальный объём кода; удобно вызвать из boot hook; легко воспроизвести вручную на стенде.

**Минусы:** parsing timestamp/JSON и правила последовательных проб становятся хрупкими; тесты начинают зависеть от shell и окружения; трудно отличить unknown от false; нельзя безопасно переиспользовать policy в T5 harness.

**Решение:** reject как основной production seam. Shell допускается только как тонкий launcher typed Python healthcheck.

## Вариант 2 — pure policy + typed probe adapters (рекомендуется)

**Плюсы:** exact thresholds и state transitions тестируются без ОС; каждый внешний probe имеет timeout и typed result; T5 lab mocks и production adapters используют один контракт; fail-closed виден в одном месте.

**Минусы:** больше файлов, чем у shell-only решения; нужно дисциплинированно не переносить I/O внутрь policy.

**Решение:** выбрать для v1.

## Вариант 3 — health daemon с event stream и persistent history

**Плюсы:** можно строить долгие графики деградации и сложные rollout strategies; отдельный daemon потенциально обслуживает несколько consumers.

**Минусы:** новый постоянно работающий процесс, lifecycle и storage; для одного локального OTA gate это лишняя глубина и ещё один источник отказа; history не требуется для `mark_good`.

**Решение:** не включать в v1; при появлении fleet rollout выделить отдельный ADR.

## Рекомендуемый health contract

### Typed signals

Policy получает snapshot из трёх обязательных probe:

1. **Collector data-flow:** `last_sample_at` — валидный UTC timestamp из локального collector status seam. Проверка проходит строго при `sample_age < 60 секунд`. Будущий timestamp, отсутствующий timestamp, невалидный формат и отрицательно вычисленный age дают `unknown` и fail.
2. **API readiness:** локальный `GET /api/health` с timeout **3 секунды**. Проходит только HTTP 200 с машинным статусом `ok` и готовыми обязательными dependencies; HTML, пустой body, любой другой status или timeout дают fail/unknown, но никогда pass.
3. **DB writable:** отдельный adapter выполняет короткую транзакцию записи в заранее созданный probe relation и делает `ROLLBACK`. Проверяется не только соединение: read-only transaction, недоступная БД, timeout, `in_recovery` или ошибка записи дают fail. Probe не оставляет постоянных строк и не использует production events.

Каждый signal имеет значение `pass | fail | unknown` и диагностический stable code; текст ошибки не используется policy для ветвления.

### Sampling и boot confirmation

- Probe cycle выполняется раз в **5 секунд**.
- Один snapshot — атомарная оценка всех обязательных signals на одном цикле; частичный snapshot не становится `pass`.
- `mark_good` разрешён только после **трёх последовательных полных pass-снимков** (окно 15 секунд).
- Boot confirmation deadline — **180 секунд** от старта healthcheck. Если deadline истёк без трёх pass, healthcheck завершается non-zero, слот остаётся pending, bootloader выполняет rollback в активный слот A.
- Ошибка отдельного цикла не сбрасывает уже накопленный диагноз в «успех»; sequence pass обнуляется при fail/unknown. Никакой автоматической попытки «угадать» последний хороший snapshot.
- Healthcheck ограничивает все внешние вызовы timeout-ами и корректно обрабатывает cancellation; зависший probe не удерживает boot hook бесконечно.

### Stable outcome

```text
HEALTH_PASS      — три последовательных полных pass; разрешить mark_good
HEALTH_PENDING   — цикл ещё в пределах 180 s; не mark_good
HEALTH_FAIL      — deadline или hard failure; non-zero, rollback path
HEALTH_UNKNOWN   — недостаточно данных; тот же fail-closed outcome, отдельный код для диагностики
```

`HEALTH_UNKNOWN` не является отдельным успешным состоянием и не может быть преобразован в `HEALTH_PASS` adapter-ом.

## Anchorage gate

`update_allowed` — pure решение над уже полученными facts:

```text
update_allowed =
    vessel_state.anchorage is true
    and health_failure is false
    and pending_rollback is false
    and inactive_slot_ready is true
    and bundle_signature_valid is true
```

- `vessel_state.anchorage` читается через существующий s11 vessel-state contract; stale/missing/bad rpm остаётся fail-closed anchorage согласно CR-P2-09.
- Существующий bounded manual override может дать `anchorage`, но только с ограниченным TTL и аудируемым событием; отдельного «force transit update» API не добавляется.
- Любой `unknown` в обязательных facts даёт `update_allowed=false`.
- Проверка gate выполняется до записи в слот B и повторно непосредственно перед switch; после switch policy не может объявить новый слот good без health contract.
- `health_failure` и `pending_rollback` блокируют новый rollout до возврата на подтверждённый слот и ручного разбора.

## Pure seams и порты

В production-коде не смешивать subprocess/HTTP/DB с policy:

- `BundleVerifier` — проверяет Ed25519 signature и content hash до записи в inactive slot.
- `HealthProbe` adapters — collector/API/DB, каждый возвращает typed signal и stable diagnostic code.
- `HealthPolicy` — pure reducer snapshot sequence → outcome.
- `AnchorageGate` — pure facts → `update_allowed` и reason code.
- `SlotController` — RAUC/U-Boot adapter для active/pending slot, bootcount, mark-good и rollback.
- `healthcheck` CLI — только сбор probes, вызов policy и mapping outcome → exit code.

Отдельный orchestration service не добавляется: последовательность install → set pending → reboot → healthcheck остаётся в OTA agent, а каждый шаг вызывает один port.

## T5 verification contract для CR-P2-10

- broken image: новый слот не получает `mark_good`, deadline вызывает rollback;
- good image + dead collector: `last_sample_at` становится stale, sequence pass не набирается, rollback;
- API 200 с неполным/degraded machine status: не pass;
- DB connect без права записи: fail, даже если API и collector healthy;
- missing/malformed signal: `HEALTH_UNKNOWN`, non-zero;
- transient failure: текущий цикл сбрасывает consecutive-pass sequence, но не создаёт ложный rollback до deadline;
- три полных pass подряд: ровно один `mark_good`, pending очищается;
- cancellation/timeout probe: процесс завершается bounded образом.

Property-based инварианты:

- из `unverified` нет перехода в `pending`;
- `unknown` никогда не даёт `mark_good` или `update_allowed=true`;
- после fail/unknown consecutive-pass counter не увеличивается;
- rollback идемпотентен;
- число вызовов `mark_good` не больше одного на boot attempt;
- любой допустимый порядок независимых probe results даёт один и тот же verdict для snapshot.

# 🎨🎨🎨 EXITING CREATIVE PHASE

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture — CR-P2-12 edge OS base

## Проблема и критерии выбора

OTA, I6 storage и I7 hardening должны собираться на одном воспроизводимом edge image. Выбор OS не должен менять policy contract: два rootfs slots, RAUC bundle, U-Boot bootcount, `/etc/shipsense/ota_pubkey.pem`, persistent data и отсутствие shore/forwarder runtime в v1 image.

Критерии:

- Python 3.12, Docker/Compose и PostgreSQL 16/Timescale runtime без нестандартной ручной сборки;
- воспроизводимый образ и pinning package/image inputs;
- поддержка A/B RAUC + U-Boot и watchdog;
- минимальная attack surface и понятный hardening для I7;
- автономность без shore dependency, recovery через локальный носитель;
- возможность T5/T6 lab harness без переписывания production path.

## Вариант 1 — Ubuntu Server 24.04 LTS minimal + RAUC/U-Boot (рекомендуется)

**Плюсы:** совместим с текущими Python 3.12 и Docker/Compose assumptions; быстрее довести до лабораторного T5; понятные пакеты, диагностика и recovery tooling; LTS lifecycle подходит корабельному образу; RAUC сохраняет system-image A/B вместо in-place container patching.

**Минусы:** package surface шире, чем у специализированного image; reproducibility и hardening нужно enforce-ить manifest/checklist; bootloader/RAUC integration остаётся отдельной lab обязанностью.

**Решение:** выбрать для v1 при условии минимального профиля и pinned image manifest.

## Вариант 2 — Yocto-based image + RAUC/U-Boot

**Плюсы:** минимальный runtime, полный контроль пакетов и boot chain, сильная воспроизводимость после стабилизации layer set, меньшая attack surface.

**Минусы:** высокая стоимость первоначальной интеграции; отдельная поддержка BSP/kernel/device tree; риск отложить T5 и I6/I7 из-за OS build plumbing; текущая команда уже ориентирована на Docker/Compose и Ubuntu-like tooling.

**Решение:** оставить migration track после v1, не блокировать текущий ship.

## Вариант 3 — Ubuntu + Mender artifact

**Плюсы:** удобные artifact lifecycle и fleet-oriented deployment; хорошие resume semantics для fleet.

**Минусы:** внешний fleet/control-plane контур не входит в v1; сложнее доказать локальный boot watchdog/rollback для T5; дублирует уже выбранный RAUC A/B contract и расширяет supply-chain surface.

**Решение:** не включать в v1; Mender возможен только через новый ADR для shore/fleet phase.

## Рекомендуемый OS contract

### Base image

- Ubuntu Server **24.04 LTS minimal**, pinned release digest/package manifest.
- Python 3.12, Docker/Compose, PostgreSQL/Timescale runtime и только необходимые device/RAUC/U-Boot packages.
- Внешние apt repositories запрещены в production image; security updates входят в новый image build и проходят тот же signed OTA bundle, а не выполняются бесконтрольным in-place upgrade.
- `shipsense` application account — non-root; root privileges только через явно перечисленные systemd/RAUC wrappers.
- Shore forwarder, B9/I2 client и неиспользуемые protocol bridges отсутствуют из v1 image; exclusion grep остаётся AC для s14/s20.

### Slot и persistent data layout

```text
boot / U-Boot environment
rootfs_A   immutable system image
rootfs_B   immutable system image
persistent data: /var/lib/shipsense
persistent events/DB storage: managed by I6 contract
recovery/import media: explicitly mounted, not part of rootfs slots
```

- RAUC пишет только inactive rootfs slot и проверяет bundle signature/hash до activation.
- `BOOT_SLOT` и bootcount принадлежат bootloader; application не редактирует их напрямую.
- `rootfs_A/rootfs_B` не содержат mutable events/config secrets; user data, events, backup staging и ship-pack overrides находятся на persistent storage по contracts I6.
- `/etc/shipsense/ota_pubkey.pem` входит в trust contract образа; смена ключа и rotation procedure документируются в I7, но не расширяют этот creative batch.
- RAUC slot naming и bootloader env names — typed constants одного adapter; не размножать строки по healthcheck, CLI и tests.

### Boot and rollback

- Новый bundle: verify → write inactive slot → set pending/bootcount → reboot.
- Bootloader имеет ограниченное число попыток; отсутствие `mark_good` до 180-секундного health deadline возвращает активный слот.
- Rollback не удаляет persistent data и не пытается «починить» БД из rootfs boot hook.
- После rollback pending state очищается только adapter-ом, который подтвердил активный слот; повторный rollout запрещён при `pending_rollback=true`.

### Hardening contract для I7

CR-P2-12 задаёт image inputs, CR-P2-06 отдельно задаёт роли и audit:

- SSH disabled by default или только локальный maintenance profile с ключами; password login отсутствует.
- UFW/default network policy разрешает только необходимые локальные ports; OTA control path не открывается наружу сам по себе.
- systemd services имеют least-privilege user, bounded restart policy и watchdog integration.
- package manifest, image digest, RAUC bundle metadata и key fingerprint попадают в reproducibility/proof artifact.
- container images pinned по digest; production compose не тянет latest.

## Cross-step contract

| Зависимый шаг | Что фиксирует CR-P2-12 | Done check |
|---|---|---|
| s12 OTA | Ubuntu minimal + RAUC/U-Boot, A/B slots, persistent data, key path, boot deadline | T5 image boots; unsigned bundle rejected; rollback preserves data |
| s13 I6 | persistent data/events не живут только в rootfs slot; backup/restore path доступен после rollback | T6 restore и disk replacement не зависят от активного rootfs |
| s14 I7 | package/network/service hardening и exclusion list для v1 image | hardening checklist и grep gates проходят |
| s18 T5/T6 | lab driver проверяет тот же RAUC/boot/health contract, что production | CI mocks и hardware checklist используют одинаковые state names |

## Что не входит в CR-P2-12

- полноценный Yocto migration;
- fleet/shore update service или Mender control plane;
- key rotation implementation;
- выбор конкретной платы/BSP и production partition byte sizes;
- новый API для OTA approval/trigger (его реализует s16 после этого creative gate).

## Верификация CR-P2-12

- image build из pinned manifest повторяем на CI и в lab;
- `apps/edge/ota` видит два slots и ожидаемый `BOOT_SLOT` без hard-coded shell-only обходов;
- production image не содержит shore/forwarder imports и unpinned `latest` images;
- rootfs rollback не меняет persistent events/config;
- `ota_pubkey.pem` присутствует в ожидаемом trust path и fingerprint попадает в proof;
- T5 сценарии 1–5 из plan выполняются на Ubuntu lab image с RAUC/U-Boot mocks, затем hardware checklist фиксирует реальные bootloader steps.

# 🎨🎨🎨 EXITING CREATIVE PHASE

## Implementation guidance

1. s12 первым пишет pure `HealthPolicy`, `AnchorageGate` и state transitions, затем typed probe/RAUC adapters; не начинать с subprocess wrapper.
2. Все threshold constants (`60s`, `3s`, `5s`, `3 passes`, `180s`) находятся в одном immutable policy config и попадают в diagnostics; не дублировать literals в tests и shell.
3. Health probe result должен различать `fail` и `unknown`, но оба остаются non-success для bootloader; UI/API позже может показать stable reason без изменения state machine.
4. s13 использует persistent storage contract, не заливает backup в rootfs slots и не добавляет OS-specific RAID logic в OTA policy.
5. s14 применяет hardening к образу, а не к healthcheck; access roles и audit trail остаются CR-P2-06.
6. s18 переиспользует pure state machine и ports, подменяя только bootloader/DB/collector drivers; production adapters не должны быть условным кодом «если тест».
7. Не добавлять generic plugin framework, event bus, fleet daemon или второй OTA engine.

## Verification summary

- [x] Один epic-scoped creative-файл с двумя CR batch.
- [x] `## Skills gate` содержит 2 core + 4 situational skills; situational ≤5.
- [x] Для каждого CR представлены 3 варианта с pros/cons и рекомендацией.
- [x] Типы Architecture и Algorithm обозначены; pure seams и adapters разделены.
- [x] Exact health thresholds CR-P2-10 зафиксированы: `<60s`, timeout `3s`, cycle `5s`, `3` pass, deadline `180s`.
- [x] Edge OS CR-P2-12 зафиксирован: Ubuntu Server 24.04 LTS minimal + RAUC/U-Boot; Yocto/Mender оставлены альтернативами вне v1.
- [x] T5/T6 и I7 cross-step contracts определены.
- [x] Fail-closed и property-based invariants определены.

## Rewire

- [x] s12: CR-P2-10/12 — `closed`; Next Phase `BACK IMPLEMENT`.
- [x] s13: CR-P2-12 — `closed`; CR-P2-03 остаётся отдельным открытым gate.
- [x] s14: CR-P2-12 — `closed`; CR-P2-06 остаётся отдельным открытым gate.
- [x] s18: CR-P2-10 — `closed`; `needs_creative: no` не меняется.
- [x] decompose index: CR-P2-10 и CR-P2-12 отмечены ✅; s12 снят с CREATIVE queue.

## Handoff

- **Done:** BACK CREATIVE CR-P2-10/12 — зафиксированы typed fail-closed OTA health policy (`<60s`, `3s`, `5s`, 3 pass, 180s), anchorage gate и Ubuntu Server 24.04 LTS minimal + RAUC/U-Boot A/B image contract.
- **Files:** [creative-ota-edge.md](creative-ota-edge.md); rewired s12, s13, s14, s18 и [decompose index](../../plan/decompose-v1-p2-ship/index.md).
- **Next:** `BACK IMPLEMENT` @s12; s13/s14 остаются на своих CR-P2-03/06.
- **Tool / model:** Claude Code + premium-coding для CREATIVE; Cursor + fast-editing для IMPLEMENT.
- **New chat:** yes — один чат = один atomic subtask.
- **code_changed:** no.
