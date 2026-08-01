# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-08 B13 tag set

**Creative ID:** CR-P2-08  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [decompose-v1-p2-ship/index.md](../../plan/decompose-v1-p2-ship/index.md)  
**Зависимые шаги:** [s06-b13-drift-engine.yaml](../../plan/decompose-v1-p2-ship/s06-b13-drift-engine.yaml), [s07-b13-warnings-api.yaml](../../plan/decompose-v1-p2-ship/s07-b13-warnings-api.yaml)  
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
- `.agents/skills/python-performance-optimization/SKILL.md`
- `.agents/skills/async-python-patterns/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture` — зафиксировать глубокий seam между судовым ship-pack, pure DriftEngine и источниками samples/setpoints; не смешивать выбор тегов с EWMA или SQL-моделями.
- `python-design-patterns` — удержать конфигурационный объект и валидатор простыми; не вводить generic registry/factory для единственного v1-конфига.
- `property-based-testing` — проверять инварианты selection/threshold/mode filtering на большом пространстве конфигураций и исключить невалидное «разрешение» предупреждения.
- `python-performance-optimization` — ограничить подписку 50–120 тегами и не сканировать все 586 тегов на каждом worker tick.
- `async-python-patterns` — worker cadence и чтение samples/setpoints не должны блокировать API/WS; cancellation и timeout должны быть явными.

---

## Контекст и проблема

B13 предупреждает о дрейфе измерения к аварийной уставке. В текущем Makarov ship-pack есть 586 тегов:

- 321 аналоговый `degC` из `aps_main`;
- 161 дискретный `alarm_bit` из `aps_main`;
- 103 аналоговых `rpm` из `skt_geu`;
- один аналоговый `bar` (`SKT002`) из `skt_geu`.

У 320 температурных тегов есть `setpoints.alarm`. Однако B13 не должен автоматически подписываться на все 320: план задаёт worker примерно на 50–120 подписанных тегов, а переходные и нерелевантные параметры увеличивают шум, CPU и поверхность ложных предупреждений.

CR-P2-08 закрывает не «калибровку всех сигналов», а v1-контракт:

1. какие теги имеют право попасть в B13 worker;
2. как конфигурация проверяется до запуска;
3. как один rpm-тег подавляет переходные режимы;
4. как неизвестный/неполный tag set ведёт себя fail-closed;
5. какие поля конфигурации видны в active/history/API без машинного обучения и без строк `AI`/`ИИ`.

Калибровка `threshold_pct`, `ewma_window_hours` и `startup_guard_sec` после реального судового съёма остаётся операционной настройкой, а не основанием для изменения архитектуры.

---

## Общий architectural baseline

```text
ship-pack/makarov/tag_map.yaml ──┐
ship-pack/makarov/warnings.yaml ─┼─> WarningConfigLoader
B10 setpoints / T-002 samples ───┘          │
                                           ▼
                                  SelectionValidator
                                           │ typed selected tags
                                           ▼
                         DriftEngine + ModeFilter + EWMA math
                              │                         │
                              ▼                         ▼
                    active/history persistence      warning events
                              │                         │
                              └──────────────┬────────┘
                                             ▼
                                      B10 warnings API/WS
```

Зависимость направлена вниз: конфигурация и источники дают typed input; pure selection/mode/math не импортируют FastAPI, SQLAlchemy, YAML runtime или конкретный collector. API и persistence работают только с результатом engine и стабильной схемой `DriftWarning`.

**Deletion test:** отдельный универсальный `TagRegistry` не нужен. Если убрать его, сложность не исчезает и не концентрируется; простой `WarningConfig` со списком `WarningTagConfig` лучше сохраняет locality. Отдельный `SelectionValidator` нужен: он является реальным test surface для fail-closed правил и не является декоративным слоем.

---

## Компонент A — состав v1 tag set

### Вариант A1 — явный allowlist в warnings.yaml (рекомендуемый)

