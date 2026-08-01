# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-07 Report forms

**Creative ID:** CR-P2-07  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [decompose-v1-p2-ship/index.md](../../plan/decompose-v1-p2-ship/index.md)  
**Step:** [s04-b12-templates.yaml](../../plan/decompose-v1-p2-ship/s04-b12-templates.yaml)  
**Дата:** 2026-07-31  
**Режим:** BACK CREATIVE  
**Уровень:** L3/L4  
**Статус:** closed

## Skills gate

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/architecture-patterns/SKILL.md`
- `.agents/skills/improve-codebase-architecture/SKILL.md`
- `.agents/skills/python-design-patterns/SKILL.md`
- `.agents/skills/grill-me/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture` — зафиксировать глубокий seam между расчётом B12, подготовкой контекста и печатным ship-pack без декоративного orchestration layer.
- `python-design-patterns` — выбрать KISS/SRP-диспетчеризацию фиксированных четырёх типов вместо преждевременного generic plugin framework.
- `grill-me` — Q5 остаётся внешней неопределённостью; решение должно сделать waiver явным и ограниченным, а не притворяться согласованной регистровой формой.

---

## Решение batch

B12 разделяется на три последовательных ответственности:

1. **Calculation / preparation** — s02–s03 и будущие расчётные use-case'ы создают typed report context: формулы, агрегаты, quality/provenance и уже схлопнутые тревоги.
2. **Template rendering seam** — `TemplateRenderer` принимает только `report_type`, `template_version` и один immutable context dict; возвращает `body_json` и `body_html`, построенные из одного и того же контекста.
3. **Ship-pack presentation** — Jinja-файлы и `schema.json` задают только layout/labels/print CSS. Формулы, SQL, debounce и policy в шаблоны не попадают.

Это сохраняет additive contract `report_runs`, `body_json`, `body_html`, `provenance`, не меняет URL фазы 1 и не добавляет универсальный registry/event bus.

---

## 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

### Компонент A — единый renderer и структура ship-pack

**Требования и ограничения:**

- Четыре известных типа: `watch`, `daily_noon`, `fuel`, `register`.
- Версия шаблона должна быть адресуемой (`v1`) и храниться в отчёте вместе с `formulas_version`.
- `body_json` и `body_html` обязаны описывать один snapshot данных.
- Существующий `ReportEngine` уже создаёт `report_runs`; s04 добавляет rendering seam, а не второй engine.
- Нельзя переносить расчётные semantics в Jinja или SQL.

#### Вариант 1 — фиксированная таблица типов и тонкий `TemplateRenderer` (рекомендуется)

```text
Report context
    ↓
TemplateRenderer.render_report(type, context)
    ├─ canonical body_json = context snapshot
    └─ Jinja template(type, version, context) = body_html
```

Диспетчеризация — обычная typed mapping для четырёх типов. Для каждого типа отдельная папка `v1/`, рядом `schema.json` там, где форма имеет публичный JSON contract. Ошибка неизвестного типа/версии — typed failure, не fallback на watch.

**Плюсы:** минимальная глубина, простой import graph, легко проверить отсутствие расхождения JSON/HTML, версия layout видна в пути.  
**Минусы:** при добавлении пятого типа нужно дописать mapping и тест; это намеренная цена явного additive change.

#### Вариант 2 — generic template plugin registry

Каждый тип регистрирует plugin с loader, schema validator, context builder и HTML renderer; engine ищет plugin по имени.

**Плюсы:** формально расширяемо, можно подключать внешние формы.  
**Минусы:** преждевременная абстракция для четырёх стабильных типов, больше failure paths и скрытая регистрация, сложнее доказать deterministic T9; нарушает правило не добавлять generic plugin framework.

#### Вариант 3 — отдельный renderer-класс на каждый тип

`WatchRenderer`, `DailyNoonRenderer`, `FuelRenderer`, `RegisterRenderer` реализуют общий Protocol.

**Плюсы:** локальная тестируемость и независимые layouts.  
**Минусы:** четыре почти одинаковых класса до появления различающихся policies; создаёт ложный слой, если классы только вызывают Jinja.

### Рекомендуемый подход

Выбрать **вариант 1**. Единственный seam — `TemplateRenderer`; mapping остаётся явным. Context builder может быть отдельной чистой функцией только там, где он действительно объединяет расчёты и provenance. Template renderer не импортирует SQLAlchemy/FastAPI.

**Канонический контракт:**

```text
render_report(report_type, context, template_version="v1")
    -> RenderedReport(body_json, body_html, template_version)
