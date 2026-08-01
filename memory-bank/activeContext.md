## load_now
1. [e07-ws-stream-fanout.yaml](integration/plan/decompose-v1-portal/e07-ws-stream-fanout.yaml) — следующий atomic UI-элемент; AC и contract в shard.
2. [implement-v1-portal/index.md](integration/implement/implement-v1-portal/index.md) — navigation hub INTEG IMPLEMENT (только ссылки).

## Handoff INTEG IMPLEMENT v1-portal — e06
- **Эпик:** T-006 v1-portal · шаги **e01–e06 completed** · pending **e07–e30**.
- **Формат:** INTEG decompose/implement → **YAML** (`epic-decompose/v1`, `epic-implement/v1`) + **checkpoints** в implement для resume loop.
- **Текущий шаг:** e06 Freshness + quarantine chrome — source status banners, null-safe poll timestamps, live WS freshness.
- **Artifact:** [e06-freshness-quarantine.yaml](integration/implement/implement-v1-portal/e06-freshness-quarantine.yaml) `completed`.
- **Проверки:** targeted frontend Vitest PASS (2 files / 9 tests), frontend TypeScript PASS, validate-step PASS, @verify PASS.
- **Изменение кода:** FreshnessController показывает BACK source name/quality для stale/quarantine, принимает nullable `last_poll_ts`, подписан на WS events+values; QuarantineBanner не маскирует состояние как «OK»; Overview timestamp helper null-safe.
- **Следующий:** `INTEG IMPLEMENT` **e07** — WS stream fanout; продолжить в новой сессии.
- **Loop:** `./loop/loop.sh gpt` (без re-arm) · ledger/result обновляется runner; `loop/loop-state.yaml` вручную не изменять.

## done — do NOT load
- [e06-freshness-quarantine.yaml](integration/implement/implement-v1-portal/e06-freshness-quarantine.yaml)
- [e05-statusbar-alarms.yaml](integration/implement/implement-v1-portal/e05-statusbar-alarms.yaml)
- [e04-appshell-chrome.yaml](integration/implement/implement-v1-portal/e04-appshell-chrome.yaml)
- [e03-session-create-logout.yaml](integration/implement/implement-v1-portal/e03-session-create-logout.yaml)
- [e02-login-roster-tiles.yaml](integration/implement/implement-v1-portal/e02-login-roster-tiles.yaml)
