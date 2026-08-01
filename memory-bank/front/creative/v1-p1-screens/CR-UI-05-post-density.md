# CR-UI-05 — Density for posts (Q9 / DS0-2)

**Тип:** Architecture + Algorithm + UI-UX  
**Задача:** T-004 / plan `plan-v1-p1-screens.md` §2.3–2.4, §3.2 DS0-2, §10 CR-UI-05  
**Decompose:** [s02-tokens-themes.yaml](../../plan/decompose-v1-p1-screens/s02-tokens-themes.yaml) (soft), [s09-screen-overview.yaml](../../plan/decompose-v1-p1-screens/s09-screen-overview.yaml) (soft)  
**Deps tokens:** [CR-UI-01-tokens.md](CR-UI-01-tokens.md)  
**Дата:** 2026-07-27  
**Статус:** closed (creative) — Q9 field **waiver** + formula floor; photo evidence → после полевых замеров

---

## 0. Design Read

Reading this as: **ship-bridge HMI post physics (ISA-101)** for вахтенный at **worst post 2.5 m** on FHD 24" — readability and touch on качка, not marketing type scale, not responsive phone breakpoints.

**Dial overrides (HMI):** VARIANCE 1 · MOTION 1 · DENSITY 9 (cockpit floor, not airy gallery).

**Skills applied:** `frontend-design` (subject = console at distance), `design-taste-frontend` (regulated/cockpit), `emil-design-eng` (no decorative motion), `impeccable` product register (contrast, touch ≥15 mm, no nested cards), `high-end-visual-design` — **trimmed**: signature = AggregateShipStatus + Lamp silhouette at distance, not glass/bento, `ui-ux-pro-max` (touch/a11y floors), `frontend-patterns` (pure lib + CSS tokens), `brainstorming` (A/B/C below).

---

## 1. Проблема и scope

### 1.1 Вопрос плана

> Final type scale + OverviewGroupCard size per worst post.  
> Deps: DS0-2 / Q9.  
> AC: Readable at worst post 2.5 m measurement photo evidence.

### 1.2 Alias плана

`DS0-2-post-physics.md` → канон = этот файл (`CR-UI-05-post-density.md`), как CR-UI-01/03/04.

### 1.3 Deliverables этого CREATIVE

| # | Путь | Статус |
|---|------|--------|
| 1 | `memory-bank/front/creative/v1-p1-screens/CR-UI-05-post-density.md` (этот файл) | done |
| 2 | `frontend/src/lib/theme/post-density-spec.ts` | done |
| 3 | Floor в `semantic-alarms.css` (`--touch-min`, `--overview-group-min-*`) | done |
| 4 | Поднятие type scale во всех `designs/d0N-*.css` до floor | done |
| 5 | `OverviewGroupCard` + `MoSection` → токены floor | done |

### 1.4 Out of scope

| Не делаем здесь | Куда |
|-----------------|------|
| Полевые замеры 6 постов ЦПУ (Q9) | PM/field; протокол §8 |
| Photo evidence G-DS0-2 / plan AC | после Q9; waiver закрывает creative |
| Выбор финального `data-design` skin | отдельное утверждение; floor обязателен для всех preview skins |
| Полный re-layout экранов 5/8/6 | уже IMPLEMENT; floor через tokens |
| `PRODUCT.md` / impeccable init | optional `/impeccable init` — не блокер |

### 1.5 Блокер Q9 (не abort CREATIVE)

- Q9 **не** блокирует закрытие soft CR-UI-05 (паттерн CR-UI-04 / Ф2.5).
- Q9 **блокирует** финальную приёмку «photo at worst post» (plan AC CR-UI-05).
- До замеров: **явный waiver** §3 с worst-case row для всех 6 постов = одинаковая строка FHD 24" / 2.5 m / touch / medium качка.

---

## 2. Architecture — 3 варианта + recommendation

### Вариант A — Worst-case waiver + единый CSS floor (рекомендуется)

Одна формула `1/200 × distance` → `--font-critical` floor; touch ≥15 mm → `--touch-min`; Overview grid `minmax(var(--overview-group-min-w), 1fr)`. Константы в `post-density-spec.ts`. Все skins ≥ floor.

**Плюсы:** закрывает G-DS0-2-01…04 без ожидания поля; TDD математики; уже wired screens подхватывают tokens; согласуется с provisional §2.3 плана (замена после Q9 = правка чисел, не architecture).  
**Минусы:** если реальный worst post > 2.5 m — нужна ревизия; до Q9 нет photo AC.

### Вариант B — Ждать Q9, оставить provisional 40 px

**Плюсы:** нет ложной «финальности».  
**Минусы:** soft blocker висит; текущий `--font-critical: 40px` **ниже** 1/200 @ 2.5 m (~47.2 px); `--touch-min: 48px` ≈ 12.7 mm < 15 mm — **нарушение** G-DS0-2-02/03 уже сейчас.

