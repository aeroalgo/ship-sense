---
description: integ DECOMPOSE — все eNN за один проход (batch), без стопа на каждом шаге
---

# INTEG DECOMPOSE — Claude Code

Apply `.claude/skills/role-command/SKILL.md` for **INTEG DECOMPOSE**.

**Batch mode (обязательно):**
- Один чат = **весь** decompose (`index.md` + **все** `eNN-*.yaml` из plan)
- **НЕ** останавливаться после e01 / не спрашивать «продолжить e02?»
- **НЕ** использовать skill `executing-plans` (он для IMPLEMENT с checkpoints)
- «Один элемент = один файл» ≠ «один элемент = один ответ с паузой»

Источник: `memory-bank/integration/plan/plan-INTEG-JOURNEY-*` (или `$ARGUMENTS`).
Читай `workflow-decompose.mdc` + isolation `_lean/decompose.mdc`.
Шаблоны: `.cursor/templates/decompose/index.md` + `.cursor/templates/decompose/epic-step.yaml`.

FINISH — один раз, когда все eNN записаны. Next: `INTEG IMPLEMENT e01` в новом чате.

$ARGUMENTS
