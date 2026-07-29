# Kilo spawn baseline — 2026-07-29

Baseline **до** политики parent-self + mandatory verify.  
Сравнивать после N новых сессий: `.kilo/metrics/spawn-compare-YYYY-MM-DD.md`.

**Источник:** `~/.local/share/kilo/kilo.db` (root sessions `parent_id IS NULL`).  
**Активное время:** span `message.time_created` (не wall `session.time_updated`).

## Политика на момент baseline (до правки)

- luna description: «MUST spawn Flash subagents»
- spawn-hard: L1–L2 parent сам предпочтительно; storage s08–s11 без worker
- Новые agents (`test-writer`/`refactor`/`bugfix`/`verify`) уже добавлены, но **verify не был mandatory**

## 10 последних root-сессий (snapshot)

| # | Start | Agent | Тип | Children | Active | Parent in | Child reason | Pytest | Итог |
|---|-------|-------|-----|----------|--------|-----------|--------------|--------|------|
| 1 | 16:44 | luna | s09 WriterService | 0 | 4.1m | 2.07M | — | 2 | PASS FINISH |
| 2 | 14:21 | luna | s08 TimeAxis дожим | 4 (3w+1r) | 8.6m | 2.28M | 55.7k | 4 | PASS (после REJECT) |
| 3 | 13:54 | luna | s08 TimeAxis старт | 7 (4w+ex+ex+r) | 15.4m | 2.35M | 29.1k | 3 | FAIL (не тот файл) |
| 4 | 06:27 | code | MQTT s04 | 0 | 5.7m | 1.86M | — | 0 | PASS |
| 5 | 06:35 | code | MQTT s05 | 0 | 6.4m | 3.09M | — | 0 | PASS |
| 6 | 06:50 | luna | BACK QA MQTT | 1 (reviewer) | 10.9m | 2.32M | 20.1k | 3 | FAIL blocked |
| 7 | 07:22 | luna | bugfix cross-pkg | 6 (3ex+2w+1r) | 34.3m | 3.83M | 73.0k | 7 | long loop |
| 8 | 08:25 | glm | MQTT s06 | 0 | 6.1m | 2.27M | — | 0 | PASS |
| 9 | 08:33 | grok | MQTT s07 docs | 0 | 16.5m | 2.74M | — | 0 | PASS |
| 10 | 08:58 | luna | BACK QA MQTT | 2 (explorer) | 25.9m | 2.49M | 16.3k | 9 | PASS 327 tests |

## Aggregates

| Метрика | Значение |
|---------|----------|
| Sessions | 10 |
| With spawn | 5 (50%) |
| No spawn | 5 (50%) |
| Total children | 20 |
| Child step-limit hits | 4 (20% children) |
| Avg active (spawn) | 19.0 min |
| Avg active (no-spawn) | 7.8 min |
| Avg child reason (spawn) | 38.8k tokens |
| luna spawn rate | 83% (5/6) |
| code/glm/grok spawn rate | 0% (0/4) |

## IMPLEMENT subset

| Подтип | n | Spawn | Avg active | Success |
|--------|---|-------|------------|---------|
| Storage L1–L2 (s08–s09) | 3 | 11 on s08, 0 on s09 | 4m (s09) vs ~12m (s08) | s09 PASS; s08 = 1 FAIL + 1 дожим |
| MQTT/scripts (code/glm/grok) | 4 | 0 | 8.7m | 4/4 PASS |

## Антипаттерны (зафиксированы)

1. explore при paths в shard → step limit, parent всё равно сам (#3)
2. worker chain >1 на один AC → step limits (#2, #3)
3. reviewer без packed AC → OK не по тому файлу (#3)
4. «MUST spawn» на luna → 83% spawn, худшие сессии с max spawn (#3, #7)

## Что работало

1. Parent-self TDD storage (#1 s09: 4.1m, 2 tests, FINISH)
2. Parent-self MQTT (#4,5,8,9: 0 spawn, all PASS)
3. Reviewer ловит blockers (#2 REJECT → fix)
4. Explorer на QA — PASS, но дорого (#10: 26m)

## Target после правки (для compare)

| Метрика | Target |
|---------|--------|
| IMPLEMENT L1–L2 spawn rate | ≤20% (только verify / bugfix) |
| Avg active IMPLEMENT | ≤8 min |
| Child step-limit rate | ≤5% |
| `task→verify` before FINISH | ≥80% IMPLEMENT sessions |
| explore on L1–L2 with paths | 0 |
| worker chain >1 on same AC | 0 |

## Как снимать следующий snapshot

```bash
# из корня репо / с доступом к kilo.db
python3 - <<'PY'
# скопировать/адаптировать скрипт из chat 2026-07-29
# писать .kilo/metrics/spawn-compare-YYYY-MM-DD.md
# сравнить с этой baseline-таблицей
PY
```

Session IDs (root, newest first):

1. `ses_051e10c77ffeYRudpww3tcidGj`
2. `ses_052647b42ffe8y2BQ6JURybudy`
3. `ses_0527d310dffemHFf88ukOhLw23`
4. `ses_054169af6ffeMweD0cGT5M1Agb`
5. `ses_0540edfd0ffednjd4gTo19yob4`
6. `ses_05400d816ffeDEGJJCJpGD3a3A`
7. `ses_053e415edffeKBJvcISS9Kqd1O`
8. (glm s06 — см. kilo.db `ORDER BY time_updated DESC LIMIT 10`)
9. (grok s07)
10. (luna QA PASS)
