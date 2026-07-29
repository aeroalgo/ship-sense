# CR-UI-03 — Alarm grammar (DS0-1) + Lamp SVG

**Тип:** Architecture + UI-UX  
**Задача:** T-004 / plan `plan-v1-p1-screens.md` §2.1, §3.1, §10 CR-UI-03  
**Decompose:** [s06-ds-components.md](../plan/decompose-v1-p1-screens/s06-ds-components.md)  
**Deps tokens:** [CR-UI-01-tokens.md](CR-UI-01-tokens.md) (`semantic-alarms.css`)  
**Дата:** 2026-07-26  
**Статус:** closed (creative) — IMPLEMENT s06 собирает `<Lamp />` + Storybook

---

## 0. Design Read

Reading this as: **ship-bridge HMI alarm grammar (ISA-101)** for watch officers at 2–3 m, industrial console language — **shape-first, color-second**, orthogonal composition of severity × lifecycle × quality; not traffic-light blobs, not SaaS status pills.

**Dial overrides (HMI):** VARIANCE 2 · MOTION 2 · DENSITY 9 (cockpit lamps).

**Skills applied:** `frontend-design` (subject-grounded signature), `design-taste-frontend` (trust/regulated dials), `emil-design-eng` (pulse only when rare+critical; reduced-motion), `impeccable` product register (a11y contrast, no layout anim), `high-end-visual-design` — **trimmed**: signature = Lamp silhouette language, not glass/bento marketing.

---

## 1. Проблема и scope

### 1.1 Вопрос плана

> Final matrix DS0-1 + animation rules.  
> AC: Grayscale print test passed.

### 1.2 Deliverables этого CREATIVE

| # | Путь | Статус |
|---|------|--------|
| 1 | `memory-bank/front/creative/CR-UI-03-alarm-grammar.md` (этот файл) | done |
| 2 | `frontend/public/ds/lamps/severity-*.svg` (6) | done |
| 3 | `frontend/public/ds/lamps/overlay-*.svg` (4) | done |
| 4 | `frontend/public/ds/lamps/grayscale-proof.html` | done |
| 5 | `frontend/src/lib/ds/lamp-grammar-spec.ts` | done |

**Alias плана:** `DS0-1-alarm-grammar.md` → канон = этот файл (`CR-UI-03-…`), как CR-UI-01.

### 1.3 Out of scope

| Не делаем здесь | Куда |
|-----------------|------|
| React `<Lamp />`, Storybook | FRONT IMPLEMENT s06 |
| ThemeProvider / skins | CR-UI-01 / s02 (уже) |
| Chart markers | CR-UI-02 / s11 |
| Watch compression UX | CR-UI-04 / s13 |
| Финальные lifecycle labels от APS | Q4 (режим A = reconstruction) |
| Финальный type scale постов | CR-UI-05 / Q9 |

### 1.4 Блокер Q4 (не abort CREATIVE)

- Q4 **не** блокирует старт DS0-1 / этот CREATIVE.
- Q4 **блокирует** финальную приёмку lifecycle-колонок журнала.
- Пока Q4 mode A / `X-Events-Reconstruction`: lifecycle ячейки в legend помечены **«реконструкция»** (G-DS0-1-05); UI показывает banner, не кнопку Ack.

---

## 2. Architecture — 3 варианта + recommendation

### Вариант A — Ортогональная композиция (рекомендуется)

**Слои:**

1. **Severity base SVG** — уникальный силуэт (форма).
2. **Quality overlay SVG** — паттерн поверх (или `null` для `good`).
3. **Lifecycle CSS** — opacity + pulse class (не отдельный файл на каждую ячейку).

**Математика:** 6 severity × 5 quality × 3 lifecycle ≈ 90 состояний из **10 SVG + CSS**, не 90 файлов.

**Плюсы:** grayscale uniqueness через форму+паттерн; поддержка; Storybook матрица; G-DS0-1-06 (SVG без raster); стык с CR-UI-01 tokens (`currentColor` / mask).  
**Минусы:** нужен аккуратный z-order и размеры `viewBox` 32×32.

