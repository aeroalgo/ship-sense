---
description: EPIC RUN — автоцикл decompose (fresh session на каждый Handoff)
---
Arm epic loop for a decompose index, then run the external fresh-session runner.

**Аргумент:** id или путь decompose, напр. `decompose-v1-p1-pipeline-db-e2e` или `memory-bank/back/plan/decompose-v1-p1-pipeline-db-e2e`

Сделай сейчас (parent):

```bash
python3 .claude/hooks/epic_resolve.py arm "$ARGUMENTS" --role BACK
python3 .claude/hooks/epic_resolve.py status
```

Потом скажи пользователю **выйти из этой сессии** и в терминале (корень репо):

```bash
./scripts/epic-loop.sh decompose-v1-p1-pipeline-db-e2e YOUR_EXACT_MODEL_ID
# или сразу с arm:
# ./scripts/epic-loop.sh decompose-v1-p1-pipeline-db-e2e provider/your-model-id
```

Каждая итерация = новый `claude -p` (чистый контекст). Handoff → следующая команда (IMPLEMENT|CREATIVE|QA|BUGFIX). Halt: QA blocked без BUGFIX, grill-me, no progress, stop×3 без FINISH.

Статус / стоп:

```bash
python3 .claude/hooks/epic_resolve.py status
python3 .claude/hooks/epic_resolve.py halt --reason 'manual'
```

Канон: `.claude/instructions/epic-loop.md`
$ARGUMENTS