`warnings.yaml` содержит только теги, утверждённые для B13, с per-tag overrides. В v1 конфигурация фиксирует 53 тега: 52 температурных аналоговых тега с alarm setpoint из `aps_main` и один pressure tag `SKT002` из `skt_geu`.

Стартовый набор температурных тегов:

```yaml
TAI4101, TAI4102,
TAI4202, TAI4204, TAI4205, TAI4207, TAI4208,
TAI4210, TAI4211, TAI4213, TAI4214, TAI4216, TAI4217,
TAI4219, TAI4220, TAI4222, TAI4223, TAI4225, TAI4226,
TAI4228, TAI4229, TAI4231, TAI4232, TAI4234, TAI4235,
TAI4237, TAI4238, TAI4240, TAI4241, TAI4243, TAI4244,
TAI4246, TAI4247, TAI4249, TAI4250, TAI4252, TAI4253,
TAI4255, TAI4256, TAI4258, TAI4259, TAI4261, TAI4262,
TAI4264, TAI4265, TAI4267, TAI4268, TAI4270, TAI4271,
TAI4273, TAI4274, TAI4276, SKT002
```

**Плюсы:**

- reviewable diff и воспроизводимый replay;
- worker не зависит от порядка или полноты `tag_map.yaml`;
- consultant может исключить один тег без изменения loader;
- неизвестный tag обнаруживается при загрузке, а не скрывается во время расчёта.

**Минусы:**

- список нужно обновлять при появлении нового судна/ревизии tag map;
- стартовый список не доказывает физическую пригодность каждого generic-labelled параметра; это явно закрывается review metadata и calibration follow-up.

### Вариант A2 — автоматический набор по `alarm` setpoint

Loader выбирает все аналоговые теги, имеющие аварийную уставку и поддержанный unit.

**Плюсы:** почти нулевая ручная поддержка; новые alarm-bearing tags подхватываются автоматически.

**Минусы:** текущий Makarov map даёт 320 температурных тегов, что выходит за целевой размер worker; изменение tag map незаметно меняет B13 surface; replay может перестать быть сопоставимым; нельзя отличить консультантски утверждённый тег от технического placeholder.

**Решение:** не использовать как v1 production mode. Допустим только как offline audit-команда, которая печатает кандидатов и проверяет полноту allowlist.

### Вариант A3 — семейства/regex (`TAI42xx`, `SKT*`)

Состав задаётся префиксами и диапазонами, например `TAI42*` + `SKT002`.

**Плюсы:** короткий YAML; удобно для массового расширения.

**Минусы:** диапазон не является доменным подтверждением; generic `TAI` naming не кодирует физическую роль; добавление тега происходит неявно; риск подписать новый сигнал без настройки setpoint/source.

**Решение:** не использовать для разрешения worker. Семейства могут быть только инструментом lint/report, но не runtime selection.

### Рекомендация A

Использовать A1: явный allowlist из 53 тегов с обязательными полями `tag_id`, `setpoint_source`, `mode_filter` и проверкой соответствия `tag_map`. `SKT001` — единственный обязательный v1 `rpm_tag`; он не является warning target и используется только для mode filter. Все остальные `SKT* rpm` не подписываются без отдельного CR.

Список является baseline для Makarov v1, а не универсальной отраслевой классификацией. Поле `review_status: reviewed|provisional` позволяет выпустить ship-pack с прозрачным provisional статусом без silent promotion в production.

---

## Компонент B — форма warnings.yaml и ownership полей

### Вариант B1 — плоский список defaults + per-tag override (рекомендуемый)

```yaml
version: "1"
defaults:
  threshold_pct: 0.90
  ewma_window_hours: 24
  min_trend_len_hours: 6
  r2_min: 0.60
  hysteresis_pct: 0.02
  startup_guard_sec: 300
  mode_filter:
    rpm_tag: SKT001
    rpm_min: 10

tags:
  - tag_id: TAI4101
    setpoint_source: aps
    threshold_pct: 0.88
    ewma_window_hours: 48
    mode_filter:
      rpm_tag: SKT001
      rpm_min: 10
    review_status: reviewed
    note: bearing temperature GD1 DE
  - tag_id: SKT4102
    setpoint_source: aps
    review_status: provisional
  - tag_id: SKT002
    setpoint_source: aps
    mode_filter:
      rpm_tag: SKT001
      rpm_min: 10
    review_status: provisional
```

