---
description: EPIC STATUS — состояние автоцикла decompose
---
Покажи статус epic loop:

```bash
python3 .claude/hooks/epic_resolve.py status
```

Выведи кратко: `active`, `status`, `decompose`, **`model`** (если задан), `iteration`, `last_command`, `halt_reason`.

Если `active` и есть `next-prompt`:

```bash
python3 .claude/hooks/epic_resolve.py resolve; echo exit:$?
```

Не запускай `./loop/epic-loop.sh` из этой команды.
$ARGUMENTS
