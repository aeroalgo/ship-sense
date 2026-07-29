# [v1-p1-mqtt-smoke s07] IMPLEMENT

**Дата:** 2026-07-29
**Уровень:** L1
**Статус:** done
**AC:** AC-MQTT-S08
**Plan:** `memory-bank/back/plan/decompose-v1-p1-mqtt-smoke/s07-readme-mqtt-smoke.md`

## Сделано

Дополнен §«Локальный MQTT-dev профиль» в `apps/edge/collector/README.md`:
- subsection **«End-to-end smoke (publisher → broker → collector → writer)»**;
- реальные smoke-команды из реализованных режимов s03–s06:
  `scripts/smoke-mqtt-stack.sh {single|dual|events|sigterm}`;
- команды `up`/`ps`/`logs`/`stop` через `--profile mqtt-dev`;
- expected writer log snippet: `samples/sec=1.0 total_samples=15 total_events=0`
  (формат `writer_stub/__main__.py:48`);
- regex-ожидания: `total_samples=[1-9]`, `samples/sec ...`,
  `total_events=[1-9][0-9]*`;
- subsection **«Known limits (dev-only)»**: `aclfile readwrite`, без TLS/auth,
  writer-stub без PSQL, deterministic seed 42, health snapshot из volume.

## Файлы

- `apps/edge/collector/README.md` — расширение §MQTT (148 → 196 строк).

## Отклонение от плана

План s07 §3.1 указывал режим `scripts/smoke-mqtt-stack.sh all`. В коде такого
режима нет (`smoke-mqtt-stack.sh:27` отклоняет `all` с `exit 2`). Вместо него
документированы **реальные** режимы из s03–s06: `single|dual|events|sigterm`.
README = источник истины для пользователя, не нереализованный `all`.

## Тесты (parent only)

- Шаг docs-only (`tdd: no`) — кода нет, тесты не применимы.
- cmd: `rg -c 'smoke-mqtt-stack|total_events|Known limits|End-to-end smoke|aclfile readwrite' apps/edge/collector/README.md`
- итог: 10 (все ключевые элементы присутствуют).

## Чекпоинт верификации

- AC-MQTT-S08: README §MQTT обновлён — реальные команды smoke +
  expected log snippets + known limits — **PASS**.

## TDD

- **Причина:** документация без кода.
- **Верификация:** README содержит (1) команды smoke; (2) expected
  `total_samples`/`samples/sec`/`total_events` snippets; (3) known limits.

## Frontend

N/A.

## Следующий шаг (для reference)

Полный BACK QA v1-p1-mqtt-smoke (новый чат) → REFLECT.