### Вариант C — Per-post `data-post` + media/container queries

Шесть профилей плотности по `post_id` / viewport.

**Плюсы:** точность после Q9.  
**Минусы:** нет ID/карт постов; усложнение dual-axis theme×design→×post; premature до полевых данных.

### Recommendation

**Вариант A.** Зафиксировано. После Q9 — только пересчёт констант в `post-density-spec.ts` + CSS; architecture без смены. Вариант C — только отдельный CREATIVE, если замеры покажут разброс >20% по дистанции.

---

## 3. DS0-2 — таблица постов (waiver)

**Gate G-DS0-2-01:** таблица заполнена **или** явный waiver с worst-case.

| Post ID | Диагональ | Разрешение | Дистанция | Ввод | Освещённость | Качка | Источник |
|---------|-----------|------------|-----------|------|--------------|-------|----------|
| P1…P6 (все) | 24" | 1920×1080 | **2.5 m** | touch | day/night/dim (theme) | medium | **WAIVER** — Q9 не измерен; worst-case = plan §2.3 / CR-UI-05 AC |

**Worst row (канон расчёта):** Post = any; D = 2.5 m; FHD 24"; CSS reference dpi = **96** (как plan touch note).

**После Q9:** заменить строки реальными значениями; `WORST_VIEW_DISTANCE_M` = max(дистанции); пересчитать floor; photo §8.

---

## 4. Algorithm — формула floor (канон численный)

Код-контракт: `frontend/src/lib/theme/post-density-spec.ts`.

### 4.1 Critical type (G-DS0-2-02)

\[
h_{\mathrm{mm}} = \frac{D_{\mathrm{mm}}}{200},\quad
px = \left\lceil h_{\mathrm{mm}} \cdot \frac{96}{25.4} \right\rceil
\]

| Вход | Значение |
|------|----------|
| `WORST_VIEW_DISTANCE_M` | **2.5** |
| `VISUAL_RATIO` | **1/200** |
| `CSS_DPI` | **96** |
| `critical_mm` | 12.5 |
| **`--font-critical` floor** | **48 px** |

Проверка provisional 40 px: \(40 \times 25.4 / 96 \approx 10.6\,\mathrm{mm} < 12.5\) → **FAIL** до CR-UI-05.

### 4.2 Touch (G-DS0-2-03)

| Вход | Значение |
|------|----------|
| `TOUCH_MIN_MM` | **15** |
| **`--touch-min` floor** | **57 px** (`ceil(15 × 96/25.4)`) |

Provisional 48 px ≈ 12.7 mm → **FAIL** до CR-UI-05.

### 4.3 Type scale ladder (канон d01 / floor для всех skins)

Не масштабировать всё ×1.2 слепо: поднять **только** то, что ниже floor; сохранить характер denser skins где возможно.

| Token | Floor (px) | Use |
|-------|------------|-----|
| `--font-display-size` | **56** | AggregateShipStatus |
| `--font-critical` | **48** | alarm counts / critical |
| `--font-title` | **28** | section titles |
| `--font-body` | **18** | journal / group names |
| `--font-caption` | **14** | filters / meta |
| `--font-mono-value` | **20** | tabular values |
| `--touch-min` | **57** | buttons / cards hit |
| `--overview-group-min-w` | **176** | was 160 provisional |
| `--overview-group-min-h` | **128** | was 120 provisional |

**Skin deltas (после raise to floor):**

| Skin | display | critical | title | body | caption | mono |
|------|---------|----------|-------|------|---------|------|
| d01 | 56 | 48 | 32 | 18 | 14 | 22 |
| d02 | 56 | 48 | 28 | 18 | 15 | 20 |
| d03 | 56 | 48 | 28 | 18 | 14 | 22 |
| d04 | 56 | 48 | 28 | 18 | 14 | 20 |
| d05 | 64 | 48 | 32 | 19 | 14 | 24 |

### 4.4 OverviewGroupCard (вопрос плана)

| Параметр | Было (provisional) | Канон CR-UI-05 |
|----------|-------------------|----------------|
| Grid `minmax` | 160 px | `var(--overview-group-min-w)` = **176 px** |
| Card min height | touch 48 | `max(--touch-min, --overview-group-min-h)` → **128** content + pad |
| Name type | `--font-body` | без смены (18+) |
| Alarm count | `--font-caption` | без смены; critical count на Aggregate — `--font-critical` |

Сигнатура на расстоянии: **Lamp silhouette + body name**, не цвет alone (CR-UI-03).

---

## 5. UI-UX — плотность vs воздух (2+ варианта)

### Вариант UI-A — Floor-only bump (рекомендуется)

Подняли critical/touch/group min; body/caption почти без роста; gap-grid skins без смены.

