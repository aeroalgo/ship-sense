# CR-UI-04 — Screen 6 compression UX (DS0-3)

**Тип:** Architecture + Algorithm + UI-UX  
**Задача:** T-004 / plan `plan-v1-p1-screens.md` §3.3 DS0-3, §5.4, §6, §10 CR-UI-04  
**Decompose:** [s13-screen-watch.md](../../plan/decompose-v1-p1-screens/s13-screen-watch.md)  
**Deps tokens:** [CR-UI-01-tokens.md](CR-UI-01-tokens.md)  
**Deps lamps:** [CR-UI-03-alarm-grammar.md](CR-UI-03-alarm-grammar.md) (Lamp в rows)  
**Дата:** 2026-07-26  
**Статус:** closed (creative) — IMPLEMENT s13 собирает `WatchPage` + `debounce.ts` + print

---

## 0. Design Read

Reading this as: **ship-bridge HMI watch handover brief (ISA-101 compressed summary)** for вахтенный механик at 2–3 m — one glance «что было без меня»; industrial console language, not SaaS digest cards, not notification feed.

**Dial overrides (HMI):** VARIANCE 2 · MOTION 1–2 · DENSITY 9 (cockpit report).

**Skills applied:** `frontend-design` (subject = вахтенный brief / paper log under glass), `design-taste-frontend` (regulated/cockpit; marketing out), `emil-design-eng` (no list entrance anim; expand ≤200 ms), `impeccable` product register (contrast, reduced-motion, no nested cards), `high-end-visual-design` — **trimmed**: signature = verdict strip + never-collapse protections, not glass/bento, `ui-ux-pro-max` (touch ≥44, hierarchy), `frontend-patterns` (pure lib + thin feature), `brainstorming` (A/B/C below).

---

## 1. Проблема и scope

### 1.1 Вопрос плана

> Client vs server debounce; verdict copy templates.  
> AC: Formal debounce params; user test script for Ф2.5.

### 1.2 Alias плана

`DS0-3-watch-compression.md` → канон = этот файл (`CR-UI-04-…`), как CR-UI-01/03.

### 1.3 Deliverables этого CREATIVE

| # | Путь | Статус |
|---|------|--------|
| 1 | `memory-bank/front/creative/v1-p1-screens/CR-UI-04-watch-compression.md` (этот файл) | done |
| 2 | `frontend/src/lib/watch/watch-compression-spec.ts` | done |

### 1.4 Out of scope

| Не делаем здесь | Куда |
|-----------------|------|
| React `WatchPage` / hooks / Vitest / PW-05 | FRONT IMPLEMENT s13 (+ s16 PW) |
| Handoff CTA wiring 6→5/1 polish | FRONT IMPLEMENT s14 (copy/href канон здесь) |
| Persisted B12 watch runs / server grouping | BACK T-005 / p2 |
| AC-6-06 три механика на живых данных | T-006 / Ф2.5 (скрипт ниже — протокол) |
| Дрейфы B13 real | stub copy; p2 |
| Финальный type scale постов | CR-UI-05 / Q9 |

### 1.5 Блокер Ф2.5 (не abort CREATIVE)

- Ф2.5 **не** блокирует старт s13 на MSW/эмуляторе.
- Ф2.5 **блокирует** финальную приёмку G-DS0-3-03 / AC-6-06.
- Прототип UI + unit debounce — на fixture; скрипт §8 — для живых данных позже.

---

## 2. Architecture — где debounce (3 варианта)

### Вариант A — Только server collapse

API `GET /api/reports/watch` отдаёт уже сгруппированные `highlights[]` / sections; UI только рендерит.

**Плюсы:** print HTML ≡ screen; один источник правды.  
**Минусы:** p1 stub `highlights: []` (BACK plan §6.8); s13 блокируется BACK; нельзя TDD collapse без API.

### Вариант B — Только client collapse (рекомендуется для p1)

Чистая функция `collapseDebounceGroups` на flat events (из `highlights` если появятся, иначе companion `GET /api/events?from&to` / fixture). Print JSON path проходит ту же функцию; HTML print — либо client PrintLayout, либо server позже подтянет те же params.

