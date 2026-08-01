## load_now
1. [e06-freshness-quarantine.yaml](integration/plan/decompose-v1-portal/e06-freshness-quarantine.yaml) — следующий atomic UI-элемент; AC и contract в shard.
2. [implement-v1-portal/index.md](integration/implement/implement-v1-portal/index.md) — navigation hub INTEG IMPLEMENT (только ссылки).

## Handoff INTEG IMPLEMENT v1-portal
- **Эпик:** T-006 v1-portal · шаги **e01–e05 completed** · pending **e06–e30**.
- **Формат:** INTEG decompose/implement → **YAML** (`epic-decompose/v1`, `epic-implement/v1`) + **checkpoints** в implement для resume loop.
- **Текущий шаг:** e05 StatusBar alarms — bootstrap alarm/warning events, StatusBar chips, journal deep-link и live WS events.
- **Artifact:** [e05-statusbar-alarms.yaml](integration/implement/implement-v1-portal/e05-statusbar-alarms.yaml) `completed`.
- **Проверки:** targeted frontend Vitest PASS (2 files / 2 tests), frontend TypeScript PASS, `validate-step` PASS, `@verify` PASS.
- **Изменение кода:** `frontend/src/features/shell/useStatusBarAlarms.ts` теперь запрашивает `severity[]=alarm&severity[]=warning` и принимает оба severity в live WS.
- **Следующий:** `INTEG IMPLEMENT` **e06** — Freshness + quarantine; продолжить в новой сессии.
- **Loop:** `./loop/loop.sh gpt` (без re-arm) · ledger/result обновляется runner; `loop/loop-state.yaml` вручную не изменять.

## done — do NOT load
- [e05-statusbar-alarms.yaml](integration/implement/implement-v1-portal/e05-statusbar-alarms.yaml)
- [e04-appshell-chrome.yaml](integration/implement/implement-v1-portal/e04-appshell-chrome.yaml)
- [e03-session-create-logout.yaml](integration/implement/implement-v1-portal/e03-session-create-logout.yaml)
- [e02-login-roster-tiles.yaml](integration/implement/implement-v1-portal/e02-login-roster-tiles.yaml)
- [e01-home-redirect.yaml](integration/implement/implement-v1-portal/e01-home-redirect.yaml)
