---
description: LOOP RUN — единый автоцикл (epic или INTEG journey)
---
Единая точка: `./loop/loop.sh`. Гайд: `loop/WORKFLOW.md`. Pointer: `.claude/instructions/loop-state.md`.

Скажи пользователю выйти из сессии и в терминале:

```bash
./loop/loop.sh decompose-v1-p2-ship YOUR_MODEL
./loop/loop.sh YOUR_MODEL
./loop/loop.sh --id INTEG-JOURNEY-… --phase GAP_FANOUT \
  --gap memory-bank/integration/gap/…/gap-….md \
  --resume-implement memory-bank/integration/implement/…/eNN.md \
  -m YOUR_MODEL
```

$ARGUMENTS