**Плюсы:** разблокирует s13 сейчас; params в `watch-compression-spec.ts`; AC-6-03 тестируем unit; совпадает с decompose «client-side if API flat list».  
**Минусы:** расхождение с server HTML, пока BACK не использует те же числа — **mitigation:** константы экспортированы; BACK p2 импортирует/копирует числа из спеки (G-DS0-3-01).

### Вариант C — Hybrid feature-detect

Если `highlights` pre-grouped → render as-is; иначе client collapse.

**Плюсы:** forward-compat p2.  
**Минусы:** две ветки + drift risk; для p1 `highlights` пуст → всегда client path. Усложнение без выгоды сейчас.

### Recommendation

**Вариант B для фазы 1.**  
Контракт на будущее: когда BACK начнёт слать grouped highlights — s13 может перейти на C **без смены** `DEBOUNCE_*` констант. Protections **никогда** не проходят collapse (даже если server ошибётся — client guard `isProtectionEvent`).

**Зафиксировано:** `frontend/src/lib/watch/watch-compression-spec.ts`; s13 `features/watch/debounce.ts` — thin re-export / wrapper вокруг spec.

---

## 3. Algorithm — debounce (канон численный)

Код-контракт: `watch-compression-spec.ts`. Gate **G-DS0-3-01**.

| Параметр | Значение | Константа |
|----------|----------|-----------|
| Min count to collapse | **≥ 3** | `DEBOUNCE_MIN_COUNT` |
| Window | **5 минут** | `DEBOUNCE_WINDOW_MS = 300_000` |
| Group key | `event_name` + `asset_id` (null → `""`) | `debounceGroupKey()` |
| Cluster rule | consecutive events same key; `last.ts − first.ts ≤ window` from cluster start | sliding clusters sorted by `ts` ASC |
| Collapsed flag | `count >= DEBOUNCE_MIN_COUNT` | `DebounceGroup.collapsed` |
| Label | `… (×N дребезг)` | `formatDebounceLabel()` |

### 3.1 Что **запрещено** схлопывать

| Класс | Правило |
|-------|---------|
| Protections / shutdowns | `isProtectionEvent` → секция protections, **каждый** event отдельной строкой; `collapsed` всегда false / не вызывать collapse |
| Разные `asset_id` | разные ключи |
| Разные `event_name` | разные ключи |
| Разрыв > 5 мин | новый cluster (два ряда ×N если два «вспышки») |

### 3.2 `isProtectionEvent` (канон p1)

1. `params.kind === "protection"` ИЛИ `params.section === "protections"`  
2. ИЛИ `severity ∈ {critical, protection-shutdown}`  
3. ИЛИ `PROTECTION_NAME_RE` на `event_name` (`trip|shutdown|protection|overspeed|разнос|защита|…`)

Alarm section = всё остальное severity alarm/warning (info → journal only / не в watch alarms, если не в highlights).

### 3.3 Expand UX (не «потерять»)

- Collapsed row: first_ts (локаль HH:mm) + label + `(×N дребезг)` + control «развернуть».
- Expanded: список member_ids с полными ts; тот же порядок что journal.
- Print: collapsed form + footnote «N срабатываний; детали в журнале» **или** full expand в print — **канон print:** показать collapsed label **и** полный список ts в `<details open>` для paper (AC-6-03 + «не врёт»).

### 3.4 Сортировка секций

1. Protections — by `ts` ASC (хронология вахты).  
2. Alarms — collapsed groups by `first_ts` ASC.  
3. Drifts — stub last.

---

## 4. Verdict copy templates

Tone → `WatchVerdictTone`: `ok` | `attention` | `critical` (уже в DS `WatchVerdict`).

| Условие | text (RU) | tone |
|---------|-----------|------|
| 0 events / 0 alarms+protections | `За вахту событий не зафиксировано` | `ok` |
| alarms>0, protections=0 | `Были тревоги по {systems}; защит: 0` | `attention` |
| protections>0, alarms=0 | `Сработали защиты: {n}` | `critical` |
| both >0 | `Были тревоги по {systems}; защит: {n}` | `critical` |