### Вариант B — Плоский глиф на каждую ячейку

90+ уникальных SVG.  
**Плюсы:** пиксель-перфект контроль.  
**Минусы:** взрыв артефактов; дрейф при правке quarantine; FAIL по maintainability для s06.

### Вариант C — Только цвет (traffic light)

Круги red/yellow/green.  
**Плюсы:** знакомо.  
**Минусы:** **FAIL G-DS0-1-01** (grayscale); FAIL дальтонизм; противоречит plan §2.1 signature; quarantine легко путается с norm.

### Recommendation

**Вариант A.** Зафиксировано. B/C — только если A провалит grayscale print (маловероятно при proof HTML).

---

## 3. Оси матрицы (канон)

| Ось | Значения | Источник |
|-----|----------|----------|
| **severity** | `norm` · `warning-drift` · `alarm` · `protection-shutdown` · `no-data` · `info` | plan §3.1 + journal info + G-DS0-1-02 |
| **lifecycle** | `active` · `acked` · `cleared` | plan §3.1; display-only; ack на АПС |
| **quality** | `good` · `uncertain` · `bad` · `stale` · `quarantine` | plan §3.1 / `lib/quality` |

### 3.1 Расширения относительно сырого §3.1

| Добавлено | Зачем |
|-----------|--------|
| `no-data` | G-DS0-1-02: норма ≠ нет данных; стык `AggregateStatus = unknown` |
| `info` | journal/info events; token `--alarm-info-fg` уже в CR-UI-01 |

### 3.2 Приоритет визуала (кто «побеждает»)

1. **Quality `quarantine`** — всегда видимый оверлей `?` + диагонали; **никогда** не выглядит как зелёная/спокойная норма (G-DS0-1-03).
2. **Severity** — форма доминирует над hue (дальтонизм / grayscale).
3. **Lifecycle** — только приглушение / pulse; не меняет силуэт базы.
4. **Hue** — вторичен; только `semantic-alarms.css` / quality tokens; **не** chrome skins.

### 3.3 Mapping rollup → Lamp

Спека: `resolveGroupLamp()` в `lamp-grammar-spec.ts`.

| Aggregate / situation | Lamp |
|-----------------------|------|
| all good, no alarms | `norm` + `good` |
| worst child warning | `warning-drift` + quality |
| alarm / protection present | that severity + quality |
| any quarantine | severity (worst or norm) + **`quarantine`** |
| unknown / empty | **`no-data`** + `good` |
| stale/bad/uncertain without event | `norm` + that quality |

**Запрет:** `quarantine` → `norm`+`good` class / зелёный chrome. Rollup уже: quarantine > stale > bad > uncertain > good.

---

## 4. Силуэты severity (обязательная форма)

Все SVG: `viewBox="0 0 32 32"`, `currentColor`, без hardcoded alarm hex.

| severity | Файл | Силуэт (grayscale) | Color token |
|----------|------|--------------------|-------------|
| `norm` | `severity-norm.svg` | горизонтальная **капсула** (не круг!) | `--text-muted` |
| `warning-drift` | `severity-warning.svg` | **треугольник** outline | `--alarm-warning-fg` |
| `alarm` | `severity-alarm.svg` | **ромб** solid fill | `--alarm-critical-fg` |
| `protection-shutdown` | `severity-protection.svg` | **двойная квадратная рамка** + soft fill | `--alarm-critical-fg` |
| `no-data` | `severity-no-data.svg` | **разорванная** рамка + центральная точка | `--text-secondary` |
| `info` | `severity-info.svg` | **круг** outline + «i» | `--alarm-info-fg` |

**Почему norm ≠ круг:** круг занят `info`; «зелёный кружок» = антипаттерн traffic light и путается с no-data в grayscale.

**Почему alarm ≠ protection:** оба critical hue, но ромб ≠ double-frame — защита читается отдельно на StatusBar / Watch (G-DS0-3 иерархия).

---

## 5. Оверлеи quality

