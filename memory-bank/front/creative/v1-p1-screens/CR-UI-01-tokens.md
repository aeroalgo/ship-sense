# CR-UI-01 — DS0-4 tokens + 5 design skins × day|night|dim

**Тип:** Architecture + UI-UX  
**Задача:** T-004 / plan `plan-v1-p1-screens.md` §2.2–2.5, §10 CR-UI-01  
**Decompose:** [s02-tokens-themes.yaml](../../plan/decompose-v1-p1-screens/s02-tokens-themes.yaml)  
**Дата:** 2026-07-26  
**Статус:** closed (creative) — IMPLEMENT s02 подключает provider/switchers

---

## 0. Design Read

Reading this as: **ship-bridge HMI (ISA-101)** for watch officers at 2–3 m, with industrial console language, leaning toward **CSS variables + CSS Modules**, dual-axis theming (`data-design` × `data-theme`), not SaaS dashboard aesthetics.

**Dial overrides (HMI):** VARIANCE 3 · MOTION 2 · DENSITY 8–9 (cockpit).

---

## 1. Проблема и scope

### 1.1 Вопрос плана (исходный)

> CSS variables only vs CSS-in-JS vs Tailwind extend?

### 1.2 Расширение от заказчика (этот CREATIVE)

Нужно **5 визуальных направлений** (design skins), у каждого полный набор под **day | night | dim**.  
Итого **15 chrome-пакетов** + **1 общий** слой alarm/quality.  
После утверждения одного skin — остальные снести.

### 1.3 Out of scope (явно)

| Не делаем здесь | Куда |
|-----------------|------|
| Экраны s09+ | FRONT IMPLEMENT |
| Chart library | CR-UI-02 |
| Lamp SVG / DS0-1 формы | CR-UI-03 |
| Финальная плотность постов | CR-UI-05 / Q9 (provisional OK) |
| ThemeProvider / layout wiring | FRONT IMPLEMENT s02 |
| Scaffold Next package.json | FRONT IMPLEMENT s01 |

### 1.4 Deliverables этого CREATIVE

| # | Путь | Статус |
|---|------|--------|
| 1 | `memory-bank/front/creative/v1-p1-screens/CR-UI-01-tokens.md` (этот файл) | done |
| 2 | `frontend/src/styles/tokens/semantic-alarms.css` | done |
| 3 | `frontend/src/styles/tokens/motion.css` | done |
| 4 | `frontend/src/styles/tokens/designs/d01…d05-*.css` (5 файлов × 3 theme) | done |
| 5 | `frontend/src/styles/tokens/index.css` (+ legacy `colors.css`) | done |
| 6 | `frontend/src/lib/theme/types.ts` (`ThemeTokens`, `DesignId`, `ThemeId`) | done |
| 7 | `frontend/src/lib/theme/switcher-spec.ts` (API + testids + preview gate) | done |

---

## 2. Architecture — 3 варианта + recommendation

### Вариант A — CSS variables + атрибуты на `<html>` (рекомендуется)

**Механика:**

```html
<html data-design="d01" data-theme="night">
```

- Селекторы: `html[data-design="dNN"][data-theme="day|night|dim"] { --surface-0: … }`
- Компоненты используют только `var(--token)`, без hardcoded hex
- CSS Modules для layout/компонентов; токены — global import в root layout

**Плюсы:** zero runtime theme cost; SSR-friendly; FOUC лечится blocking inline script до paint; легко удалить 4 skin-файла; соответствует plan §2.2; Playwright просто assert на `html[data-*]`.  
**Минусы:** 15 блоков CSS вручную (уже сгенерированы); нет «типобезопасности» значений hex в CSS (компенсация — `ThemeTokens` + карта `THEME_TOKEN_CSS_VARS`).

### Вариант B — CSS-in-JS (vanilla-extract / Panda)