> В примере выше `SKT4102` — намеренная иллюстрация формы, не часть allowlist; в реальном файле используется существующий `TAI4102`. Loader обязан проверять точное совпадение `tag_id` и не исправлять опечатки.

`setpoint_source` принимает только `aps` или `config`:

- `aps`: получить live alarm setpoint из B10 setpoints/tag map; отсутствие setpoint — `config_error`, warning не создаётся;
- `config`: требовать `setpoint_value` и `unit`; mismatch unit с tag map — `config_error`;
- нельзя молча переключать `aps` на `config` или наоборот.

**Плюсы:** локальный override, стабильный diff, простая схема; defaults не скрывают критические per-tag отличия.

**Минусы:** повторение `mode_filter` в отдельных тегах; при расширении могут появиться одинаковые значения.

### Вариант B2 — отдельные профили режима

```yaml
profiles:
  main_engine_temperature:
    threshold_pct: 0.90
    mode_filter: {rpm_tag: SKT001, rpm_min: 10}
tags:
  - {tag_id: TAI4101, profile: main_engine_temperature}
```

**Плюсы:** меньше дублирования; централизованная калибровка.

**Минусы:** появляется registry/profile indirection до появления реальной третьей группы; сложнее объяснить effective config в API и replay.

**Решение:** отложить до третьего подтверждённого профиля; сейчас B1 даёт лучшую locality.

### Вариант B3 — конфигурация полностью в tag_map.yaml

**Плюсы:** один источник описания тега.

**Минусы:** operational warning policy смешивается с базовым каталогом APS; tag map уже используется другими consumers; изменение threshold ради B13 меняет общий контракт; труднее вести версию warning policy.

**Решение:** не использовать. `tag_map.yaml` — источник identity/unit/range/setpoints; `warnings.yaml` — источник B13 subscription/policy.

---

## Компонент C — режимный фильтр и startup guard

### Вариант C1 — rpm threshold + transition timestamp (рекомендуемый)

Для каждого warning target хранить состояние последнего rpm sample и `rpm_transition_at`. Warning calculation подавляется, если:

1. rpm sample отсутствует, имеет плохое quality или старше `mode_stale_after_sec`;
2. `rpm < rpm_min`;
3. `now - rpm_transition_at < startup_guard_sec` после перехода через `rpm_min`.

При подавлении не записывать активный warning. Для history/API сохранять typed `suppressed_reason` только если существует рассчитанный candidate и это необходимо для audit; отсутствие данных не превращать в нулевое значение.

**Плюсы:** подавляет стартовый разгон и останов; transition определяется из samples; не требует отдельного ручного state API.

**Минусы:** качество фильтра зависит от rpm sample; при плохом rpm warning безопасно не выдаётся.

### Вариант C2 — только `rpm < rpm_min`

**Плюсы:** минимальный state; простая реализация.

**Минусы:** после перехода в рабочий режим EWMA может содержать стартовый transient; ложное enter остаётся возможным.

**Решение:** недостаточно для B13-F8 и S13.2.

### Вариант C3 — ручной vessel mode из B10

**Плюсы:** режим «ход/стоянка» может быть виден оператору; не нужен rpm parser.

**Минусы:** ручной или задержавшийся mode сам является источником расхождения; worker теряет локальный физический signal; отдельный API/ACL не входит в s06.

**Решение:** использовать позднее как дополнительный suppressor, но не как единственный v1 gate.

### Рекомендация C

C1 с fail-closed semantics. Для всего baseline использовать `SKT001`, `rpm_min: 10`, `startup_guard_sec: 300`; per-tag override допустим, если отдельный сигнал имеет другой физический режим. `SKT001` валидируется как `unit: rpm`, `signal_type: analog`, `source_id: skt_geu`, range с верхней границей не менее `rpm_min`.

