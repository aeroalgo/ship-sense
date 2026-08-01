# Program loop — cross-role journey above epic-loop

**Слои:**
- **epic-loop** — одна роль × один `decompose`; next-mode = `loop/transitions.yaml` (+ runner)
- **program-loop** — journey BACK/FRONT/INTEG + GAP fanout + resume
- **loop-state** — канон статусов: `loop/loop-state.yaml` (+ `transitions.yaml`)

Канон epic: `.claude/instructions/epic-loop.md`.  
Канон ledger: `.claude/instructions/loop-state.md`.

## Зачем

После `INTEG GAP` человеку больше не нужно вручную писать `BACK PLAN` → epic → `FRONT PLAN` → `INTEG GAP CLOSE`.  
Program читает queue из `gap-*.md` и сам переключает роль (новая `claude -p` / nested `epic-loop.sh`).

## Фазы

```
INTEG_PLAN → INTEG_DECOMPOSE → INTEG_STEPS
      │              (nested epic INTEG eNN)
      │                    │
      │              next = INTEG GAP
      ▼                    ▼
                 GAP_OPEN (INTEG GAP session)
                       │
                       ▼
                 GAP_FANOUT
            ┌──────────┴──────────┐
            ▼                     ▼
     G-FB* BACK:            G-BF* FRONT:
     PLAN→DECOMPOSE→EPIC    PLAN→DECOMPOSE→EPIC
            │                     │
            └──────────┬──────────┘
                       ▼
                   GAP_JOIN
                       ▼
                   GAP_CLOSE
                       ▼
                 INTEG_RESUME (остаток eNN)
                       ▼
                 INTEG_QA → INTEG_REFLECT → complete
```

`ARCHIVE NOW` — вручную.

## Queue (из gap md)

| Gap ID | Роль work | Порядок |
|--------|-----------|---------|
| `G-FB*` | BACK | сначала |
| `G-BF*` | FRONT | после всех BACK (`after`) |

Статусы item: `pending → plan → decompose → done` (после nested epic).

State: `.claude/runtime/program/state.json` + `queue.json`.

## Handoff contract (machine fields)

После `INTEG GAP` / GAP-PLAN:

```markdown
- **Следующий:** BACK PLAN
- **Program:** GAP_FANOUT
- **Gap:** `memory-bank/integration/gap/<epic_id>/gap-YYYYMMDD-slug.md`
- **Resume:** INTEG GAP CLOSE @memory-bank/integration/implement/…/eNN-….md
```

## Запуск

```bash
# INTEG steps под program (GAP прервёт epic → fanout)
./loop/program-loop.sh --id INTEG-JOURNEY-demo \
  --phase INTEG_STEPS \
  --integ-decompose memory-bank/integration/plan/decompose-demo \
  -m provider/model

# Уже есть gap — сразу fanout
./loop/program-loop.sh --id INTEG-JOURNEY-demo \
  --phase GAP_FANOUT \
  --gap memory-bank/integration/gap/<epic_id>/gap-….md \
  --resume-implement memory-bank/integration/implement/…/e03-….md \
  -m provider/model
```

CLI:

```bash
python3 .claude/hooks/program_resolve.py arm --id … --phase GAP_FANOUT --gap …
python3 .claude/hooks/program_resolve.py status
python3 .claude/hooks/program_resolve.py parse-gap memory-bank/integration/gap/<epic_id>/gap-….md
python3 .claude/hooks/program_resolve.py halt --reason 'manual'
```

## Actions

| kind | Runner |
|------|--------|
| `mode` | одна `claude -p` (PLAN / DECOMPOSE / GAP / GAP CLOSE / QA / REFLECT) |
| `epic` | `./loop/epic-loop.sh --role ROLE decompose` |
| halt/complete | stop |

## Halt

- grill-me / needs_human
- no fingerprint progress (mode)
- nested epic halted
- GAP_FANOUT stuck (blocked / deps)
- max_iterations

## Не делать

- Не смешивать program-политику внутрь `epic_lib.resolve_next`
- Не стартовать BACK/FRONT epic вручную из GAP-сессии — только через queue
- Не крутить несколько eNN/sNN в одной mode-сессии
