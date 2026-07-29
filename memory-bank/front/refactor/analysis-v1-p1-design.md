# Analysis — FRONT REFACTOR design-only (v1 p1 screens)

**ID:** RF-UI-01  
**Дата:** 2026-07-26  
**Scope:** только визуал / design stack (workflow-implement A∪B design). Без смены API, WS, data flow.  
**Канон:** CR-UI-01 tokens (preserve). ui-ux-pro-max indigo/Inter **отклонён** (конфликт с HMI skins).

## Design Read

Reading this as: **ship-bridge HMI** for watch officers, redesign-preserve of CR-UI-01, product register (impeccable), dials VARIANCE 3 · MOTION 2 · DENSITY 9.

## Skills Read

frontend-design · design-taste-frontend · emil-design-eng · impeccable (product) · high-end-visual-design (restrained for HMI) · ui-ux-pro-max (density/a11y only)

## Findings (severity)

| Sev | Issue | Where | Skill |
|-----|-------|-------|-------|
| Critical | `html *` transitions на все свойства | `motion.css` | emil / perf |
| Critical | Нет `:active` / `:focus-visible` на DS controls | LoginTile, StatusBar, ThemeSwitcher, StateShell, SessionChip, AppNav… | emil / ui-ux |
| Critical | Em-dash `—` в user-visible copy | Login, banners, watch, overview empty, loading msgs | design-taste 9.G |
| High | IBM Plex в токенах, шрифт не грузится | `layout.tsx` / designs | next/font, FOIT |
| High | `100vh` вместо `100dvh` | AppShell, LoginPage | design-taste |
| Medium | Пустой `typography.css` | tokens | impeccable product |
| Medium | `--accent` не задан (nav fallback) | AppNav | tokens |
| Low | Слабый brand signal на login (product OK) | LoginPage | frontend-design |

## Emil review (Before / After)

| Before | After | Why |
| --- | --- | --- |
| `html * { transition: background-color, color, … }` | theme transition только на `html` / `body` / chrome surfaces | `*` = layout thrash; theme swap не нужен на каждом leaf |
| `ease` на theme | `cubic-bezier(0.23, 1, 0.32, 1)` | punch; ease-out для enter/theme |
| Нет `:active` на button | `transform: scale(0.97)` 160ms | press feedback |
| Нет `:focus-visible` | `outline: 2px solid var(--focus-ring)` | a11y keyboard |
| Em-dash в copy | hyphen / colon / period | AI tell ban |

## Out of scope

- CR-UI-05 / Q9 финальная typography density  
- Снос 4 skins (ждём утверждения)  
- Logic / API / Playwright suite s16  
- Marketing/landing patterns (glass, bento, hero choreography)

## Baseline tests

Vitest 102 passed (2026-07-26) before changes.