**Плюсы:** typed tokens в TS.  
**Минусы:** лишний toolchain на пост-мониторе; сложнее anti-flash; удаление skins = правки codegen; конфликт с «CSS Modules default» плана.

### Вариант C — Tailwind `theme.extend` + plugins

**Плюсы:** быстрый DX в marketing UI.  
**Минусы:** план явно «без Tailwind по умолчанию»; dual-axis (design×theme) раздувает config; class churn в HMI-компонентах хуже читается на качке.

### Recommendation

**Вариант A.** Зафиксировано. Tailwind/CSS-in-JS — только отдельный CREATIVE, если A провалится по DX (маловероятно).

---

## 3. Две оси (не смешивать)

| Атрибут | Значения | Смысл | Жизненный цикл |
|---------|----------|-------|----------------|
| `data-theme` | `day` \| `night` \| `dim` | Освещённость поста (ISA-101) | **Навсегда** (продукт) |
| `data-design` | `d01`…`d05` | Визуальный язык (шрифты, радиусы, плотность, chrome hue) | Preview → **оставить 1**, снести 4 |

**Persist:**

| Key | Значение | Кто пишет |
|-----|----------|-----------|
| `localStorage['shipsense-theme']` | ThemeId | `ThemeProvider` / `useTheme` (продукт) |
| `localStorage['shipsense-design']` | DesignId | `DesignProvider` / `useDesign` (preview; после утилизации — захардкодить default или убрать ключ) |

**Default:** `theme=day`, `design=d01` (Bridge Console — ближайший к plan §2.2).

**Запрет:** менять alarm/quality hue при смене `data-design`. Семантика — только `semantic-alarms.css`.

---

## 4. Общий слой семантики (invariant)

Файл: `frontend/src/styles/tokens/semantic-alarms.css`

| Token | Hex / value | DS0-1 форма (ссылка; SVG в CR-UI-03) |
|-------|-------------|--------------------------------------|
| `--alarm-critical-fg` | `#ff4d4f` | ромб + solid |
| `--alarm-critical-bg` | `rgba(255,77,79,0.12)` | — |
| `--alarm-warning-fg` | `#faad14` | треугольник outline |
| `--alarm-warning-bg` | `rgba(250,173,20,0.12)` | — |
| `--alarm-info-fg` | `#69b1ff` | circle outline |
| `--alarm-info-bg` | `rgba(105,177,255,0.12)` | — |
| `--quality-bad-fg` | `#ff7875` | cross hatch |
| `--quality-quarantine-fg` | `#b37feb` | diagonal + ? |
| `--quality-stale-fg` | `#8c8c8c` | dashed |
| `--quality-uncertain-fg` | `#ffc069` | dotted |

**Правила:**

1. Нормальные поверхности/текст — **только** нейтрали дизайна; цвет = отклонение.
2. `--chrome-accent` и `--focus-ring` — **не** alarm; это UI chrome (клавиатура, активная вкладка). Не использовать как severity.
3. Global stale: `body[data-stale="true"] #app-root { filter: saturate(0.55) brightness(0.92); }` — баннеры свежести **вне** `#app-root` или выше z-index без filter.
4. Запрет `#ffffff` / `#f5f5f5` как `--surface-*` в night/dim (проверено в пакетах ниже).
5. Слово «AI» в UI — запрет (product).

---

## 5. Пять дизайнов — портреты

### 5.1 d01 Bridge Console (default candidate)

- **Метафора:** стальной мостиковый HMI, знакомый по ECDIS/консолям.
- **Шрифты:** IBM Plex Sans + IBM Plex Mono.
- **Радиусы:** 2 / 4 / 6 px.
- **Плотность:** высокая, gap 16, statusbar 56/48.
- **Chrome accent:** холодный steel blue-gray (`#6b7c8f` day).
- **Signature:** спокойная серая плоскость; иерархия через surface-0/1/2 без декора.
- **Риск:** «слишком как план» — зато безопасный baseline для IMPLEMENT.
- **Файл:** `designs/d01-bridge-console.css`