---

## Компонент D — setpoint и единицы

### Вариант D1 — APS-first, config override только явно (рекомендуемый)

- `aps` читает alarm setpoint из live setpoints/ship-pack;
- `config` требует `setpoint_value` и `unit`;
- `setpoint_source` и effective setpoint сохраняются в calculation provenance;
- изменение setpoint не переписывает историю, новая calculation получает новый source/value.

### Вариант D2 — всегда snapshot из warnings.yaml

**Плюсы:** replay полностью самодостаточен.

**Минусы:** риск drift относительно APS; operator видит не ту уставку; конфликт с B13-F2 и setpoint API.

**Решение:** не использовать для `aps` tags.

### Вариант D3 — всегда live APS без config path

**Плюсы:** единый authoritative source.

**Минусы:** невозможно покрыть tags без опубликованной setpoint; replay старой истории зависит от текущего APS snapshot.

**Решение:** оставить explicit `config` для approved exceptions, но не делать fallback implicit.

---

## Компонент E — EWMA, тренд и ETA

### Вариант E1 — continuous-time EWMA + regression window (рекомендуемый)

Использовать канон плана:

```text
alpha = 1 - exp(-dt / tau)
S_i = alpha * x_i + (1 - alpha) * S_prev
```

`dt` берётся из timestamp samples, отрицательный timestamp отвергается, `dt == 0` не двигает состояние. `tau` — `ewma_window_hours * 3600`, а не количество samples.

На retained window `[now - ewma_window, now]` вычислять slope EWMA по времени линейной регрессией. ETA выдавать только при `len >= min_trend_len`, достаточном `R²` или monotonic-rise policy, положительном slope и `ewma < setpoint`.

**Плюсы:** воспроизводимость при неравномерной телеметрии; явные единицы; ETA не путается со скоростью raw sample.

**Минусы:** больше arithmetic state, чем у fixed-N EWMA.

### Вариант E2 — fixed-N discrete EWMA

**Плюсы:** короткая формула.

**Минусы:** скорость collector меняет фактическое окно; replay с пропусками не bit-exact по времени; противоречит предпочтению time window в B13-F3.

**Решение:** запрещён для production, разрешён только для сравнения в unit test.

### Вариант E3 — raw linear regression без EWMA

**Плюсы:** минимальный state.

**Минусы:** transient/noise сразу попадает в slope; нарушает B13-F3; startup guard не компенсирует все выбросы.

**Решение:** не использовать.

### ETA и hysteresis invariants

- `eta_to_setpoint_days is None`, если slope `<= 0`, `ewma >= setpoint`, недостаточно точек или trend unstable;
- warning enter: `ewma >= setpoint * threshold_pct`;
- warning exit: `ewma < setpoint * (threshold_pct - hysteresis_pct)`;
- между enter и exit состояние не меняется;
- quality gap не превращается в sample с нулём;
- active warning содержит effective setpoint/threshold и `since`, history фиксирует enter/exit transition.

---

## Компонент F — worker subscription и performance

### Вариант F1 — immutable selected-tag snapshot на старте/изменении config (рекомендуемый)

Loader один раз валидирует YAML и строит immutable tuple выбранных тегов. Worker tick итерирует только этот tuple (53 baseline tags); полный `tag_map` не перечитывается. Новый config создаёт новый snapshot атомарно после успешной валидации.

**Плюсы:** O(selected tags) на tick, понятный bound 50–120, безопасная публикация новой версии.

**Минусы:** изменение YAML требует reload/restart или явно существующего config reload hook.

### Вариант F2 — полный scan tag_map на каждом tick

**Решение:** запрещён. O(586) сейчас и неограниченный рост позже; runtime selection становится недетерминированным.

### Вариант F3 — одна asyncio task на тег

**Плюсы:** независимый cancellation.

**Минусы:** до 120 tasks и лишний scheduling overhead для общей cadence; сложнее persistence transaction.

**Решение:** один bounded worker tick с batch reads, `asyncio.gather` только для независимых I/O chunks и `return_exceptions=True`; один ошибочный tag не ломает остальные, но unhealthy source виден в metrics/logs.