**Плюсы:** G-DS0-2 без «раздувания» журнала; DENSITY 9.  
**Минусы:** d04 теряет часть «hard-edge compact» характера (title/body подняты до floor).

### Вариант UI-B — Full ladder ×1.2 от provisional d01

display 62 / critical 48 / title 36 / body 22 / caption 17.

**Плюсы:** запас на >2.5 m.  
**Минусы:** Journal/Watch переполнятся; конфликт с CR-UI-04 density 9.

### Вариант UI-C — Rem only + user zoom

Оставить px provisional; полагаться на OS zoom.

**Плюсы:** zero CSS churn.  
**Минусы:** посты ЦПУ часто kiosk без zoom; не закрывает gates.

### Recommendation

**UI-A + Architecture A.**

---

## 6. Gates mapping

| Gate | Критерий | Статус creative |
|------|----------|-----------------|
| G-DS0-2-01 | Таблица 6 постов или waiver | **PASS** — waiver §3 |
| G-DS0-2-02 | `--font-critical` ≥ 1/200 × worst D | **PASS** — 48 px @ 2.5 m |
| G-DS0-2-03 | Touch ≥ 15 mm worst | **PASS** — 57 px |
| G-DS0-2-04 | Токены в DS0-4 CSS | **PASS** — skins + semantic |
| Plan AC photo 2.5 m | Photo evidence | **OPEN** — после Q9; протокол §8 |

---

## 7. Implementation guide (уже применено в этом CREATIVE)

1. Импортировать / assert константы из `post-density-spec.ts` в unit (опционально follow-up TASK).
2. Компоненты: только `var(--font-*)`, `var(--touch-min)`, `var(--overview-group-min-*)` — без hardcoded 160/48.
3. После Q9: изменить `WORST_VIEW_DISTANCE_M` (и таблицу §3) → `npm`/скрипт не нужен; пересчитать `criticalFontPx` / `touchMinPx` → правка CSS одним проходом.
4. Photo: §8; не считать T-004 typography **field-accepted** до evidence.

---

## 8. Протокол замеров Q9 + photo evidence

**Цель:** заменить waiver реальными данными; закрыть plan AC CR-UI-05.

### 8.1 На каждый пост ЦПУ

1. Замерить: диагональ, native resolution, дистанция глаз→экран (м), тип ввода, lux (день/ночь если доступно), оценка качки.
2. Записать в таблицу §3 (снять пометку WAIVER).
3. `WORST_VIEW_DISTANCE_M = max(D_i)`.

### 8.2 Photo evidence (AC)

1. Theme `day` + product design (после выбора skin; default d01).
2. Screen 1 Overview: AggregateShipStatus + ≥1 OverviewGroupCard с Lamp + alarm count.
3. Фото с **worst post** на дистанции замера (штатив / метка на палубе).
4. Проверка: critical count и group name читаются без приближения; touch target палец ≥ визуального `--touch-min`.
5. Приложить файлы: `memory-bank/front/creative/evidence/CR-UI-05-worst-post/` (jpg/png) + строка в §Handoff follow-up.

### 8.3 Fail criteria

- Critical height на фото < расчётного mm → поднять `--font-critical`.
- Палец не закрывает hit area → поднять `--touch-min` / group min.

---

## 9. Rewire dependents

| Шаг | Действие |
|-----|----------|
| [s02](../../plan/decompose-v1-p1-screens/s02-tokens-themes.yaml) | `**Creative:**` → CR-UI-01 + CR-UI-05; soft Q9 closed via waiver |
| [s09](../../plan/decompose-v1-p1-screens/s09-screen-overview.yaml) | `**Creative:**` → CR-UI-05; Consumes density tokens |
| [index](../../plan/decompose-v1-p1-screens/index.md) | CR-UI-05 ✅ |

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Реальный D > 2.5 m | §8 пересчёт; numbers-only |
| d04 «слишком крупный» | floor > aesthetic; soft fail skin character |
| Photo AC open | не путать closed creative с field acceptance |
| Dual dpi (native vs CSS) | канон 96 CSS px; native PPI только в таблице Q9 |

---

## Handoff

- **Done:** FRONT CREATIVE CR-UI-05 — DS0-2 waiver + floor 48/57/176×128; tokens + OverviewGroupCard/MoSection; soft blocker closed
- **Files:** `memory-bank/front/creative/v1-p1-screens/CR-UI-05-post-density.md`; `frontend/src/lib/theme/post-density-spec.ts`; `frontend/src/styles/tokens/**`; `OverviewGroupCard.tsx`; `MoSection.tsx`
- **Next:** `FRONT REFLECT` T-004 (параллельно) или `BACK IMPLEMENT s11`; photo Q9 — soft follow-up
- **Tool / model:** Cursor + fast-editing
- **New chat:** yes — one chat = one atomic subtask