### 5.2 d02 Chart Table

- **Метафора:** стол карт / paper chart under glass.
- **Шрифты:** Source Sans 3 + IBM Plex Mono.
- **Радиусы:** чуть мягче (3/6/8).
- **Воздух:** gap 20, pad 20/28.
- **Chrome accent:** приглушённый teal **только** focus/chrome (`#2f7a72` day) — не alarm green.
- **Signature:** «картографическая» холодная нейтраль surfaces.
- **Файл:** `designs/d02-chart-table.css`

### 5.3 d03 Machinery Deck

- **Метафора:** машинное отделение, штампованный металл, толстые рамки.
- **Шрифты:** IBM Plex Sans + JetBrains Mono (цифры доминируют).
- **Бордеры:** 2–3 px; radius почти 0.
- **Chrome accent:** тёплый brass (`#8a7040`) — **не** warning yellow alarm.
- **Signature:** tabular mono values 22px; tracking labels 0.08em.
- **Файл:** `designs/d03-machinery-deck.css`

### 5.4 d04 Hard Edge

- **Метафора:** military CRT / strip chart, максимальная плотность на пост.
- **Шрифты:** IBM Plex Sans (+ Condensed display).
- **Радиусы:** все 0; hairline 1px; gap 8; caption 12px.
- **Chrome accent:** нейтральный gunmetal.
- **Signature:** почти «нет UI chrome» — только линии и данные.
- **Риск:** усталость глаз на day — компенсируется night/dim ramp.
- **Файл:** `designs/d04-hard-edge.css`

### 5.5 d05 Instrument Cluster

- **Метафора:** приборный щиток; крупный aggregate ship status.
- **Шрифты:** Barlow / Barlow Condensed (display 64px).
- **Радиусы:** 4/8/12 — единственный более «округлый» skin (всё ещё industrial).
- **Chrome accent:** muted sea-green для chrome.
- **Signature:** `--font-display-size: 64px` для AggregateShipStatus.
- **Файл:** `designs/d05-instrument-cluster.css`

---

## 6. Матрица токенов 5 × 3 (chrome)

Ниже — **все** комбинации. Alarm/quality — §4 (общие).

### 6.1 Поверхности и текст

#### d01 Bridge Console

| Token | day | night | dim |
|-------|-----|-------|-----|
| `--surface-0` | `#1a1d21` | `#121418` | `#0e1012` |
| `--surface-1` | `#22262c` | `#1a1d23` | `#15181c` |
| `--surface-2` | `#2a2f36` | `#22262e` | `#1c2026` |
| `--text-primary` | `#e8eaed` | `#d8dce2` | `#b8bcc4` |
| `--text-secondary` | `#9aa0a8` | `#889098` | `#788088` |
| `--text-muted` | `#6b7280` | `#5c6370` | `#505860` |
| `--border-subtle` | `#3a4048` | `#323840` | `#2a3038` |
| `--border-strong` | `#4a525c` | `#3e4650` | `#343c44` |
| `--focus-ring` | `#5b8def` | `#4a7ad4` | `#3d6ab8` |
| `--chrome-accent` | `#6b7c8f` | `#5a6a7c` | `#4a5868` |
| `--statusbar-height` | `56px` | `56px` | `48px` |

#### d02 Chart Table

| Token | day | night | dim |
|-------|-----|-------|-----|
| `--surface-0` | `#161c20` | `#10161a` | `#0c1014` |
| `--surface-1` | `#1c242a` | `#161e24` | `#12181c` |
| `--surface-2` | `#243038` | `#1e2a30` | `#182024` |
| `--text-primary` | `#e2ebe8` | `#d0dbd8` | `#b0bcb8` |
| `--text-secondary` | `#8aa09a` | `#7a908a` | `#687870` |
| `--text-muted` | `#5e706c` | `#546460` | `#485450` |
| `--border-subtle` | `#2e3c42` | `#283438` | `#222c30` |
| `--border-strong` | `#3a4e52` | `#344448` | `#2c383c` |
| `--focus-ring` | `#3d9b8f` | `#348a80` | `#2a7068` |
| `--chrome-accent` | `#2f7a72` | `#286860` | `#205850` |
| `--statusbar-height` | `56px` | `56px` | `48px` |

