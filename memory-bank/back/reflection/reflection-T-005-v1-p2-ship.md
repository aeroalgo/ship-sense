# BACK REFLECT — T-005 / v1-p2-ship

**Дата:** 2026-08-01  
**Уровень:** L4  
**Статус:** completed  
**Основание:** [Epic QA PASS](../qa/v1-p2-ship/qa-20260801-v1-p2-ship.md)  
**Scope:** s01–s20; CR-P2-01..12; reports/warnings, storage, session/access audit, semantic packs, integration/API hardening, I4 runbooks and training materials.

## Сравнение с планом и decompose

План T-005 требовал довести судовой v1 phase 2 до проверяемого backend scope: B12 отчёты и формулы, B13 drift/warnings, I1 read-only gateway и proof artifact, I4 acceptance/runbooks, I5 OTA A/B, I6 RAID/backup, I7 hardening/audit, расширения API, а также интеграционные seams T7/T10. Для критичных неоднозначностей план предусматривал CREATIVE-гейты до реализации, а итоговую проверку — через полный backend suite и reviewer gate.

Decompose выполнен полностью: `s01–s20` имеют завершённые implement-артефакты, все `CR-P2-01..12` закрыты до зависимых шагов, а итоговый QA охватил весь эпик. Human index и implement index сохраняют навигацию по каждому атомарному шагу; machine cursor подтвердил `pending: 0`.

| Плановый блок | Шаги | Фактический итог |
|---|---:|---|
| I1 gateway, proof и read-only boundary | s01, s15 | Gateway contract, proof artifact, T4 evidence и запрет мутаций оформлены и покрыты проверками. |
| B12 engine, formulas, templates и T9 | s02–s05 | ReportEngine, report runs, ship-pack formulas, Jinja templates и golden fixtures согласованы. |
| B13 drift и warnings | s06–s07 | EWMA/trend/ETA semantics, typed warnings REST/WS и stale/quarantine/unknown paths закрыты. |
| Mnemo и reports API | s08–s10 | YAML bindings loader, mnemo endpoints и полный reports surface реализованы с deterministic contracts. |
| Vessel state и setpoints | s11 | APS-first setpoints, mode filter и changelog semantics зафиксированы. |
| I5 OTA A/B | s12 | Typed health gate, anchorage approval, signature/rollback policy и RAUC/U-Boot contract проверены. |
| I6 RAID, backup и I7 hardening | s13–s14, s16 | Degraded storage, backup evidence, role gates, access audit и admin API закрыты fail-closed правилами. |
| T1, T5/T6 и I4 | s17–s19 | Soak/lab harnesses, acceptance runbooks, training cards и sign-off/evidence paths оформлены. |
| Интеграционная hardening-поверхность | s20 | Emulator-shaped reports/warnings seam, T7 rebrowse matrix, T10 six-client replay, OpenAPI p2 и v1 exclusions покрыты. |

### DoD против факта

- **Подтверждено:** полный backend suite `.venv/bin/pytest -q --tb=line` — **580 passed, 12 deselected, 5 warnings, exit 0**.
- **Подтверждено:** reviewer read-only gate завершён с `VERDICT: PASS`; открытых QA issues и blockers нет.
- **Подтверждено:** I4 integration и acceptance runbooks содержат OTA/A-B, read-only gateway, storage/backup, T4/T5/T6/T9/T10, 24h autonomy, discrepancy list и sign-off поля.
- **Подтверждено:** training materials покрывают экраны 1–10, замену ZFS-диска A4, stale/quarantine/unknown и OTA approval в anchorage.
- **Подтверждено:** T7 покрывает added/changed quarantine, removed mapping, unknown tag и stale state; T10 — шесть независимых клиентов, disconnect и cursor replay.
- **Подтверждено:** API/OpenAPI и exclusion checks удерживают additive versioning и не допускают v2/forwarding/ML/AI surface в заявленном scope.
- **Ограничение:** пять предупреждений pytest зафиксированы suite evidence; они не привели к failing/error результату, но требуют отдельного housekeeping, если предупреждения станут release policy.
- **Ограничение:** QA подтверждает backend suite и статические/in-process seams; live vessel, физический OTA, реальное RAID-resilver и продолжительный 24h runtime остаются эксплуатационными acceptance activities из runbooks, а не доказательством текущего shell-прогона.

## Что сработало

1. **Атомарный decompose s01–s20.** Большой судовой scope был разделён по capability boundaries: каждый шаг имел собственную карту файлов, TDD boundary и короткий implement-артефакт. Это сделало прогресс проверяемым и не смешало API, storage, OTA и документацию в один непрозрачный коммитный поток.
2. **CREATIVE до реализации.** CR-P2-01..12 заранее зафиксировали read-only gateway, формулы, report forms, mnemo semantics, роли, tag baseline, RPM/setpoints и OTA/API versioning. Контрактные решения не маскировались fallback-логикой и были доступны зависимым шагам до написания кода.
3. **Fail-closed operational contracts.** Для ролей, OTA health, anchorage approval, storage degradation и quarantine использованы явные typed states и no-go conditions. Это сохранило safety semantics на границе API и runbooks.
4. **Детерминированные тестовые seams.** Emulator-shaped integration path, T7 matrix и T10 reconnect/replay matrix дали воспроизводимую проверку integration behavior без выдачи UI-only или live-vessel claims за runtime evidence.
5. **Финальный полный suite как отдельный QA gate.** После targeted проверок каждого шага результат был проверен полным backend suite, затем reviewer отдельно сопоставил AC+, AC− и §0.11. Это позволило обнаружить и закрыть не только локальные, но и fixture/order-related регрессии.
6. **Явная фиксация evidence и ограничений.** Runbooks требуют timestamp, health gates, rollback/stop conditions, evidence и sign-off. Ограничения live hardware/runtime не скрыты внутри PASS и остаются операционными условиями приёмки.
7. **Ownership и cross-layer contract.** API, integration contract, acceptance materials и training cards используют согласованные пути и названия. В проверенном scope phantom references отсутствуют.

