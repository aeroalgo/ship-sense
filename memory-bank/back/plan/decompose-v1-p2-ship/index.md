# Реестр шагов (Decompose index)
**Plan ID:** v1-p2-ship  
**План:** [plan-v1-p2-ship.md](../plan-v1-p2-ship.md)  
**Implement index:** [implement-v1-p2-ship/index.md](../../implement/implement-v1-p2-ship/index.md)  
**Дата:** 2026-07-31  
**Режим:** BACK DECOMPOSE  
**Task:** T-005

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали — в `sNN-*.yaml`. Интерфейсы — lean.

> **Policy:** машинный курсор/pending — `loop/loop-state.yaml` (`epic.remaining` + `pending` + `next`). Этот `index.md` — human view (seed remaining один раз). `activeContext.md` — session view.  
> **Канон `needs_creative`:** `.cursor/templates/decompose/epic-step.yaml` — `no` | `yes (CR-…)` | `yes (CR-…) — **closed**` / колонка `yes (CR-…) ✅`. FORBIDDEN: `no (… closed)` · `yes (done)` без CR-ID.

## Skills в контексте

| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность sNN, file map, TDD cycle boundaries |

**Per-step канон:** skills gate — Core + situational из `.cursor/rules/back_developer/skills-gate-situational.mdc` (`workflow-decompose.mdc`). Канон путей — в каждом `sNN`.

## CREATIVE gates — CR-P2-01..12