---

## Итоговый v1 контракт warnings.yaml

```yaml
version: "1"
defaults:
  threshold_pct: 0.90
  ewma_window_hours: 24
  min_trend_len_hours: 6
  r2_min: 0.60
  hysteresis_pct: 0.02
  startup_guard_sec: 300
  mode_filter:
    rpm_tag: SKT001
    rpm_min: 10

tags:
  - tag_id: TAI4101
    setpoint_source: aps
    threshold_pct: 0.88
    ewma_window_hours: 48
    review_status: reviewed
  - tag_id: TAI4102
    setpoint_source: aps
    review_status: reviewed
  - tag_id: TAI4202
    setpoint_source: aps
    review_status: provisional
  # ... остальные baseline tags из явного списка CR-P2-08 ...
  - tag_id: SKT002
    setpoint_source: aps
    review_status: provisional
```

Обязательные loader validations:

1. `version == "1"`;
2. `tags` непустой и содержит от 1 до 120 элементов; для Makarov baseline ожидается 53;
3. `tag_id` уникален и существует в `tag_map`;
4. target — `signal_type: analog`, не `alarm_bit`;
5. unit числовой и согласован с setpoint;
6. `setpoint_source: aps` требует alarm setpoint в source;
7. `setpoint_source: config` требует конечный `setpoint_value > 0` и `unit`;
8. `threshold_pct` в `(0, 1)`; `hysteresis_pct` в `[0, threshold_pct)`;
9. `ewma_window_hours > 0`, `min_trend_len_hours > 0`, `r2_min` в `[0, 1]`;
10. `rpm_tag` существует, имеет `unit: rpm`, `signal_type: analog`, а `rpm_min >= 0`;
11. duplicate `tag_id`, unknown fields для критичных policy keys и невалидные types — hard config error;
12. нет runtime fallback на auto-discovery или config setpoint при ошибке.

`review_status: provisional` прозрачно отражается в config validation/report metadata; provisional не означает suppress. Если policy требует запрета provisional в production, это отдельный deployment gate, а не молчаливое удаление тега.

---

## Persistence и API seam

s06 сохраняет active/history через порт persistence. SQLAlchemy models и migration не импортируются в EWMA math. Минимальный active record содержит `tag_id`, effective setpoint/source, current/raw/ewma values, threshold, slope/ETA, quality, `since`, config version и `suppressed_reason` при наличии.

s07 получает уже typed `DriftWarning` и не пересчитывает EWMA. REST filters (`active`, `tag_id`, `asset_id`, `since`) и WS enter/exit используют те же поля; effective config provenance остаётся доступным для audit, но внутренний loader object наружу не выдаётся.

При смене config version:

- старый active warning завершается событием `config_changed`, если tag удалён или policy стала incompatible;
- history не переписывается;
- новая версия начинает собственную calculation state;
- API может отфильтровать history по `config_version`.

---

## Property-based и scenario verification

### Pure selection properties

- любой неизвестный tag отклоняется, а не включается;
- список после validation уникален и имеет размер `1..120`;
- любой выбранный target — analog и имеет совместимый setpoint;
- `config` без value/unit никогда не создаёт warning;
- `aps` без live setpoint никогда не падает в config fallback;
- повторная загрузка одинакового YAML даёт идентичный immutable snapshot;
- порядок строк YAML не влияет на effective selection, но canonical serialization стабилизирует replay.

### Mode properties

- плохое/просроченное rpm quality не разрешает warning;
- `rpm < rpm_min` suppresses candidate;
- переход через rpm threshold запускает guard ровно один раз;
- чтение во время guard не продлевает guard timestamp;
- останов после active warning создаёт exit/suppressed transition по policy, но не ложный новый enter.

### Math properties

- при одинаковом `x` EWMA остаётся `x` после первого seed;
- `0 <= alpha <= 1` для `dt >= 0`, `tau > 0`;
- рост timestamps с одинаковым input воспроизводим bit-exact;
- неравномерные intervals используют elapsed seconds, а не sample count;
- non-positive slope даёт `eta=None`;
- hysteresis не меняет state внутри deadband;
- плохой sample не заменяется нулём.