## Проблемы и их разрешение

- **QA-1: изоляция metadata ReportRun.** Первичный полный прогон выявил конфликт метаданных модели при комбинации fixture/import paths. Отдельный `DeclarativeBase` для metadata устранил cross-test coupling; targeted evidence и повторный suite зелёные.
- **QA-2: порядок импорта stop-gate/result fixture.** Тесты зависели от порядка импорта и наличия stub `result.yaml`. Зависимость изолирована, после чего targeted проверки прошли независимо от порядка.
- **QA-3: SQLite fixture для `access_audit`.** API fixture не всегда создавала таблицу audit до raw SQL insert, а UUID не сериализовался для bind. Fixture и writer приведены к явному созданию таблицы и сериализации UUID; session/audit targeted tests и полный suite зелёные.
- **QA-4: semantic vessel fixture.** Fixture содержала неполный набор обязательных tags. Набор приведён к контракту из четырёх обязательных tags; semantic targeted checks и полный suite больше не воспроизводят blocker.
- **Итерационный QA cursor.** Между первичным blocked QA и финальным PASS потребовались отдельные bugfix-сессии. Это подтвердило полезность разделения QA blockers по ID, но также показало, что fixture contract checks нужно запускать раньше полного QA.
- **Предупреждения suite.** Финальный результат содержит пять warnings. Они не блокируют текущий PASS, однако не должны автоматически считаться безопасными для release без отдельной классификации.
- **Live acceptance boundary.** Полный backend suite не заменяет физическую проверку OTA/RAID/24h autonomy. Runbooks это явно отражают; следующий эксплуатационный этап должен собирать отдельные evidence artifacts, а не расширять текущий unit/in-process PASS.

## Уроки

- До реализации крупного backend-эпика фиксировать не только endpoint wire, но и fixture/data contracts: обязательные tags, таблицы audit, metadata ownership и reset semantics.
- Полный suite должен включать независимый запуск наиболее чувствительных fixture-групп до общего прогона; это быстрее выявляет order coupling и уменьшает стоимость финального QA.
- `status`, `verdict`, artifact path и Handoff должны оставаться разными слоями: result.yaml — machine event, QA/reflection shard — evidence, activeContext — session view, loop-state — cursor.
- Документация по live operations должна отделять доказанные in-process checks от hardware/runtime acceptance. PASS нельзя расширять за пределы реально выполненных команд.
- Для API и UI-контрактов additive versioning, cursor replay и quarantine semantics лучше проверять через публичные seams, а не через приватные implementation details.
- Security и safety boundary должна быть fail-closed по умолчанию: неизвестная роль, tag, health state или storage state приводит к явному no-go/quarantine, а не к silent fallback.
- Финальный reviewer полезен именно после полного suite: он проверяет полноту AC− и phantom refs, которые targeted tests не обязаны обнаружить.

## Улучшения процесса

1. В decompose-шаблон добавить обязательную секцию `fixture/data contract` для шагов, меняющих SQLAlchemy metadata, SQLite fixtures, semantic packs или raw SQL.
2. Перед первым полным QA запускать короткий preflight: чистый Python process, targeted fixture groups в независимом порядке, проверка обязательных таблиц/tags и импортов.
3. В QA-артефакте разделять `suite PASS` и `runtime acceptance pending` отдельными строками AC+ и AC−; не смешивать hardware evidence с pytest evidence.
4. Добавить policy для pytest warnings: классификация каждой warning как допустимой, исправляемой или release-blocking с владельцем follow-up.
5. Для следующих ship-эпиков заранее завести отдельные evidence directories для live OTA, RAID replacement/resilver и 24h autonomy; runbook должен ссылаться на конкретные artifact names и retention policy.
6. Сохранить обязательный порядок `artifact → result.yaml → verify/reviewer → Handoff → runner`, чтобы machine cursor не опережал документацию и не появлялись phantom completion states.
7. Для будущего frontend/integration wire использовать `integration/contracts/b10-phase2.md`, QA и reflection как фактические backend inputs, но вести отдельный INTEG GAP для каждой обнаруженной асимметрии.

## Архитектурные заметки

- Backend остаётся read-only фасадом над telemetry/storage repositories и ship-pack YAML; API не становится writer в APS и не мутирует архив телеметрии.
- Reports, warnings, mnemo и vessel state сходятся через typed contracts, а provenance/data-quality/quarantine сохраняются в ответах и acceptance evidence.
- OTA и storage операции имеют отдельные admin boundaries, role checks и audit trail; degraded/no-go state не скрывается агрегатором.
- WebSocket contract использует client-held cursor и replay semantics, что делает reconnect воспроизводимым и совместимым с T10 six-client scenario.
- Runbooks и training являются частью release surface: они описывают не только happy path, но и rollback, stale/quarantine/unknown, degraded storage, discrepancy и sign-off.

## Итог

T-005 / `v1-p2-ship` завершён: s01–s20 и CR-P2-01..12 закрыты, полный backend suite PASS (580 passed, 12 deselected, 5 warnings), reviewer PASS, открытых blockers нет. QA-1..QA-4 устранены и подтверждены повторным suite. Runtime/hardware acceptance ограничения явно сохранены как follow-up evidence, а не выданы за текущий automated PASS. Следующий workflow — `BACK ARCHIVE NOW`; `code_changed` для REFLECT = no.
