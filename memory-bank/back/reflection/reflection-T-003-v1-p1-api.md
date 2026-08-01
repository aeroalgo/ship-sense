# BACK REFLECT — T-003 / v1-p1-api

**Дата:** 2026-07-31  
**Уровень:** L3–L4  
**Статус:** completed  
**Основание:** [Epic QA PASS](../qa/v1-p1-api/qa-20260731-v1-p1-api.md)  
**Scope:** s01–s10; CR-API-01..05; API REST/WS, B11 session, reports, health/sources/rate, I1/OpenAPI, storage contract boundary и compose configuration.

## Сравнение с планом и decompose

План T-003 требовал единую read-only точку данных для UI фазы 1: B10 REST для медленных запросов, WebSocket для realtime и B11 для входа оператора. API должен читать TimescaleDB/Postgres и ship-pack YAML, не писать в АПС и не мутировать архив телеметрии.

Decompose закрыт полностью: `s01–s10` имеют завершённые implement-артефакты, а CREATIVE-гейты `CR-API-01..05` закрыты до зависимых шагов.

| Блок | Шаги | Итог |
|------|------|------|
| Scaffold и контракты | s01 | FastAPI factory, envelope, DI, OpenAPI и runtime wiring |
| Дерево и telemetry reads | s02–s05 | assets tree, aggregate status, series/downsample, events cursor/keyset, setpoints из YAML |
| Realtime и session | s06–s07 | WS fanout/ring/bridge, roster и session lifecycle с HttpOnly cookie и B6 audit events |
| Reports и operational reads | s08–s09 | reports catalog/watch JSON+HTML, deterministic verdict/data-quality, health/sources и rate limit |
| Hardening и audit | s10 | I1 static import denylist, mutation audit, quarantine example/disclaimer и OpenAPI completeness |

### DoD против факта

- **Подтверждено:** storage contract suite — 82 passed.
- **Подтверждено:** backend non-slow suite — 453 passed, 9 deselected, 3 warnings.
- **Подтверждено:** API regression входит в зелёный non-slow scope.
- **Подтверждено:** numeric storage payloads принимаются, non-numeric payload отклоняется.
- **Подтверждено:** `DATABASE_URL`, `SHIPSSENSE_WRITER_ENDPOINT`, writer TCP `9009` и compose names `db`/`writer` согласованы статически с §0.11.
- **Подтверждено:** reviewer read-only gate завершён с PASS; обязательных исправлений не найдено.
- **Ограничение:** slow/full suite в этой QA-сессии отдельно не выполнялся; 9 slow-тестов deselected.
- **Ограничение:** live `docker compose` smoke не запускался; compose wiring проверен статически и не выдаётся за runtime evidence.
- **Ограничение:** отдельные lint/type/security CLI-инструменты не входят в настроенный QA scope.

## Что сработало

1. Разделение на атомарные sNN позволило закрыть широкий API scope последовательно, сохранив targeted TDD-проверки перед эпиковой QA.
2. CREATIVE batch до зависимых реализаций снял критичные контрактные разночтения по downsample, WS fanout, session lifecycle, cursor и reports.
3. Read-only граница API сохранена: storage и ship-pack используются как источники данных, а I1/OpenAPI audit проверяет отсутствие запрещённых импортов и мутаций.
4. Функциональный scope проверен двумя уровнями: storage contracts и backend non-slow regression; reviewer отдельно подтвердил AC+, AC− и §0.11.
5. Согласование runtime-путей и compose-переменных после RF-01 сохранило единый ownership `apps/api` и не оставило phantom refs в проверенном scope.

## Проблемы и их разрешение

- На старте эпика контрактные решения для нескольких зависимых API-частей ещё требовали фиксации. Это разрешено отдельными `CR-API-01..05` до реализации зависимых шагов, без silent fallback.
- Ширина эпика потребовала финального s10 для I1/OpenAPI и mutation audit; перенос hardening в последний шаг сохранил основной delivery path, но сделал его обязательным gate перед QA.
- QA evidence не включает slow/full и live compose scopes. Это не blocker для заявленного non-slow PASS, но ограничение должно оставаться видимым до отдельного runtime-прогона.

## Уроки

- Для API-эпика сначала фиксировать wire-контракты CREATIVE-гейтами, затем реализовывать зависимые endpoints; это дешевле, чем исправлять расхождения после полной сборки.
- Non-slow regression green не равен terminal green для полного backend scope: deselected slow tests должны быть явно отражены в verdict.
- Статическая проверка compose-конфигурации подтверждает wiring, но не заменяет live smoke с health и runtime logs.
- I1 import/mutation audit и OpenAPI completeness полезно держать отдельным финальным шагом, чтобы проверять фактическую поверхность после всех endpoint-изменений.
- Storage contract boundary должна оставаться частью API QA: она предотвращает расхождение между числовыми telemetry payloads и API-ожиданиями.

## Улучшения процесса

1. В планах API-эпиков заранее выделять два явных QA-профиля: обязательный non-slow regression и отдельный full/slow + live compose acceptance.
2. В Epic QA checklist закрепить live compose smoke с health endpoints, чистыми runtime logs и проверкой writer/database connectivity; статический §0.11 оставить отдельным пунктом.
3. Сохранять path/ownership amendment (`apps/api`) в plan и decompose до первого implement-шарда, чтобы не тратить финальные шаги на исправление маршрутов.
4. Подготовить доступные lint/type/security инструменты или явно зарегистрировать отдельный follow-up TASK, не смешивая их отсутствие с PASS текущего scope.
5. Для следующего frontend/integration wire использовать этот implement index и QA-артефакт как источник фактических REST/WS/session контрактов, а не как замену отдельному INTEG GAP.

## Архитектурные заметки

- API остаётся read-only фасадом над storage repositories и ship-pack YAML; writer/Timescale — upstream boundary, не обязанность B10/B11.
- REST покрывает snapshot/series/events/setpoints/assets/reports/health reads, WebSocket — realtime fanout, B11 — operator session и B6 audit trail.
- Quarantine example и explicit README disclaimer оставляют I1-ограничения видимыми и не маскируют запрещённую мутацию под обычный API path.
- Следующая интеграционная работа должна проверить frontend consumption этих REST/WS контрактов и отдельно зафиксировать отсутствующие live/runtime acceptance gaps.

## Итог

T-003 / `v1-p1-api` завершён: s01–s10 и CR-API-01..05 закрыты, Epic QA PASS для storage и backend non-slow scope, reviewer PASS, обязательных blockers нет. Ограничения slow/full и live compose smoke зафиксированы как AC−, а не скрыты. Следующий workflow — `BACK ARCHIVE NOW`; `code_changed` для REFLECT = no.