#### d03 Machinery Deck

| Token | day | night | dim |
|-------|-----|-------|-----|
| `--surface-0` | `#1c1a18` | `#141210` | `#100e0c` |
| `--surface-1` | `#26221e` | `#1c1a16` | `#181612` |
| `--surface-2` | `#302a24` | `#26221c` | `#201c18` |
| `--text-primary` | `#ece6dc` | `#dcd4c8` | `#bcb4a8` |
| `--text-secondary` | `#a89880` | `#968870` | `#807060` |
| `--text-muted` | `#706858` | `#605848` | `#504840` |
| `--border-subtle` | `#443c34` | `#3a342c` | `#302c26` |
| `--border-strong` | `#5a5044` | `#4e463c` | `#403830` |
| `--focus-ring` | `#c4a35a` | `#a88848` | `#8a7038` |
| `--chrome-accent` | `#8a7040` | `#746038` | `#5e4c30` |
| `--statusbar-height` | `56px` | `56px` | `48px` |

#### d04 Hard Edge

| Token | day | night | dim |
|-------|-----|-------|-----|
| `--surface-0` | `#0a0c0e` | `#06080a` | `#040506` |
| `--surface-1` | `#121416` | `#0e1012` | `#0a0c0e` |
| `--surface-2` | `#1a1c1e` | `#16181a` | `#121416` |
| `--text-primary` | `#e0e4e8` | `#c8ccd0` | `#a8acb0` |
| `--text-secondary` | `#889098` | `#707880` | `#606870` |
| `--text-muted` | `#585e66` | `#484e54` | `#404448` |
| `--border-subtle` | `#2a2e32` | `#222628` | `#1a1e20` |
| `--border-strong` | `#3a3e42` | `#323638` | `#282c2e` |
| `--focus-ring` | `#7a8a9a` | `#6a7a8a` | `#5a6a7a` |
| `--chrome-accent` | `#5a6a7a` | `#4a5a6a` | `#3a4a5a` |
| `--statusbar-height` | `48px` | `48px` | `44px` |

#### d05 Instrument Cluster

| Token | day | night | dim |
|-------|-----|-------|-----|
| `--surface-0` | `#14181c` | `#0e1216` | `#0a0e12` |
| `--surface-1` | `#1c2228` | `#161a20` | `#12161a` |
| `--surface-2` | `#262e36` | `#1e262e` | `#1a2026` |
| `--text-primary` | `#e6ecf0` | `#d4dce2` | `#b4bcc4` |
| `--text-secondary` | `#8a9aa8` | `#7a8a98` | `#687888` |
| `--text-muted` | `#5c6a78` | `#506070` | `#44505c` |
| `--border-subtle` | `#343e48` | `#2c3640` | `#242c34` |
| `--border-strong` | `#46525e` | `#3e4a56` | `#343c44` |
| `--focus-ring` | `#5a9e8a` | `#4a8a78` | `#3a7060` |
| `--chrome-accent` | `#3d7a6a` | `#346858` | `#2a5848` |
| `--statusbar-height` | `60px` | `60px` | `52px` |

### 6.2 Chrome density / type (не зависят от theme, кроме statusbar)