| ID | Блокирует | Артефакт / статус |
|----|-----------|-------------------|
| CR-P2-01 | s01, s15 | [closed](../../creative/v1-p2-ship/creative-i1-ota-b12.md#cr-p2-01-i1-read-only-gateway) |
| CR-P2-02 | s12, s19 | [closed](../../creative/v1-p2-ship/creative-i1-ota-b12.md#cr-p2-02-i5-ota-a-b) |
| CR-P2-03 | s13 | [✅ closed](../../creative/v1-p2-ship/creative-raid-storage.md) |
| CR-P2-04 | s02, s03, s05 | [closed](../../creative/v1-p2-ship/creative-i1-ota-b12.md#cr-p2-04-b12-formulas-v1) |
| CR-P2-05 | s08, s09 | [✅ closed](../../creative/v1-p2-ship/creative-mnemo-computed.md) |
| CR-P2-06 | s14, s16 | [✅ closed](../../creative/v1-p2-ship/creative-b11-roles.md) |
| CR-P2-07 | s04 | [✅ closed](../../creative/v1-p2-ship/creative-report-forms.md) |
| CR-P2-08 | s06, s07 | [✅ closed](../../creative/v1-p2-ship/creative-b13-tag-set.md) |
| CR-P2-09 | s11 | [✅ closed](../../creative/v1-p2-ship/creative-vessel-rpm.md) |
| CR-P2-10 | s12, s18 | [✅ closed](../../creative/v1-p2-ship/creative-ota-edge.md) |
| CR-P2-11 | s20 | [✅ closed](../../creative/v1-p2-ship/creative-api-versioning.md) |
| CR-P2-12 | s12, s13, s14 | [✅ closed](../../creative/v1-p2-ship/creative-ota-edge.md) |

**Закрыт batch W1:** CR-P2-01, CR-P2-02, CR-P2-04. **Закрыт batch W2:** CR-P2-07. **Закрыт batch W3:** CR-P2-05. **Закрыт batch W4:** CR-P2-10, CR-P2-12. **Закрыт W5:** CR-P2-06.

**Следующая команда:** `BACK IMPLEMENT` @s20. Машинный курсор — `loop/loop-state.yaml` (+ `activeContext.md`). Open creative впереди: нет для s20; CR-P2-11 закрыт.

## Очередь шагов

| step_id | title & files | implement | needs_creative | tdd | next_phase | status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| **s01** | [s01-i1-gateway.md](s01-i1-gateway.md)<br>• I1 Modbus/OPC gateway, logs, compose | [s01…](../../implement/implement-v1-p2-ship/s01-i1-gateway.md) | yes (CR-P2-01) ✅ | yes | BACK IMPLEMENT | **completed** |
| **s02** | [s02-b12-engine-core.md](s02-b12-engine-core.md)<br>• ReportEngine + report_runs | [s02…](../../implement/implement-v1-p2-ship/s02-b12-engine-core.md) | yes (CR-P2-04) ✅ | yes | BACK IMPLEMENT | completed |
| **s03** | [s03-b12-formulas-v1.md](s03-b12-formulas-v1.md)<br>• formulas ship-pack motohours/fuel | [s03…](../../implement/implement-v1-p2-ship/s03-b12-formulas-v1.md) | yes (CR-P2-04) ✅ | yes | BACK IMPLEMENT | completed |
| **s04** | [s04-b12-templates.md](s04-b12-templates.md)<br>• Jinja watch/daily/fuel | [s04…](../../implement/implement-v1-p2-ship/s04-b12-templates.md) | yes (CR-P2-07) ✅ | yes | BACK IMPLEMENT | completed |
| **s05** | [s05-b12-t9-fixtures.md](s05-b12-t9-fixtures.md)<br>• T9 golden fixtures | [s05…](../../implement/implement-v1-p2-ship/s05-b12-t9-fixtures.md) | no | yes | BACK IMPLEMENT | completed |
| **s06** | [s06-b13-drift-engine.md](s06-b13-drift-engine.md)<br>• EWMA DriftEngine | [s06…](../../implement/implement-v1-p2-ship/s06-b13-drift-engine.md) | yes (CR-P2-08) ✅ | yes | BACK IMPLEMENT | completed |
| **s07** | [s07-b13-warnings-api.md](s07-b13-warnings-api.md)<br>• warnings REST+WS | [s07…](../../implement/implement-v1-p2-ship/s07-b13-warnings-api.md) | no | yes | BACK IMPLEMENT | **completed** |
| **s08** | [s08-mnemo-bindings-loader.md](s08-mnemo-bindings-loader.md)<br>• mnemo YAML loader | [s08…](../../implement/implement-v1-p2-ship/s08-mnemo-bindings-loader.md) | yes (CR-P2-05) ✅ | yes | BACK IMPLEMENT | **completed** |
| **s09** | [s09-api-mnemo-endpoints.md](s09-api-mnemo-endpoints.md)<br>• mnemo API+WS | [s09…](../../implement/implement-v1-p2-ship/s09-api-mnemo-endpoints.md) | yes (CR-P2-05) ✅ | yes | BACK IMPLEMENT | completed |
| **s10** | [s10-api-reports-full.md](s10-api-reports-full.md)<br>• reports generate/list/versions | [s10…](../../implement/implement-v1-p2-ship/s10-api-reports-full.md) | no | yes | BACK IMPLEMENT | completed |
| **s11** | [s11-api-vessel-setpoints.md](s11-api-vessel-setpoints.md)<br>• vessel state + setpoints changelog | [s11…](../../implement/implement-v1-p2-ship/s11-api-vessel-setpoints.md) | yes (CR-P2-09) ✅ | yes | BACK IMPLEMENT | completed |
| **s12** | [s12-i5-ota-rauc.md](s12-i5-ota-rauc.md)<br>• OTA A/B sign health gate | [s12…](../../implement/implement-v1-p2-ship/s12-i5-ota-rauc.md) | yes (CR-P2-02, CR-P2-10, CR-P2-12) ✅ | yes | BACK IMPLEMENT | **completed** |
| **s13** | [s13-i6-raid-backup.md](s13-i6-raid-backup.md)<br>• RAID + backup + alerts | [s13…](../../implement/implement-v1-p2-ship/s13-i6-raid-backup.md) | yes (CR-P2-03) ✅ | yes | BACK IMPLEMENT | **completed** |
| **s14** | [s14-i7-hardening-audit.md](s14-i7-hardening-audit.md)<br>• hardening + access_audit | [s14…](../../implement/implement-v1-p2-ship/s14-i7-hardening-audit.md) | yes (CR-P2-06) ✅ | yes | BACK IMPLEMENT | completed |
| **s15** | [s15-i1-proof-artifact.md](s15-i1-proof-artifact.md)<br>• I1 proof PDF + T4 | [s15…](../../implement/implement-v1-p2-ship/s15-i1-proof-artifact.md) | no | yes | BACK IMPLEMENT | completed |
| **s16** | [s16-admin-api-storage-ota.md](s16-admin-api-storage-ota.md)<br>• admin OTA/storage/audit | [s16…](../../implement/implement-v1-p2-ship/s16-admin-api-storage-ota.md) | yes (CR-P2-06) ✅ | yes | BACK IMPLEMENT | completed |
| **s17** | [s17-t1-soak-harness.md](s17-t1-soak-harness.md)<br>• T1 soak harness | [s17…](../../implement/implement-v1-p2-ship/s17-t1-soak-harness.md) | no | yes | BACK IMPLEMENT | completed |
| **s18** | [s18-t5-t6-lab-tests.md](s18-t5-t6-lab-tests.md)<br>• T5/T6 lab automation | [s18…](../../implement/implement-v1-p2-ship/s18-t5-t6-lab-tests.md) | no | yes | BACK IMPLEMENT | **completed** |
| **s19** | [s19-i4-runbook.md](s19-i4-runbook.md)<br>• I4 runbook + training | [s19…](../../implement/implement-v1-p2-ship/s19-i4-runbook.md) | no | no | BACK IMPLEMENT | completed |
| **s20** | [s20-integration-hard.md](s20-integration-hard.md)<br>• E2E + T7/T10 + OpenAPI p2 | [s20…](../../implement/implement-v1-p2-ship/s20-integration-hard.md) | yes (CR-P2-11) ✅ | yes | BACK QA | completed |

**status:** `pending` | `active` | `completed` | `blocked`  
**needs_creative:** `no` | `yes (CR-…)` | `yes (CR-…) ✅`

## Summary-чеклист

- [x] s01 — I1 read-only gateway
- [x] s02 — B12 ReportEngine core
- [x] s03 — B12 formulas v1
- [x] s04 — B12 templates
- [x] s05 — B12 T9 fixtures
- [x] s06 — B13 DriftEngine
- [x] s07 — B13 warnings API
- [x] s08 — mnemo bindings loader
- [x] s09 — mnemo API endpoints
- [x] s10 — reports API full
- [x] s11 — vessel + setpoints changelog
- [x] s12 — I5 OTA
- [x] s13 — I6 RAID/backup
- [x] s14 — I7 hardening/audit
- [x] s15 — I1 proof artifact
- [x] s16 — admin API
- [x] s17 — T1 soak harness
- [x] s18 — T5/T6 lab tests
- [x] s19 — I4 runbook
- [ ] s20 — integration hard

## Порядок (после CREATIVE batch)

`s01` → `s02`→`s03`→`s04`→`s05` → `s06`→`s07` → `s08`→`s09` → `s10`→`s11` → `s12`→`s13`→`s14`→`s15`→`s16` → `s17`→`s18`→`s19` → `s20` → **BACK QA**

Параллель возможна: B12 (s02–s05) ∥ B13 (s06–s07) ∥ mnemo (s08–s09) после закрытия своих CR.

## Handoff (snapshot only)

Канон next / курсора: `loop/loop-state.yaml` + `memory-bank/activeContext.md`.

- **Next:** `BACK IMPLEMENT` @s20
- **load_now:** `memory-bank/back/plan/decompose-v1-p2-ship/s20-integration-hard.md`
- **INTEG GAP вход:** этот index + implement index после QA pass (только когда s01–s20 completed)
