# Шаг s10: Normalizer mqtt bridge — disable reconstruction
**Plan ID:** v1-p1-mqtt
**Next Phase:** BACK IMPLEMENT
**needs_creative:** yes (CR-COL-05) — **closed** | **tdd:** yes
**AC:** AC-MQTT-13, AC-MQTT-20, plan §5.2 normalizer changes

- **Creative:** [CR-COL-05 / creative-collector-mqtt-contract.md](../../creative/v1-p1-mqtt/creative-collector-mqtt-contract.md) — `skip_event_detector: true` for mqtt tags, Event passthrough, idempotency dedup

**code_surface:** service

**Impl skills (REQUIRED Read до кода):**
- `.agents/skills/tdd/SKILL.md`
- `.agents/skills/python-testing-patterns/SKILL.md`
- `.agents/skills/modern-python/SKILL.md`
- `.agents/skills/python-anti-patterns/SKILL.md`

## Цель
Minimal B4 changes: mqtt-tagged map entries skip EventDetector reconstruction; accept pre-built Events from mqtt path; dedup idempotency_key in normalizer or sink hook.

## Контекст
- **Consumes:** T-001 s13 NormalizerWorker; s05 mapper Events; tag map metadata `source: mqtt`
- **Produces:** normalizer branch for mqtt protocol / map flag

## Файлы
- `apps/edge/collector/src/collector/normalizer/worker.py` (Модификация)
- `apps/edge/collector/src/collector/normalizer/event_bridge.py` (Создание — optional MqttEventBridge)
- `apps/edge/collector/tests/unit/test_normalizer_mqtt.py` (Создание)

## Интерфейсы (lean — без кода)
- flag: TagMapEntry or source protocol marks `skip_event_detector: true` for mqtt
- path: Events arriving on parallel queue or embedded in raw consumer — align with T-001 s05 pattern
- dedup: normalizer respects idempotency_key from mqtt Event (R-M4)
- scalar path: existing float raw_value unchanged for mqtt telemetry

## TDD (красная → зелёная)
1. **Тест:** mqtt-tagged sample → no reconstructed flip event; mqtt Event passes through with reconstructed=false; modbus sample still uses EventDetector
2. **Запуск:** tесты падают.
3. **Реализация:** minimal branch, no fork of normalizer.
4. **Запуск:** tесты проходят.

## Подробный процесс выполнения
1. ~~**BLOCKED** partial until s05 Event shape finalized in CR-COL-05~~ — **unblocked:** Event shape + skip_event_detector в [creative](../../creative/v1-p1-mqtt/creative-collector-mqtt-contract.md).
2. Prefer mapper emits Events directly; normalizer enriches tag lookup only.
3. Do not delete EventDetector — only skip for mqtt-marked tags.
4. Document downstream T-003 header `X-Events-Reconstruction: false` expectation in implement handoff.

## Чекпоинт верификации
- AC-MQTT-13: reconstructed always false for mqtt events
- modbus regression test in same file passes
- duplicate idempotency_key → single event in sink