```

`body_json` — сериализуемая копия контекста с удалёнными только внутренними объектами дат/enum через один canonical serializer. `body_html` рендерится тем же логическим snapshot; HTML escape включён по умолчанию. В `report_runs` сохраняются оба тела и provenance.

**Руководство по реализации:**

- Создать `ship-pack/makarov/report_templates/{watch,daily_noon,fuel,register}/v1/`.
- Общий `ship-pack/makarov/report_templates/_provenance.html.j2` включать в каждый HTML template.
- `schema.json` минимум обязателен для watch; для остальных типов схема должна быть рядом с template, если body contract не совпадает с общей базовой схемой.
- Стабильный порядок полей и списков — часть canonical JSON, чтобы SHA256 T9 не зависел от dict insertion order.
- `ReportEngine` получает prepared context и сохраняет renderer output в существующий `ReportRun`; immutable/version semantics не меняются.

**Верификация:**

- Один fixture context даёт один canonical JSON и HTML с теми же значениями.
- Неизвестный `report_type` и отсутствующий `vN` завершаются typed error.
- В HTML каждого типа присутствует provenance partial.
- Изменение layout версии не меняет `formulas_version` и не перезаписывает старый run.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## 🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm

### Компонент B — watch alarm debounce/collapse

**Требования и ограничения:**

- Схлопывание только для watch list.
- Ключ группы: `(event_name, asset_id)`.
- Окно берётся из versioned formulas/config, не зашивается в Jinja.
- Повторные тревоги должны оставаться traceable: одна строка с count и границами группы, а не потеря событий.
- Сортировка должна быть детерминированной для T9.

#### Вариант 1 — anchor-window grouping (рекомендуется)

Сначала сортировать события по `(official_ts, event_name, asset_id, event_id)`. Для каждой пары `(event_name, asset_id)` первая запись становится anchor; последующие записи попадают в группу, пока `official_ts < anchor_ts + debounce_window_sec`. Запись на точной правой границе начинает новую группу. Результат хранит `count`, `first_ts`, `last_ts`, severity по deterministic worst-of rule и список/идентификатор исходных событий.

**Плюсы:** независим от порядка входного SQL, окно однозначно, не допускает бесконечного chain-collapse.  
**Минусы:** событие после anchor+window не продлевает уже открытую группу.

#### Вариант 2 — rolling-window grouping

Каждая запись сравнивается с предыдущей записью той же пары; пока gap меньше окна, группа продолжается и окно фактически продлевается.

**Плюсы:** хорошо подавляет плотный дребезг.  
**Минусы:** длинный поток событий может схлопнуться в одну строку на часы, результат зависит от плотности данных и хуже объясняется в print report.

#### Вариант 3 — count-only aggregation

Сгруппировать по ключу и периоду, отдать только `×N` без временных границ и source ids.

**Плюсы:** самый короткий payload.  
**Минусы:** теряется provenance и auditability; невозможно отличить реальное длительное состояние от повторных импульсов.

### Рекомендуемый подход

Выбрать **вариант 1**. Debounce — чистая подготовительная функция до Jinja. Для `count == 1` сохранять обычную строку; для `count > 1` отображать `×N`, `first_ts–last_ts` и severity. Не смешивать разные `event_name` или `asset_id`, даже если timestamps совпадают.

**Руководство по реализации:**

- Конфигурация содержит `debounce_window_sec`; отсутствие конфигурации — typed configuration error, не silent default.
- `asset_id = null` является отдельным ключом и не смешивается с любым asset.
- Severity aggregation: `critical > alarm > warning > info`; при равной severity брать первый event как label, но сохранять count и границы.
- Исходные ids или compact `source_event_ids` сохраняются в structured body/provenance, если они доступны; presentation может показывать только count.
- Empty alarms — `[]`, не `null`; gap/stale не превращаются в alarm.

**Верификация:**

- Одинаковый набор событий в любом входном порядке даёт байт-стабильный canonical JSON.
- События на левой границе входят, на правой — образуют новую группу.
- Два разных asset с одним `event_name` не схлопываются.
- Повторный запуск debounce идемпотентен только на raw events; уже collapsed rows не подаются обратно как raw input.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## 🎨🎨🎨 ENTERING CREATIVE PHASE: UI-UX

### Компонент C — четыре печатные формы и общий provenance

**Требования и ограничения:**

- Watch: `verdict`, `protections[]`, `alarms_collapsed[]`, `drifts[]`, `period`, `watchkeeper`.
- Daily noon: судовые сутки `[prev_noon, noon)` по B7 timezone, `fuel_total`, `motohours_by_asset[]`, `avg_peak[]`.
- Fuel: `by_bunker`, `by_engine`, method A/B, `corrections[]`; метод и ограничения должны быть видны пользователю.
- Register: зависит от Q5; нельзя показывать несогласованный официальный бланк.
- Любая форма должна показывать provenance: quarantine, stale intervals, gaps, official timestamp rule; preliminary status не должен выглядеть как final.

#### Вариант 1 — общий print frame + специфичные sections (рекомендуется)

Каждый template использует одинаковый frame: title, period, status banner, body sections, `_provenance.html.j2`, footer с `formulas_version`/`template_version`. Специфичные sections различаются только содержимым.

**Плюсы:** одинаковая читаемость на борту и одинаковое место для доверительных ограничений; partial гарантирует отсутствие формы без provenance.  
**Минусы:** нужно дисциплинированно не перегружать общий frame типовыми полями.

#### Вариант 2 — полностью независимые формы

Каждая форма имеет собственный header/footer/provenance markup.

**Плюсы:** максимальная свобода для будущего заказчика.  
**Минусы:** drift layout, повторение ошибок и риск забыть provenance; T9/print smoke сложнее поддерживать.

#### Вариант 3 — единый generic table для всех типов

Один HTML layout, который динамически выводит поля контекста.

**Плюсы:** минимум файлов.  
**Минусы:** теряется смысловая иерархия watch/daily/fuel; пустые поля начинают выглядеть как нули или ложные значения; непригодно для register waiver.

### Рекомендуемый подход

Выбрать **вариант 1**. Общий frame — presentation-only; никакой логики «если gap, то zero». Значения с отсутствием данных отображаются как `—`/`unknown` с пояснением в provenance. `preliminary` получает заметный текстовый banner и не используется как финальная подпись.

**Руководство по реализации:**

- `watch/v1/template.html.j2`: verdict/protections/alarms/drifts и compact provenance.
- `daily_noon/v1/template.html.j2`: noon boundary, fuel/motohours/avg-peak; отдельно показывать gap в периоде.
- `fuel/v1/template.html.j2`: method, source tags, bunkers/engines, corrections и quality limitations.
- `_provenance.html.j2`: единый block с `status`, `formulas_version`, `template_version`, `data_watermark`, `official_ts_rule`, `quarantined_tags`, `stale_intervals`, `gaps`, `clock_adjustment_in_period`, `reconstruction_note` и anomaly flags при наличии.
- HTML не содержит неподтверждённых слов «официальный»/«принят» для preliminary или waived data.

**Верификация:**

- Snapshot smoke для всех трёх обязательных форм проверяет title, period, status и provenance.
- HTML escape тестируется на `watchkeeper`, asset и event labels.
- Поля missing/gap визуально различимы от числового нуля.
- Print CSS остаётся минимальным и не претендует на FRONT pixel-perfect acceptance.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture

### Компонент D — Q5 register waiver и граница официальной формы

**Требования и ограничения:**

- Q5 не имеет согласованного layout.
- Product AC допускает `register` «по Q5 или waiver документирован».
- Нельзя silently omit template или выпускать несогласованный документ под видом регистра.
- Остальные watch/daily/fuel не должны зависеть от Q5.

#### Вариант 1 — waiver-first conditional artifact (рекомендуется)

Создать `register/v1/` как conditional package с `schema.json` и template. Context обязан иметь `register_scope`:

```json
{
  "status": "approved|waived",
  "waiver_id": "Q5-...",
  "reason": "layout not signed off",
  "owner": "...",
  "expires_at": "..."
}
```

При `approved` renderer выводит только согласованные поля из Q5 contract. При `waived` renderer не имитирует официальный бланк: выдаёт structured exclusion/waiver block с alarms extract/daily logs только как working appendix, с явным статусом `waived` и ответственным за закрытие.

**Плюсы:** AC выполняется честно, provenance сохраняется, watch/daily/fuel не блокируются, будущий Q5 layout может стать additive `v2`.  
**Минусы:** register output в v1 не является официальным регистром и требует документации waiver.

#### Вариант 2 — отложить весь register package

Не создавать `register/v1`, пока Q5 не подписан; закрыть только три формы.

**Плюсы:** нет риска неверного бланка.  
**Минусы:** decompose s04 и package contract остаются неполными, waiver невозможно проверить автоматически, а omission трудно отличить от забытых deliverables.

#### Вариант 3 — принять generic daily как register

Переиспользовать daily_noon template и назвать его register до sign-off.

**Плюсы:** быстро и без нового файла.  
**Минусы:** юридически и операционно опасно; разные boundary/fields/семантика, ложное соответствие Q5.

### Рекомендуемый подход

Выбрать **вариант 1** и зафиксировать текущий decision: **CR-P2-07 закрывает Q5 через документированный waiver, не через выдуманный layout**. Waiver — обязательное поле context/schema; отсутствие `waiver_id`, `reason`, `owner` или `expires_at` при `status=waived` — validation error. `approved` без versioned Q5 field contract также отвергается.

**Руководство по реализации:**

- `register/v1/schema.json` описывает оба статуса и required waiver metadata.
- `register/v1/template.html.j2` содержит явный `REGISTER WAIVED` banner при waiver.
- В `body_json` хранить status и waiver metadata; не записывать waiver только в HTML.
- В `provenance` добавить `form_status=waived` и ссылку на waiver id.
- После Q5 sign-off следующая creative/implementation работа добавляет approved field contract как новый template version или явно согласованный additive revision; v1 waiver не мутируется.

**Верификация:**

- `waived` без полного metadata не рендерится.
- `waived` HTML не содержит утверждения, что документ является подписанным регистром.
- `approved` требует явного Q5 schema/version.
- T9 фиксирует waiver metadata в canonical JSON, исключая только generated timestamps.

🎨🎨🎨 EXITING CREATIVE PHASE

---

## Общий контракт s04

### Context shape

```text
ReportContext
  report_type: watch | daily_noon | fuel | register
  template_version: v1
  period: {from, to, boundary_rule, vessel_timezone?}
  status: final | preliminary
  body: type-specific fields
  provenance: structured gaps/quarantine/stale/clock/reconstruction data
  formulas_version: v1...