### Required scenarios

1. 53-tag baseline loads and only configured tags reach worker.
2. `TAI4101` approaches APS alarm 85°C while `SKT001 >= 10`: enter after threshold and stable trend.
3. Startup jumps from 0 to 250 rpm: no warning during 300-second guard.
4. Shutdown to 0 rpm: candidate suppressed; no new warning.
5. `SKT002` APS setpoint is low-side oil pressure; policy documents direction as explicit `toward_setpoint`/`comparison` metadata before enabling it. If direction is not implemented in s06, `SKT002` remains provisional and disabled by production validation.
6. Historical replay uses fixed timestamps and config version and produces identical EWMA/slope/ETA.
7. Unknown `TAI9999` in warnings.yaml fails loader before worker start.
8. No import/string audit finds `sklearn`, `torch`, ML training terminology, `AI` or `ИИ` in B13 runtime/API payloads.

**Important direction decision:** temperature tags are high-side (`value` rises toward alarm); `SKT002` has a low-side alarm semantics (`value` falls toward alarm). Therefore `comparison: high`/`comparison: low` is required in the schema before treating pressure as equivalent. Until implemented and tested, `SKT002` is retained in the reviewed candidate list but marked `provisional` and excluded from the production active snapshot. This prevents a high-side-only formula from producing a mathematically plausible but semantically wrong pressure warning.

---

## Реализационное руководство для s06

1. Создать `warnings.yaml` с explicit baseline list, `comparison: high` для temperature tags и `comparison: low` для `SKT002` только после поддержки low-side path.
2. Реализовать typed config loader/validator; не исправлять неизвестные tag IDs и не делать implicit discovery.
3. Реализовать pure `ewma_update`, slope/ETA и hysteresis state machine по E1.
4. Сначала включить temperature baseline; для provisional/unsupported direction использовать deterministic config error, а не silent suppress.
5. Подключить mode filter через `SKT001`, quality/staleness и non-extending startup guard.
6. Worker читает selected snapshot, cadence 60 s, batch I/O; persistence — через порт.
7. Добавить replay fixture, property/scenario tests и static denylist no-ML test.
8. После s06 передать s07 стабильный `DriftWarning` и transition event contract; API не должен повторять selection/math logic.

## Реализационное руководство для s07

1. REST/WS публикуют только active/history records из s06 persistence/service.
2. Поля REST и WS совпадают для warning payload; enter/exit transition явно различаются.
3. `suppressed_reason`, `quality`, `comparison`, `setpoint_source` и `config_version` не теряются на transport seam.
4. Watch `drifts[]` использует active warnings и не создаёт новый расчёт.
5. Audit test запрещает ML/AI strings и не допускает leakage внутреннего loader error stack в API.

---

## Verification checklist

- [x] Один epic-scoped creative-файл создан.
- [x] Core skills и 5 situational skills перечислены.
- [x] CR-P2-08 классифицирован как Architecture + Algorithm.
- [x] Для selection, config, mode, setpoint, math и worker предложены минимум 2 варианта.
- [x] Выбран explicit allowlist; автоматическое discovery оставлено только offline audit.
- [x] Зафиксирован размер Makarov baseline и bound 1–120; production snapshot отделён от candidate list.
- [x] Учтена low-side семантика `SKT002`; high-side formula не применяется вслепую.
- [x] Зафиксированы fail-closed правила, property-based invariants и replay scenarios.
- [x] s06 и s07 получают один typed contract без дублирования domain logic.
- [x] Нет ML-пути и пользовательских строк «AI»/«ИИ» в B13 contract.
- [x] Зависимые decompose-файлы и index rewired на этот artifact.

## Следующая команда

**BACK IMPLEMENT @s06** — реализовать engine/loader/math/worker по закрытому CR-P2-08; после s06 — `BACK IMPLEMENT @s07`.