`{systems}` = уникальные system labels из asset tree / event params; если пусто → `системам`.

### 4.1 Server vs client verdict

| Источник | Правило |
|----------|---------|
| `summary.verdict` non-empty | **использовать text** сервера (AC-6-01 предпочтение API) |
| tone | **всегда** из `buildVerdict(counts)` — сервер tone не шлёт |
| empty server verdict | полный `buildVerdict` |

`resolveVerdict({ serverVerdict, input })` в spec.

**AC-6-01:** если server text противоречит counts (например «защит: 0» при protections_count=1) — **не** молчать: s13 показывает banner «Вердикт API расходится со счётчиками» + client text secondary. (FAIL soft в proto; не silent wrong.)

---

## 5. UI-UX — layout (G-DS0-3-02)

### Вариант UI-A — Vertical brief strip (рекомендуется)

```
┌─ watch page ────────────────────────────────────────────────┐
│ [banner 60s] Пересменочный обзор                            │
│ WatchVerdict (border-left tone)                             │
├─────────────────────────────────────────────────────────────┤
│ WatchSection protections  collapsible=false  defaultOpen    │
│   • HH:mm — label (+ Lamp protection)                       │
├─────────────────────────────────────────────────────────────┤
│ WatchSection alarms       collapsible=true   defaultOpen    │
│   DebounceGroupRow × N                                      │
├─────────────────────────────────────────────────────────────┤
│ WatchSection drifts       stub copy                         │
├─────────────────────────────────────────────────────────────┤
│ DataQualityPanel (quarantine / stale / banner)              │
├─────────────────────────────────────────────────────────────┤
│ [Печать]  [К активным тревогам]  [Обзор судна]              │
└─────────────────────────────────────────────────────────────┘
```

**Signature:** verdict strip + protections always expanded (no chevron).  
**Tokens:** `--surface-1`, `--text-*`, `--alarm-*-fg`, `--panel-pad`, `--touch-min`.  
**Запрет:** card-in-card, pill clusters, emoji, purple glow, dashboard KPI strip.

### Вариант UI-B — Tabbed sections

Tabs Protections|Alarms|Drifts.  
**Минусы:** protections можно «не увидеть» без клика → **FAIL G-DS0-3-02 / AC-6-02**. Reject.

### Recommendation UI

**UI-A.** `WatchSection` protections: `collapsible={false}`. Alarms: `collapsible` OK, default open.

### Motion

- Expand debounce: height/opacity ≤200 ms `ease-out`; `prefers-reduced-motion` → instant.
- Нет stagger list entrance.
- Handoff banner: auto-hide `HANDOFF_BANNER_MS = 60_000` (plan §6.3).

### A11y

- Expand control: `aria-expanded`, min 44×44 (`--touch-min`).
- Verdict: `role="status"` (уже paragraph; s13 может добавить).
- Print: contrast tokens; lamps grayscale already CR-UI-03.

---

## 6. Data flow s13

```
useWatchReport(from,to)
  → GET /api/reports/watch?format=json
  → summary + data_quality + watchkeeper + period
  → events source:
       A) highlights[] if length>0 and shaped as events
       B) else GET /api/events?from&to&limit=… (same window)
  → split protections / alarms via isProtectionEvent
  → collapseDebounceGroups(alarms only)
  → resolveVerdict(server summary.verdict, counts)
  → PrintLayout: verdict + sections + data_quality + watchkeeper + period
```

Period bounds: session `started_at` → now, else last 8h (plan §5.4.4) — detail in s13.

---

## 7. Handoff CTA (G-DS0-3-04 pointer)

Канон href/copy (wire в s13; polish flow s14):

| Role | Label | href |
|------|-------|------|
| Primary | К активным тревогам | `/journal?severity=alarm&active=1` |
| Secondary | Обзор судна | `/overview` |
| Banner | Пересменочный обзор | 60 s |

Полный scenario «Пересменка» — plan §6.3 / s14.

---

## 8. User test script Ф2.5 (G-DS0-3-03 / AC-6-06 prep)

