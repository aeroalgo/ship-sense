# Реестр шагов (Decompose index)
**Plan ID:** v1-p1-mqtt-smoke
**План:** [plan-v1-p1-mqtt-smoke.md](../plan-v1-p1-mqtt-smoke.md)
**Родитель:** [decompose-v1-p1-mqtt/index.md](../decompose-v1-p1-mqtt/index.md)
**Implement index:** [implement-v1-p1-mqtt-smoke/index.md](../../implement/implement-v1-p1-mqtt-smoke/index.md)
**Дата:** 2026-07-29
**Режим:** BACK DECOMPOSE
**Уровень:** L3 (T-008 gap-close)

Каждый шаг — атомарная задача под один заход IMPLEMENT. Детали — в `sNN-*.yaml`. Интерфейсы — **lean** (без тел/полного кода).
> **Трекер шагов:** только этот index (не дублировать чеклисты sNN в plan).

## Контекст codebase (verified 2026-07-29)
- `MqttPublisherAdapter` реализован: `apps/edge/emulator/src/emulator/protocols/mqtt_publisher.py` — `connect(broker_url)`, `build_messages(tick)`, `publish_loop(iterations=)`, `stop()`, deterministic seed, panels `aps`/`geu`, 4 kind (analog/discrete/event/egt).
- `apps/edge/emulator/src/emulator/mqtt_publish.py` — **отсутствует** (создаётся в s01).
- compose: `mosquitto` + `collector-mqtt` в профиле `mqtt-dev` есть; сервиса `emulator-mqtt` — **нет** (s02).
- `infra/mosquitto/aclfile`: только `topic read shipsense/#` → **publish запрещён** анониму (s02 правит).
- README `apps/edge/collector/README.md` §«Локальный MQTT-dev профиль» есть (s12), но без publisher-команд и expected log snippets (s07).

## Skills в контексте
| Skill | Зачем |
|-------|-------|
| `writing-plans` | атомарность шагов, files/AC/TDD boundaries |
| `architecture-patterns` | compose service isolation, reuse T-008 framework |
| `python-testing-patterns` | targeted pytest для entrypoint + smoke harness |

**Per-step канон** (не дублировать пути здесь): каждый `sNN` — `code_surface` + **Impl skills** по карте `back_developer/workflow-decompose.mdc`.

| `code_surface` | Шаги (mqtt-smoke) |
|----------------|-------------------|
| `service` | s01 (+ anti-patterns) |
| `infra` | s02 (+ anti-patterns: lifecycle/deps), s07 |
| `test` | s03, s04, s05, s06 |

## CREATIVE blockers
Нет. Контракт MQTT payload закрыт CR-COL-05; `MqttPublisherAdapter` (s08 родителя) его реализует. Этот декомпоз — wire + smoke, не дизайн (plan §9).

## Compose execution — parent only
Шаги s03–s06 гоняют `docker compose --profile mqtt-dev` — выполняет **parent** (не subagent). Subagent если спавнится — только готовит скрипт/фикстуры, не запускает compose. FRONT N/A (`front-tests-parent-only.mdc`).

## Очередь шагов
| step_id | title & files | implement | needs_creative | tdd | ac | next_phase | status |
|:---|:---|:---|:---:|:---:|:---|:---|:---|
| **s01** | [s01-mqtt-publish-entrypoint.md](s01-mqtt-publish-entrypoint.md)<br>• `apps/edge/emulator/src/emulator/mqtt_publish.py` (create)<br>• `apps/edge/emulator/tests/test_mqtt_publish_entrypoint.py` (create) | [s01](../../implement/implement-v1-p1-mqtt-smoke/s01-mqtt-publish-entrypoint.md) | no | yes | AC-MQTT-S01 | BACK IMPLEMENT | done |
| **s02** | [s02-compose-emulator-mqtt.md](s02-compose-emulator-mqtt.md)<br>• `docker-compose.yml` (modify: +`emulator-mqtt`)<br>• `infra/mosquitto/aclfile` (modify: +publish anon)<br>• `infra/mosquitto/mosquitto.conf` (verify) | [s02](../../implement/implement-v1-p1-mqtt-smoke/s02-compose-emulator-mqtt.md) | no | no | AC-MQTT-S02, AC-MQTT-S07 | BACK IMPLEMENT | done |
| **s03** | [s03-smoke-single-panel.md](s03-smoke-single-panel.md)<br>• `scripts/smoke-mqtt-stack.sh` (create) | [s03](../../implement/implement-v1-p1-mqtt-smoke/s03-smoke-single-panel.md) | no | no | AC-MQTT-S03 | BACK IMPLEMENT | done |
| **s04** | [s04-smoke-dual-panel-health.md](s04-smoke-dual-panel-health.md)<br>• `scripts/smoke-mqtt-stack.sh` (modify) | [s04](../../implement/implement-v1-p1-mqtt-smoke/s04-smoke-dual-panel-health.md) | no | no | AC-MQTT-S04 | BACK IMPLEMENT | done |
| **s05** | [s05-smoke-lifecycle-events.md](s05-smoke-lifecycle-events.md)<br>• `scripts/smoke-mqtt-stack.sh` (modify) | [s05](../../implement/implement-v1-p1-mqtt-smoke/s05-smoke-lifecycle-events.md) | no | no | AC-MQTT-S06 | BACK IMPLEMENT | done |
| **s06** | [s06-smoke-sigterm-drain.md](s06-smoke-sigterm-drain.md)<br>• `scripts/smoke-mqtt-stack.sh` (modify) | [s06](../../implement/implement-v1-p1-mqtt-smoke/s06-smoke-sigterm-drain.md) | no | no | AC-MQTT-S05 | BACK IMPLEMENT | done |
| **s07** | [s07-readme-mqtt-smoke.md](s07-readme-mqtt-smoke.md)<br>• `apps/edge/collector/README.md` (modify §MQTT) | [s07](../../implement/implement-v1-p1-mqtt-smoke/s07-readme-mqtt-smoke.md) | no | no | AC-MQTT-S08 | BACK IMPLEMENT | done |

## Порядок выполнения
s01 → s02 → s03 → s04 → s05 → s06 → s07.
s02 можно делать параллельно с s01 (нет общей файловой поверхности: s01 = emulator pkg, s02 = compose/infra). s03 зависит от s01 + s02.

## AC coverage
| AC | Шаг |
|----|-----|
| AC-MQTT-S01 | s01 |
| AC-MQTT-S02 | s02 |
| AC-MQTT-S03 | s03 |
| AC-MQTT-S04 | s04 |
| AC-MQTT-S05 | s06 |
| AC-MQTT-S06 | s05 |
| AC-MQTT-S07 | s02 |
| AC-MQTT-S08 | s07 |

---

*2026-07-29 — BACK DECOMPOSE v1-p1-mqtt-smoke. 7 шагов, all AC-MQTT-S01..S08 covered.*
