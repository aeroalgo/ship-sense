# BACK REFLECT — T-008 / v1-p1-mqtt

**Дата:** 2026-07-30  
**Уровень:** L4  
**Статус:** completed  
**Основание:** core QA fail→fix (R-1 Topic) · smoke [QA PASS](../../archive/back/qa/v1-p1-mqtt-smoke/qa-20260729-v1-p1-mqtt-smoke.md) после [BUGFIX ENTRYPOINT](../../archive/back/bugfix/v1-p1-mqtt-smoke/bugfix-20260729-mqtt-smoke-emulator-entrypoint.md); earlier [qa-20260728](../../archive/back/qa/v1-p1-mqtt/qa-20260728-t008-mqtt.md)  
**Scope:** s01–s12 + mqtt-smoke gap-close; CR-COL-05

## Сравнение с планом и decompose

План L4: третий source plugin `mqtt` для боевого пути Канонерки (две панели), native lifecycle→Event без bitfield reconstruction, I3 MQTT publisher, health, compose `mqtt-dev`. Writer/API — стык, не scope.

Decompose s01–s12 — **done**:

| Блок | Шаги | Итог |
|------|------|------|
| Config/client | s01–s02 | MqttSourceConfig + publish guard; aiomqtt wrapper |
| Semantic (CR-COL-05) | s03–s06, s10 | payload models, lifecycle tracker, mapper, connector, normalizer bridge (no EventDetector reconstruct) |
| Maps/emulator | s07–s08 | channel maps stub; I3 MqttPublisher |
| Prove | s09, s11–s12 | Mosquitto E2E; health fields; compose profile |
| Smoke gap | plan-v1-p1-mqtt-smoke | single/dual/events/sigterm green после ENTRYPOINT fix |

**DoD vs факт:** PluginRegistry `mqtt`, N≥2 isolation, subscribe-only guard, lifecycle→Event native, analog/discrete/EGT mapping, emulator publisher, health, mqtt-dev compose — закрыты evidence suite/smoke. Broker placement / prod ACL Канонерки — вне day-1 (dev ACL `shipsense/#` noted). Journal UI banner (AC-MQTT-20) — T-003 downstream.

Ограничение: QA-артефакт smoke содержит и PASS-шапку, и хвост старого BLOCKED — канон статуса = log/tasks (**PASS** после BUGFIX), не хвост файла.

## Что сработало

1. CREATIVE CR-COL-05 до semantic stack (s03–s06, s10) зафиксировал native lifecycle mode A и границы B4.
2. Reuse B1 (`SourceConnector` / supervisor / queues) без форка ядра — MQTT как peer Modbus/OPC.
3. TDD на R-1 (`aiomqtt.Topic`→`str`) вернул silent drop сообщений в явный failing unit до E2E green.
4. Отдельный smoke harness (`smoke-mqtt-stack.sh`) + modes single/dual/events/sigterm дали compose evidence без смешения с Modbus day-1 stack.
5. BUGFIX ENTRYPOINT: compose `command` vs image `ENTRYPOINT` — классика Docker; fail-loud в логах emulator (`unrecognized arguments`).

## Проблемы и их разрешение

- **R-1 Topic type:** `_dispatch_message` принимал только `str` → сообщения discard; normalize `str(topic)` + bytes payload.
- **Smoke circular import (ранний QA):** lazy import / tree fix; на BUGFIX-сессии уже не воспроизводился — истинный блокер оказался ENTRYPOINT.
- **emulator-mqtt ENTRYPOINT:** `python -m emulator` + mqtt_publish argv → restart loop; `entrypoint: ["python", "-m", "emulator.mqtt_publish"]`.
- **dual health via `compose run`:** ENTRYPOINT collector глотал probe; → `exec -T`.
- **PYTHONPATH / deps:** full root pytest без path падает; канон — `PYTHONPATH=apps/edge/...` + `.venv` (R-3 note).

## Уроки

- Внешние SDK типы (`aiomqtt.Topic`) проверять unit-тестом на границе wrapper, не полагаться на «topic is str» из доков.
- Compose smoke: всегда явно задавать `entrypoint` для alternate `__main__` модулей в том же image.
- Не диагностировать «circular import» как sole root cause, пока контейнер publisher не healthy и логи не прочитаны.
- Gap-close smoke держать рядом с epic (отдельный plan_id), но закрывать тем же T-xxx до REFLECT/ARCHIVE.
- QA-файл: при re-QA **переписывать** verdict/blockers целиком — не оставлять старый FAIL хвост под PASS шапкой.

## Улучшения процесса

1. Шаблон compose service для multi-entrypoint images: checklist entrypoint/command/health probe (`run` vs `exec`).
2. В IMPLEMENT s09 добавлять contract-тест на тип topic/payload сразу после выбора MQTT client lib.
3. После smoke BUGFIX — обязательный re-QA rewrite одного канонического qa-файла (без противоречивых секций).
4. При ARCHIVE T-008: перенести `v1-p1-mqtt` + связанные `v1-p1-mqtt-smoke` (plan/qa/bugfix) и `creative/v1-p1-mqtt`.
5. Follow-up out_of_scope: prod broker ACL/placement с Канонеркой; AC-MQTT-20 в T-003.

## Архитектурные заметки

- MQTT встаёт в тот же контур: connector → raw → Normalizer → IPC/sink; lifecycle Events с `reconstructed=false`.
- Dual panel = два source_id в supervisor; isolation подтверждена dual smoke/health.
- Emulator MQTT — отдельный publish path, не через Modbus `__main__` того же image.

## Итог

T-008 / `v1-p1-mqtt` (+ smoke) завершён: s01–s12 done, smoke PASS, blockers нет. Следующий workflow — `BACK ARCHIVE NOW`; `code_changed` для REFLECT = no.