**Цель:** три механика — «не шумит, не врёт, ничего важного не потеряно».  
**Когда:** живые/эмулятор данные Ф2.5; до того — MSW fixture с 5× same alarm + 1 protection.

### Setup

1. Войти плиткой с `default_screen=6` (или открыть `/watch`).
2. Период = текущая вахта / fixture 08:00–16:00.
3. Подготовить в журнале: ≥3 одинаковых `event_name+asset_id` в ≤5 мин **alarm**; ≥1 protection/trip; опционально второй cluster через >5 мин.

### Скрипт

| # | Действие | Ожидание | Механика |
|---|----------|----------|----------|
| 1 | Открыть Watch | Verdict non-empty; tone ≠ ok если есть alarm/protection | — |
| 2 | Секция защит | Первая; **нет** chevron collapse; trip виден одной строкой на событие | **не потеряно** |
| 3 | Секция тревог | Дребезг = **одна** строка `(×N дребезг)`, N≥3 | **не шумит** |
| 4 | Развернуть группу | Список ts совпадает с journal filter того же окна/имени | **не врёт** |
| 5 | Print | data_quality + watchkeeper + period + protections + collapsed alarms с N | AC-6-04 |
| 6 | CTA «К активным» | → journal active alarms | handoff |
| 7 | (neg) 2 события за 5 мин | **не** collapse (N&lt;3) | порог |

**Pass Ф2.5:** механики 1–3 (строки 2–4) + print DQ. Formal AC-6-06 → T-006.

---

## 9. Implementation guide (s13)

1. Import constants/fns from `@/lib/watch/watch-compression-spec` (или re-export в `features/watch/debounce.ts`).
2. TDD red: `debounce.test.ts` — count≥3/window; protections not collapsed; verdict templates; cluster split &gt;5 min.
3. `DebounceGroupRow` — collapsed/expanded; `data-testid=debounce-group-row`.
4. `DataQualityPanel` — quarantine_tags, stale_intervals, banner; `watch-data-quality`.
5. Protections `WatchSection` `collapsible={false}`.
6. Drifts: single stub item `DRIFTS_STUB_COPY`.
7. PrintLayout children include DQ + watchkeeper.
8. PW-05 → s16 (не блокер s13 unit).

### Файлы (из decompose)

- `features/watch/WatchPage.tsx`
- `features/watch/useWatchReport.ts`
- `features/watch/DebounceGroupRow.tsx`
- `features/watch/DataQualityPanel.tsx`
- `features/watch/debounce.ts`
- `app/(authenticated)/watch/page.tsx`
- tests: `WatchPage.test.tsx`, `debounce.test.ts`

---

## 10. Gate checklist DS0-3 / CR-UI-04

| ID | Статус |
|----|--------|
| G-DS0-3-01 Formal debounce numbers | ✅ §3 + spec.ts |
| G-DS0-3-02 Wireframe hierarchy | ✅ §5 UI-A |
| G-DS0-3-03 Три механика live | ⏳ скрипт §8; приёмка Ф2.5 |
| G-DS0-3-04 Handoff 6→5/1 | ✅ §7 (+ s14) |
| CR-UI-04 AC Formal params | ✅ |
| CR-UI-04 AC User test script | ✅ §8 |

---

## 11. Rewire

| Шаг | Действие |
|-----|----------|
| s13 | `needs_creative: CR-UI-04 — **closed**`; Next → FRONT IMPLEMENT |
| index | CR-UI-04 ✅; s13 `yes (done)` / `pending` |

---

## Handoff

- **Done:** FRONT CREATIVE CR-UI-04 — client debounce канон (≥3 / 5 мин), verdict templates, UI-A hierarchy, Ф2.5 script; `watch-compression-spec.ts`
- **Files:** `memory-bank/front/creative/v1-p1-screens/CR-UI-04-watch-compression.md`; `frontend/src/lib/watch/watch-compression-spec.ts`
- **Next:** `FRONT IMPLEMENT` s13
- **Tool / model:** Cursor + fast-editing
- **New chat:** yes — one chat = one atomic subtask
- **code_changed:** yes (spec.ts only; graphify update)
