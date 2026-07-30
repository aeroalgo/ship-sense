# Claude Code setup ()

Зеркало Cursor workflow. **Single source of truth:** `.cursor/rules/` + `memory-bank/`.

## Быстрый старт

```bash
cd /home/aero/PyProject/ship-sense
claude
/status
```

По умолчанию epic-loop = **headless auto-chain** (s01→s02→… без `/exit`). Для полного UI: `--interactive`.

Команды в чате = slash-команды (1:1). Примеры:

```
BACK PLAN          →  /back-plan
FRONT CREATIVE     →  /front-creative
PM PLAN            →  /pm-plan
IDEA PIPELINE      →  /idea-pipeline
```

## Epic loop (автоцикл decompose)

Fresh session на **каждый** Handoff (IMPLEMENT / CREATIVE / QA / BUGFIX):

```bash
./scripts/epic-loop.sh decompose-v1-p1-pipeline-db-e2e
./scripts/epic-loop.sh decompose-v1-p1-pipeline-db-e2e claude-opus-4-20250514
./scripts/epic-loop.sh decompose-v1-p1-pipeline-db-e2e provider/your-model-id
```

Второй аргумент — **точное** имя для `claude --model` (gateway id, полный API id). Сохраняется в `state.json`.

Slash: `/epic-run` · `/epic-status` · `/epic-halt`  
Канон: `.claude/instructions/epic-loop.md` · state: `.claude/runtime/epic/`

## Все slash-команды (72+)

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
| `/integ-van` | INTEG VAN (brownfield → полная `architecture/`) |
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
| `.claude/instructions/spawn-hard.md` | Политика spawn + packed prompt (Claude Code) |
| `.claude/agents/*.md` | Custom subagents |
| `.claude/hooks/*.py` | Lifecycle hooks: spawn-gate |
| `.claude/settings.json` | Project hooks wiring |
| `.claude/rules/` | Path-scoped доп. правила |
| `.claude/rules/language.md` | **Always-on** — русский язык чата (Layer 0) |
| `.claude/rules/front-tests-parent-only.md` | **Always-on** — frontend-тесты только в parent, never subagent |
| `.claude/settings.json` | permissions + local router env |
| `~/.claude/rules/02-front-tests-parent-only.md` | **Глобально** — frontend-тесты только parent |
| `.venv/bin/graphify` | CLI графа (не в PATH) — из **корня репо**: `query` / `path` / `explain` / `update .` → только `<repo>/graphify-out/` |

## Subagents

Claude Code делегирует через `Agent` как обычно. Overlay (custom):

| Agent | Когда | Как вызвать |
|-------|-------|-------------|
| `explorer` | поиск «где X» другой моделью (haiku) | `@explorer` · GRAPHIFY + ALLOW |
| `verify` | Pre-FINISH IMPLEMENT при code_changed — **обязателен** | `@verify` · AC+/AC−/§0.11/VERIFY |
| `reviewer` | BACK QA после suite — **обязателен** | `@reviewer` · Suite + AC + §0.11 |

Политика: `.claude/instructions/spawn-hard.md`. Hooks: `.claude/hooks/` + `.claude/settings.json`.

## Hooks lifecycle (spawn-gate)

По схеме Claude Code:

```
SessionStart → UserPromptSubmit → … agentic loop …
  PreToolUse(Agent) → [tool] → PostToolUse(Agent)
  SubagentStart → … → SubagentStop
Stop  (gate)
```

| Event | Скрипт | Эффект |
|-------|--------|--------|
| `SessionStart` | `hooks/session-start.py` | EPIC MODE reminder (если epic armed) |
| `UserPromptSubmit` | `hooks/user-prompt.py` | MODE implement/qa + spawn-map (CC делегирует + overlay) |
| `PreToolUse` Agent | `hooks/agent-pretool.py` | HARD RULE; strip worktree/model на overlay; deny секций **только** verify/reviewer |
| `SubagentStart` | `hooks/subagent-start.py` | CONTRACT explorer/verify/reviewer |
| `SubagentStop` | `hooks/subagent-stop.py` | verify/reviewer без `VERDICT` → block |
| `PostToolUse` Agent | `hooks/agent-posttool.py` | фиксирует VERDICT в runtime state |
| `PostToolUse` Bash | `hooks/bash-output-cap.py` | hybrid extract → LLM summary → head/tail |
| `Stop` | `hooks/stop-gate.py` | FINISH без `@verify` / QA без `@reviewer` / QA без Handoff |

State: `.claude/runtime/spawn-gate/<session>.json` · epic: `.claude/runtime/epic/` (gitignore).  
Built-in типы **не** алиасятся и **не** блокируются.

## Local API router

1. `cp .claude/settings.local.json.example .claude/settings.local.json`
2. API key из `http://localhost:20128`

## FINISH

Канон: `.cursor/rules/shared/finish-block.mdc` → `finish-doc-router.mdc` → `/clear` (аналог new chat в Cursor).  
IMPLEMENT: step-файл + Handoff в `activeContext` **до** decompose completed.

**Epic mode:** `/clear` делает `scripts/epic-loop.sh` (exit процесса → новый `-p`), агент сам `/clear` не вызывает.