```

`ReportContext` строится до рендера и не содержит ORM entities. Все datetime имеют timezone-aware ISO representation на serialization boundary. Внутренний порядок коллекций стабилизирован до `body_json`.

### Error policy

- Неизвестный тип, версия, отсутствующий required field или invalid Q5 waiver → typed validation error.
- Jinja template missing/invalid → typed renderer error с `report_type` и version; не fallback на другую форму.
- Data gap/stale/quarantine → valid report с provenance и `preliminary`/quality markings, если это определено engine; не exception и не zero.
- Renderer не выполняет retry, SQL или внешние вызовы.

### Implementation sequence

1. Добавить template tree и `_provenance` partial.
2. Зафиксировать JSON schemas и validation fixtures для watch/daily/fuel/register waiver.
3. Реализовать pure debounce preparation и renderer mapping.
4. Подключить output к `ReportEngine`/`report_runs` так, чтобы один context давал оба тела.
5. Добавить targeted tests: provenance, same-context JSON+HTML, debounce ×N, Q5 waiver/approved validation, HTML escaping.
6. Сохранить generated timestamps отдельно от canonical fixture hash для T9.

## Acceptance / verification checklist

- [ ] watch, daily_noon и fuel имеют versioned Jinja template и deterministic JSON body.
- [ ] register package существует в conditional waiver-first режиме; Q5 не замаскирован.
- [ ] Каждый HTML включает `_provenance.html.j2`.
- [ ] Debounce использует `(event_name, asset_id)` и anchor half-open window.
- [ ] `body_json` и `body_html` получены из одного context snapshot.
- [ ] `ReportRun` остаётся append-only; старый version не изменяется при пересчёте.
- [ ] Отсутствующие данные видны как gap/unknown/preliminary, не как zero/success.
- [ ] T9 fixtures могут сравнивать canonical JSON SHA256 без `generated_at`.

## Итоговое решение

CR-P2-07 закрыт как **Architecture + Algorithm + UI-UX** decision batch:

- фиксированный `TemplateRenderer` вместо generic plugin framework;
- anchor-window deterministic debounce до rendering;
- общий print frame и обязательный provenance partial;
- register v1 — conditional и waiver-first до Q5 sign-off.

**Следующий режим:** `BACK IMPLEMENT` @s04.