| quality | Файл | Силуэт | Color token |
|---------|------|--------|-------------|
| `good` | — | нет слоя | — |
| `uncertain` | `overlay-uncertain.svg` | 8 точек по периметру | `--quality-uncertain-fg` |
| `bad` | `overlay-bad.svg` | крест + оси | `--quality-bad-fg` |
| `stale` | `overlay-stale.svg` | пунктирный квадрат | `--quality-stale-fg` |
| `quarantine` | `overlay-quarantine.svg` | диагонали + диск «?» | `--quality-quarantine-fg` |

**Стык с CR-UI-01 §4:** те же метафоры (dotted / cross hatch / dashed / diagonal+?).

---

## 6. Lifecycle (CSS, не SVG)

| lifecycle | Opacity | Pulse | Вид |
|-----------|---------|-------|-----|
| `active` | 1.0 | да, если `shouldPulse` | полный контраст |
| `acked` | 0.55 | нет | приглушён (G-DS0-1-04) |
| `cleared` | 0.40 | нет | ещё слабее; визуально «контур уходит» |

### 6.1 Pulse rules (animation)

| Правило | Значение |
|---------|----------|
| Частота | **0.5 Hz** (period 2000 ms) — plan §2.x |
| Когда | только `lifecycle=active` **и** (`alarm` \| `protection-shutdown`) |
| Что анимируем | **outline / box-shadow**, не layout, не fill flash |
| `prefers-reduced-motion: reduce` | pulse **off**; static thicker outline / `data-pulse="static"` |
| Не пульсировать | warning, info, norm, no-data, acked, cleared |
| Не анимировать | keyboard focus ring отдельно (`--focus-ring`, не alarm) |

Константы: `LAMP_PULSE` в `lamp-grammar-spec.ts`.  
Ключи CSS (s06): `@keyframes lamp-pulse-outline` + `--lamp-pulse-ms: 2000ms`.

**Emil / HMI:** лампа на вахте видна постоянно → motion минимален; pulse = «ещё не обработано на АПС», не декорация.

### 6.2 Q4 reconstruction

| Режим | UI |
|-------|-----|
| Q4 incomplete / mode A | `reconstructed=true` на Lamp; legend: «lifecycle — реконструкция»; journal banner |
| Q4 final | снять пометку; labels active/acked/cleared = канон APS |

---

## 7. Полная матрица (логика ячеек)

Не 90 отдельных дизайнов — **правило композиции**:

```
visual = severitySvg(severity)
       + (quality !== good ? overlaySvg(quality) : ∅)
       + lifecycleCss(lifecycle)
       + (shouldPulse ? pulseClass : ∅)
```

### 7.1 Критические отличия (AC)

| Пара | Как различаются в grayscale |
|------|------------------------------|
| `norm` vs `no-data` | капсула vs разорванная рамка+точка (G-DS0-1-02) |
| `norm+good` vs `norm+quarantine` | нет оверлея vs диагонали+? (G-DS0-1-03) |
| `alarm` vs `protection` | ромб vs double square |
| `warning` vs `info` | треугольник vs круг |
| `uncertain` vs `stale` | точки vs dash-rect |
| `active` vs `acked` vs `cleared` | opacity ladder (G-DS0-1-04) |

### 7.2 Размеры

| size | px | Где |
|------|-----|-----|
| `sm` | 16 | EventRow densе, chips |
| `md` | 24 | default OverviewGroupCard |
| `lg` | 32 | StatusBar alarm chips |
| `xl` | 48 | AggregateShipStatus |

Touch: контейнер кликабельной лампы ≥ `--touch-min` (48px) даже при `sm` glyph.

---

## 8. AggregateShipStatus + StatusBar (signature)

### 8.1 AggregateShipStatus

- Норма: спокойная серая плоскость + `Lamp` `norm/good` (форма капсулы едва заметна).
- Тревога: **форма xl** доминирует; hue secondary; label одной строкой (без «AI»).
- Карантин: xl lamp с quarantine overlay + QuarantineBanner снаружи.