| Token | d01 | d02 | d03 | d04 | d05 |
|-------|-----|-----|-----|-----|-----|
| `--radius-sm/md/lg` | 2/4/6 | 3/6/8 | 0/2/2 | 0/0/0 | 4/8/12 |
| `--border-width` / strong | 1/2 | 1/1 | 2/3 | 1/1 | 1/2 |
| `--gap-grid` | 16 | 20 | 12 | 8 | 16 |
| `--panel-pad` | 16 | 20 | 14 | 10 | 18 |
| `--content-pad-x` | 24 | 28 | 20 | 16 | 24 |
| `--font-display-size` | 52 | 48 | 50 | 44 | **64** |
| `--font-critical` | 40 | 38 | 42 | 36 | 48 |
| `--font-title` | 30 | 28 | 28 | 24 | 32 |
| `--font-body` | 18 | 18 | 18 | 16 | 19 |
| `--font-caption` | 14 | 15 | 14 | 12 | 14 |
| `--font-mono-value` | 20 | 19 | **22** | 18 | 24 |
| `--tracking-label` | 0.04em | 0.06em | 0.08em | 0.12em | 0.05em |
| `--space-unit` | 8 | 8 | 8 | **4** | 8 |

**Provisional:** type scale до Q9 / CR-UI-05 — можно подкрутить без смены architecture.

### 6.3 Контраст (AC check)

- Body text (`--text-primary` on `--surface-0`): все 15 комбинаций — тёмный фон + светлый текст; целевой ≥4.5:1 на FHD.
- Muted на secondary panels — допускается ближе к 3:1 только для decorative labels; critical values — primary или mono-value.
- Night/dim: яркость surfaces и text снижается вместе (нет «белой вспышки»).

---

## 7. Motion / anti-flash

Файл: `motion.css`

1. `html { color-scheme: dark; }`
2. Transition surfaces/text/border ≤ `--motion-theme-ms: 150ms`
3. `prefers-reduced-motion: reduce` → почти 0
4. `html:not([data-theme])` fallback фон `#121418` (не белый)
5. **Blocking script** (IMPLEMENT s02) в `<head>` **до** CSS paint:

```js
(function () {
  try {
    var t = localStorage.getItem("shipsense-theme");
    var d = localStorage.getItem("shipsense-design");
    if (t === "day" || t === "night" || t === "dim") {
      document.documentElement.setAttribute("data-theme", t);
    } else {
      document.documentElement.setAttribute("data-theme", "day");
    }
    if (d === "d01" || d === "d02" || d === "d03" || d === "d04" || d === "d05") {
      document.documentElement.setAttribute("data-design", d);
    } else {
      document.documentElement.setAttribute("data-design", "d01");
    }
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "day");
    document.documentElement.setAttribute("data-design", "d01");
  }
})();
```

6. Запрещено: blink/strobe >1 Hz на весь экран (plan §2.5).

---

## 8. Спека ThemeSwitcher + DesignSwitcher

### 8.1 ThemeSwitcher (продукт)

| Поле | Значение |
|------|----------|
| Path (s02) | `frontend/src/components/ds/ThemeSwitcher.tsx` |
| Props | `{ theme: ThemeId; onChange: (t: ThemeId) => void }` |
| `data-testid` | `theme-switcher` |
| Поведение | cycle `day → night → dim → day` (или segmented control 3 кнопки — IMPLEMENT выбирает UX; API стабилен) |
| Persist | `shipsense-theme` |
| A11y | `aria-label` «Тема освещения»; min touch 48×48 |
| E2E | plan PW theme: click ×2 → `html[data-theme=dim]` |

### 8.2 DesignSwitcher (только preview)

| Поле | Значение |
|------|----------|
| Path (s02) | `frontend/src/components/ds/DesignSwitcher.tsx` |
| Props | `{ design: DesignId; onChange: (d: DesignId) => void; enabled?: boolean }` |
| `data-testid` | `design-switcher` |
| Gate | `isDesignPreviewEnabled()` — `NODE_ENV===development` **или** `NEXT_PUBLIC_DESIGN_PREVIEW=1` |
| Persist | `shipsense-design` |
| Production default | компонент **не монтировать** если gate false |
| Labels | `DESIGN_META[id].title` |

