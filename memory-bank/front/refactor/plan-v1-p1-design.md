# Plan — RF-UI-01 design-only

**Analysis:** [analysis-v1-p1-design.md](./analysis-v1-p1-design.md)

## Priority Critical → Low

1. **Critical** — `motion.css`: убрать `html *`; scoped theme transition + `--ease-out`
2. **Critical** — `ds-interactive.css` + import в `globals.css`: press / focus / cursor / touch-action для `button`, `a`, `[role="button"]`
3. **Critical** — replace visible `—` → `-` / `:` / rephrase (src only; storybook fixtures optional)
4. **High** — `next/font` IBM Plex Sans + Mono → CSS vars; override `--font-*` after skins
5. **High** — `minHeight: 100vh` → `100dvh` (AppShell, LoginPage)
6. **Medium** — `typography.css`: tabular nums for mono, h1–h3 `text-wrap: balance`
7. **Medium** — `--accent: var(--chrome-accent)` в semantic layer
8. **Low** — Login: brand line «ShipSense» + copy без em-dash

## Self-check

- [ ] CR-UI-01 hex/skins не ломаем  
- [ ] testids / behavior без изменений  
- [ ] Vitest green after  
- [ ] Design skills applied (product HMI, not landing)

## Execute order

CSS (motion, interactive, typography, fonts, accent) → copy strings → layout font wire → tests.
