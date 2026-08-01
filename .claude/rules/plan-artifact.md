---
paths:
  - "memory-bank/**/plan-*.md"
  - "memory-bank/**/gap/gap-*.md"
  - "memory-bank/**/plan-*-GAP-*.md"
  - "memory-bank/back/plan/plan-*.md"
  - "memory-bank/front/plan/plan-*.md"
  - "memory-bank/integration/plan/plan-*.md"
  - "memory-bank/**/security/plan/plan-*.md"
  - "memory-bank/**/refactor/plan/plan-*.md"
  - "memory-bank/architecture/**"
---

# PLAN / GAP / ARCHITECTURE artifacts — NO OUTPUT ECONOMY

When creating or editing files matching these paths:

## Absolute rules

1. **Token economy / telegraph / «max 3 sentences» / 200-line caps DO NOT APPLY** to this file.
2. **Chat brevity does not limit** this file. Short reply to user ≠ short plan/map.
3. **Lean load ≠ lean write.** Context may stay focused; this artifact must be exhaustive.
4. Truncating «для экономии контекста / токенов» = **FAIL**. Rewrite longer.

## Minimum bar (architecture — `memory-bank/architecture/**`)

- Brownfield VAN must produce real as-built content, not stubs-only
- Required mermaid: service interaction + data-flow; ERD or explicit `erd: n/a`
- Missing layer → explicit `absent` / `n/a`, never silent omit
- Session van log stays thin; detail lives in architecture shards

## Minimum bar (INTEG GAP — `gap-*.md`)

- **FAIL** if only parity matrix / ID table without executable work
- Required per every `G-BF*` / `G-FB*`: as-is asymmetry → what BACK/FRONT/INTEG must do → done checkboxes (шаблон `.cursor/templates/integration-gap.md` §«Работы по gap»)
- Medium detail OK (full AC/wire may live in `plan-*-GAP-*`); gap itself must still be actionable without re-reading implement bullets

## Minimum bar (INTEG portal plan)

If scope is portal/journey / file is `plan-INTEG-*`:

- **Hard FAIL** if artifact is TOC-only (registry table + short rollout without per-element detail)
- Prefer **≥400 lines** OR equivalent density: every UI element gets its own subsection (§UI, §API today, §Contract outline, §wire, §tests) — not one mega-table alone
- Every `frontend/src/app/**/page.tsx` route must appear
- Guides (`/guides`, `/guides/[slug]`) required
- API today must use ✅ / ⚠️ mock / ❌ missing honestly (not all ✅)
- Rollout must use **eNN** element steps, not layer s01-migration / s02-endpoint

## After Write

Run `wc -l` on the plan file. If under acceptance bar → expand before FINISH. Do not declare done.
For architecture shards: verify mermaid blocks exist before FINISH.