Константы: `frontend/src/lib/theme/switcher-spec.ts`.

### 8.3 Providers (IMPLEMENT s02 — guide)

| Module | Responsibility |
|--------|----------------|
| `ThemeProvider` | sync `data-theme`, localStorage, `useTheme` |
| `DesignProvider` | sync `data-design`, localStorage, `useDesign` (можно один `AppearanceProvider`) |
| `layout.tsx` | import `@/styles/tokens/index.css`; blocking script; wrap providers |

Тесты (s02 TDD): cycle order, round-trip storage, default day/d01, reject invalid storage values.

---

## 9. Сравнение дизайнов (для выбора заказчиком)

| Критерий | d01 | d02 | d03 | d04 | d05 |
|----------|-----|-----|-----|-----|-----|
| Близость к plan §2.2 | ★★★★★ | ★★★★ | ★★★ | ★★★ | ★★★★ |
| Плотность на пост | ★★★★ | ★★★ | ★★★★ | ★★★★★ | ★★★ |
| Читаемость цифр | ★★★★ | ★★★★ | ★★★★★ | ★★★ | ★★★★★ |
| Отличие «не SaaS» | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★ |
| Риск усталости | низкий | низкий | средний (warm) | высокий на day | низкий |
| Сложность DS components | низкая | низкая | средняя (thick borders) | средняя (0 radius) | средняя (large display) |

### Recommendation (provisional default)

**Пока утверждаете — default `d01`.**  
Кандидаты к финалу после живого переключения на Overview mock: **d01** (безопасный) vs **d05** (сильный signature AggregateShipStatus) vs **d02** (если хотите «морской» teal chrome).  
**d04** — только если пост очень тесный и экипаж ок с densest UI.  
**d03** — если приоритет машинных цифр/mono.

Финальный выбор = решение пользователя после preview; creative **не** удаляет skins до явного «утверждаем dNN».

---

## 10. Правило утилизации (после утверждения)

Когда пользователь говорит «утверждаем d0X»:

1. Оставить `designs/d0X-*.css`; переименовать опционально в `design-canonical.css` **или** оставить id и захардкодить `DEFAULT_DESIGN = "d0X"`.
2. Удалить остальные 4 файла в `designs/`.
3. Убрать импорты из `index.css`.
4. Удалить `DesignSwitcher.tsx`, `useDesign` (или заглушить no-op), убрать `DESIGN_IDS` лишние из `types.ts`.
5. Blocking script: всегда `data-design="d0X"` (или убрать атрибут и перенести токены на `html[data-theme=…]` only).
6. Удалить `shipsense-design` из localStorage migration note.
7. Обновить этот файл §статус → `canonical: d0X`; plan/style-guide одной строкой.
8. Playwright: убрать design-switcher specs; оставить theme specs.

**Не трогать:** `data-theme`, `semantic-alarms.css`, alarm grammar.

---

## 11. Implementation guide (для FRONT IMPLEMENT s02)

### 11.1 Порядок работ

1. Убедиться s01 scaffold умеет импортировать CSS в `layout.tsx`.
2. `import "@/styles/tokens/index.css"`.
3. Inline blocking script (§7).
4. TDD: `theme.test.ts` / `design.test.ts` — cycle + storage.
5. `ThemeProvider` + `ThemeSwitcher`.
6. `DesignProvider` + `DesignSwitcher` за preview gate.
7. Visual smoke: 5×3 ручной чеклист или Storybook appearance panel (s06).
8. Не хардкодить hex в компонентах — только `var(--…)`.

### 11.2 Файловая карта (as-built + planned)