### 8.2 StatusBar alarm chips

- Список active alarms: severity glyph + short text; click → journal filter.
- Pulse только unacked critical.
- Compact: `sm`/`md`; не прятать protection.

---

## 9. Implementation guide (для s06)

### 9.1 Компонент `<Lamp />`

```tsx
// контракт (не код production здесь — s06)
props: { severity, lifecycle, quality, size?, reconstructed? }
data-testid="lamp"
data-severity={severity}
data-lifecycle={lifecycle}
data-quality={quality}
data-pulse={shouldPulse ? "on"|"static" : "off"}
data-reconstructed={reconstructed ? "true" : undefined}
```

**Рендер:** предпочтительно **inline SVG** или CSS `mask-image` с `background-color: var(--token)`, чтобы `currentColor`/tokens работали.  
`<img src=…>` — только proof/print; для product UI **не** полагаться на наследование color в `<img>`.

**Запрет:** hardcoded `#ff4d4f` в TSX; только tokens из `SEVERITY_COLOR_TOKEN` / `QUALITY_COLOR_TOKEN`.

### 9.2 Структура файлов (s06 дорисует)

```
frontend/public/ds/lamps/          # DONE creative
frontend/src/lib/ds/lamp-grammar-spec.ts  # DONE creative
frontend/src/components/ds/Lamp.tsx       # s06
frontend/src/components/ds/Lamp.test.tsx  # s06 — каждая severity×quality → unique data-state
frontend/src/components/ds/Lamp.module.css # pulse + lifecycle opacity
```

### 9.3 TDD (из decompose s06)

1. Каждая комбинация severity×quality → уникальный `data-severity`+`data-quality`.
2. `quarantine` ≠ class/path нормы.
3. Stories: матрица + lifecycle + reduced-motion.

### 9.4 Storybook

- Story «Matrix» = таблица как в proof HTML.
- Story «Lifecycle».
- Story «AggregateShipStatus xl».
- Addon: emulate `prefers-reduced-motion`.

### 9.5 Print / grayscale evidence

1. Открыть `/ds/lamps/grayscale-proof.html` (dev server или `file:`).
2. Toggle grayscale → Print / PDF.
3. Чеклист G-DS0-1-01..05 вручную.
4. Приложить PDF или скрин в PR s06 (creative фиксирует процедуру).

**Creative self-check 2026-07-26:** силуэты severity различимы без цвета; quarantine оверлей читается поверх любой базы; lifecycle ladder задан числами opacity.

---

## 10. UI-UX варианты оформления лампы (chrome вокруг glyph)

### Вариант U1 — Naked glyph (рекомендуется для HMI)

Только SVG(+overlay) на нейтральном surface; без pill background.  
**Плюсы:** меньше шума на Overview; форма читается с 2.5 m.  
**Минусы:** на очень тёмном dim нужна достаточная яркость token (уже в semantic).

### Вариант U2 — Soft chip plate

Glyph в `surface-2` rounded rect.  
**Плюсы:** кликабельность.  
**Минусы:** на сетке групп — визуальный «карточки» шум; против «норма не светится».

### Вариант U3 — Neon glow blob

Glow + saturated fill.  
**Плюсы:** «вау».  
**Минусы:** FAIL ISA-101 / night flash; AI-slop; запрет.

### Recommendation UI chrome

**U1** для Lamp в карточках/агрегате; кликабельный hit-area прозрачный ≥48px. StatusBar chip может иметь subtle `alarm-*-bg` plate (уже токены bg) — не neon.

---

## 11. a11y / дальтонизм / print

| Требование | Решение |
|------------|---------|
| Не цвет-единственный | форма + паттерн |
| Contrast | critical/warning на surface-0 ≥ крупные glyph; text рядом с Lamp ≥ 4.5:1 |
| Screen reader | `aria-label` составной: «Тревога, активна, карантин» (copy RU в s06; без «AI») |
| Focus | `--focus-ring` на hit-area, не путать с alarm pulse |
| Print monochrome | proof HTML + PrintLayout журнала использует те же SVG |

