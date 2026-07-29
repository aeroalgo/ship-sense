# Claude Code setup ()

Зеркало Cursor workflow. **Single source of truth:** `.cursor/rules/` + `memory-bank/`.

## Быстрый старт

```bash
cd /home/aero/PyProject/
claude
/status
```

Команды в чате = slash-команды (1:1). Примеры:

```
BACK PLAN          →  /back-plan
FRONT CREATIVE     →  /front-creative
PM PLAN            →  /pm-plan
IDEA PIPELINE      →  /idea-pipeline
```

## Все slash-команды (72)

### BACK (12)

| Slash | Chat |
|-------|------|
| `/back-van` | BACK VAN |
| `/back-plan` | BACK PLAN |
| `/back-decompose` | BACK DECOMPOSE |
| `/back-creative` | BACK CREATIVE |
| `/back-implement` | BACK IMPLEMENT |
| `/back-task` | BACK TASK |
| `/back-bugfix` | BACK BUGFIX |
| `/back-refactor` | BACK REFACTOR |
| `/back-qa` | BACK QA |
| `/back-security` | BACK SECURITY |
| `/back-reflect` | BACK REFLECT |
| `/back-archive` | BACK ARCHIVE NOW |

### FRONT (12)

| Slash | Chat |
|-------|------|
| `/front-van` | FRONT VAN |
| `/front-plan` | FRONT PLAN |
| `/front-decompose` | FRONT DECOMPOSE |
| `/front-creative` | FRONT CREATIVE |
| `/front-implement` | FRONT IMPLEMENT |
| `/front-task` | FRONT TASK |
| `/front-bugfix` | FRONT BUGFIX |
| `/front-refactor` | FRONT REFACTOR |
| `/front-qa` | FRONT QA |
| `/front-security` | FRONT SECURITY |
| `/front-reflect` | FRONT REFLECT |
| `/front-archive` | FRONT ARCHIVE NOW |

### INTEG (3+)

| Slash | Chat |
|-------|------|
| `/integ-gap` | INTEG GAP (алиас INTEGRATION GAP; rewrite §Gaps → link) |
| `/integ-gap-close` | INTEG GAP CLOSE (follow links + rewire) |
| `/integ-plan` | INTEG PLAN (SUSPENSION GUARD — plan unlimited) |
| `/integ-decompose` | INTEG DECOMPOSE (batch: все eNN за один проход) |
| `/integ-security` | INTEG SECURITY |

Остальные INTEG-команды — через chat (`INTEG IMPLEMENT`, …); slash — по мере добавления в `.claude/commands/`.

### IDEA PIPELINE (4)

| Slash | Chat |
|-------|------|
| `/idea-pipeline` | IDEA PIPELINE |
| `/idea-pipeline-continue` | IDEA PIPELINE CONTINUE |
| `/idea-pipeline-finish` | IDEA PIPELINE FINISH |
| `/idea-pipeline-status` | IDEA PIPELINE STATUS |

### PM (12) — архив `_archive/cursor-rules/project_manager/`

`/pm-init` `/pm-discover` `/pm-discover-market` `/pm-plan` `/pm-roadmap` `/pm-backlog` `/pm-sprint-plan` `/pm-jira` `/pm-status` `/pm-session` `/pm-retro` `/pm-archive`

### TL (6) — архив `team_lead/`

`/tl-standup` `/tl-sprint` `/tl-delivery` `/tl-blockers` `/tl-capacity` `/tl-sync-dev`

### CONTENT (8) — архив `content_growth/`

`/content-init` `/content-plan` `/content-write` `/content-seo` `/content-audit` `/content-launch` `/content-optimize` `/content-interview`

### MARKETING (8) — архив `marketing_growth/`

`/marketing-plan` `/marketing-ads` `/marketing-email` `/marketing-monetize` `/marketing-retain` `/marketing-social` `/marketing-pr` `/marketing-revops`

### SEO (9) — архив `seo_ops/`

`/seo-tech` `/seo-local` `/seo-links` `/seo-geo` `/seo-content-ops` `/seo-ecommerce` `/seo-data` `/seo-competitors` `/seo-aso`

## Что куда

| Файл | Роль |
|------|------|
| `CLAUDE.md` | Layer 0 + imports token-economy + mainrule |
| `.claude/skills/role-command/` | Цепочка всех role commands (Step 0 = graphify для code modes) |
| `.claude/commands/*.md` | Slash-команды (по одной на режим) |
| `.claude/rules/` | Path-scoped доп. правила |
| `.claude/rules/language.md` | **Always-on** — русский язык чата (Layer 0) |
| `.claude/rules/front-tests-parent-only.md` | **Always-on** — frontend-тесты только в parent, never subagent |
| `.claude/settings.json` | permissions + 9router env |
| `~/.claude/rules/02-front-tests-parent-only.md` | **Глобально** — frontend-тесты только parent |
| `.venv/bin/graphify` | CLI графа (не в PATH) — из **корня репо**: `query` / `path` / `explain` / `update .` → только `<repo>/graphify-out/` |

## 9router

1. `cp .claude/settings.local.json.example .claude/settings.local.json`
2. API key из `http://localhost:20128`

## FINISH

`## Handoff` в artifact + `/clear` (аналог new chat в Cursor).