```
frontend/src/styles/tokens/
  index.css
  colors.css              # legacy alias → index
  typography.css          # pointer note
  spacing.css             # pointer note
  semantic-alarms.css     # DONE
  motion.css              # DONE
  designs/
    d01-bridge-console.css
    d02-chart-table.css
    d03-machinery-deck.css
    d04-hard-edge.css
    d05-instrument-cluster.css
frontend/src/lib/theme/
  types.ts                # DONE
  switcher-spec.ts        # DONE
  # s02: theme-storage.ts, useTheme.ts, useDesign.ts
frontend/src/features/session/
  # s02: ThemeProvider.tsx (или AppearanceProvider)
frontend/src/components/ds/
  # s02: ThemeSwitcher.tsx, DesignSwitcher.tsx
```

### 11.3 Расширение s02 AC (поверх decompose)

- [ ] Все 15 комбинаций применяются сменой атрибутов без reload
- [ ] Alarm tokens идентичны при смене design (assert computed style)
- [ ] DesignSwitcher отсутствует при `NODE_ENV=production` без `NEXT_PUBLIC_DESIGN_PREVIEW=1`
- [ ] Нет white flash (Playwright PW theme + design)

---

## 12. Шрифты — загрузка (s01/s02 note)

| Family | Где | Fallback |
|--------|-----|----------|
| IBM Plex Sans / Mono | next/font/google или self-host | Segoe UI, ui-monospace |
| Source Sans 3 | d02 | IBM Plex Sans |
| JetBrains Mono | d03 | IBM Plex Mono |
| Barlow / Condensed | d05 | IBM Plex Sans |

**Запрет user-rule:** Inter / Roboto / Arial как primary — не используем (plan упоминал Inter как опцию — **отклонено** в пользу Plex/Barlow).

До подключения font files браузер использует fallback — не блокер creative.

---

## 13. Риски и mitigation

| Риск | Mitigation |
|------|------------|
| Путаница chrome teal/brass с alarm | Документ §4; code review: severity только semantic tokens |
| FOUC | blocking script + dark fallback |
| Q9 меняет type scale | provisional; CR-UI-05 правит `--font-*` без смены оси |
| 5 skins раздувают CSS | утилизация после выбора; gzip мелкий |
| d04 слишком тёмный day | сравнить с d01 на реальном мониторе поста |

---

## 14. AC checklist (этот CREATIVE)

- [x] Architecture: CSS variables only (Вариант A)
- [x] Оси `data-design` × `data-theme` разделены
- [x] 5 дизайнов описаны + матрица 5×3 hex
- [x] Общий semantic alarm/quality слой
- [x] CSS файлы на диске для всех 15 chrome-пакетов
- [x] TS types `ThemeTokens` / `DesignId` / `ThemeId`
- [x] Спека ThemeSwitcher + DesignSwitcher (testid, gate, API)
- [x] Правило утилизации после утверждения
- [x] Recommendation provisional default = d01
- [x] Документ на русском, детальный (не telegraph)

---

## Handoff

- **Done:** FRONT CREATIVE CR-UI-01 — architecture A; 5 skins × day/night/dim; tokens CSS + TS types + switcher spec
- **Files:** `memory-bank/front/creative/v1-p1-screens/CR-UI-01-tokens.md`; `frontend/src/styles/tokens/**`; `frontend/src/lib/theme/types.ts`; `frontend/src/lib/theme/switcher-spec.ts`
- **Next:** (1) Пользователь переключает skins после `FRONT IMPLEMENT` s01+s02 и утверждает dNN. (2) Параллельно: `FRONT IMPLEMENT` s01 scaffold-app, затем s02 tokens providers. (3) След. CREATIVE: `FRONT CREATIVE` CR-UI-03 (alarm grammar).
- **Tool / model:** Cursor + fast-editing для s01/s02; Claude Code + premium-coding для CR-UI-03
- **New chat:** yes — CREATIVE закрыт; IMPLEMENT в новом чате

---

## Appendix A — быстрый выбор заказчику

Скажи одну фразу после preview:

- `утверждаем d01` / `d02` / `d03` / `d04` / `d05`

Агент выполнит §10 утилизации отдельной командой (`FRONT TASK` или шаг в IMPLEMENT).