---

## 12. Copy / legend (RU)

| Ключ | Текст |
|------|-------|
| Legend title | Грамматика состояний |
| norm | Норма |
| warning-drift | Предупреждение / дрейф |
| alarm | Тревога |
| protection-shutdown | Защита / стоп |
| no-data | Нет данных |
| info | Информация |
| active | Активна |
| acked | Квитирована (на АПС) |
| cleared | Снята |
| quarantine | На сверке |
| reconstructed | Реконструкция (Q4) |
| pulse hint | Мигание контура — активная неквитированная тревога/защита |

**Запрет:** слово «AI» в любом copy ламп/легенды.

---

## 13. AC gate mapping

| ID | Критерий | Evidence |
|----|----------|----------|
| G-DS0-1-01 | Уникальный силуэт в grayscale | `grayscale-proof.html` + §7.1 |
| G-DS0-1-02 | Норма ≠ нет данных | `norm` капсула vs `no-data` broken frame |
| G-DS0-1-03 | Карантин ≠ зелёная норма | overlay `?` всегда; resolveGroupLamp |
| G-DS0-1-04 | acked/cleared приглушены | opacity 0.55 / 0.40 |
| G-DS0-1-05 | Q4 mode A → «реконструкция» | `reconstructed` + legend §12 |
| G-DS0-1-06 | SVG в Lamp без raster | assets в `public/ds/lamps/*.svg`; s06 wire |

**CR-UI-03 plan AC:** Grayscale print test — процедура §9.5; creative closed с proof page.

---

## 14. Риски

| Риск | Mitigation |
|------|------------|
| `<img>` не красит currentColor | s06: mask/inline SVG |
| Q4 labels drift | reconstructed flag до закрытия Q4 |
| Skin dNN меняет alarm hue | запрет CR-UI-01; review |
| Pulse раздражает на качке | 0.5 Hz only critical active; reduced-motion off |
| Quarantine fill `#1a1d23` в overlay | s06 может заменить на `var(--surface-1)` при inline |

---

## 15. Связь с другими CREATIVE / шагами

| ID | Связь |
|----|-------|
| CR-UI-01 | hue tokens; формы отложены сюда |
| CR-UI-02 | chart markers — те же severity shapes (reuse SVG ids) |
| CR-UI-04 | Watch sections используют Lamp в rows |
| s06 | единственный IMPLEMENT consumer |
| s09/s10 | Overview/Journal — только через ds/Lamp |

---

## 16. Чеклист creative

- [x] 2+ architecture варианта + recommendation (A)
- [x] 2+ UI chrome варианта + recommendation (U1)
- [x] Матрица осей + composition rules
- [x] Animation / reduced-motion rules
- [x] SVG export (10 files) + proof HTML
- [x] Spec TS для s06
- [x] Q4 reconstruction legend
- [x] Decompose link s06
- [x] Tokens/signature задокументированы
- [x] Без слова «AI» в copy

---

## Handoff

- **Done:** FRONT CREATIVE CR-UI-03 — DS0-1 alarm grammar (вариант A: ортогональная композиция), SVG lamps + overlays, grayscale-proof, `lamp-grammar-spec.ts`
- **Files:** `memory-bank/front/creative/CR-UI-03-alarm-grammar.md`; `frontend/public/ds/lamps/*`; `frontend/src/lib/ds/lamp-grammar-spec.ts`
- **Next:** (1) `FRONT IMPLEMENT` s04 api-client (очередь activeContext) или s06 после CR-UI-03; (2) grayscale print из proof HTML; (3) параллельно s04 OK
- **Tool / model:** Cursor + fast-editing для s04; Cursor/premium для s06 (Storybook + матрица)
- **New chat:** yes — CREATIVE закрыт; IMPLEMENT отдельно

## Следующий шаг

→ `FRONT IMPLEMENT` s04 (api-client) **или** `FRONT IMPLEMENT` s06 (ds-components) после s04–s05 по очереди decompose.
