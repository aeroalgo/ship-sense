# T5 OTA lab

## Назначение

CI harness фиксирует критические OTA-сценарии I5 без RAUC и физического устройства. `LabOtaDriver` — детерминированный адаптер для тех же rollback, signature и resume hooks, которые подключаются к hardware runner.

## Сценарии

| Сценарий | Проверка | Ожидаемый результат |
|---|---|---|
| Bad image | health check после переключения A → B | активный A, pending очищен |
| Collector dead | collector не поднялся после healthy boot | rollback к A |
| Unsigned | пустая подпись до staging | `SignatureVerificationError`, запись не начата |
| Ten cuts | десять прерываний chunk download | payload полностью собран, SHA-256 совпадает |

## CI

```bash
.venv/bin/pytest apps/edge/ota/tests/lab/test_t5_scenarios.py -q --tb=line
```

Тесты не запускают RAUC, переключение диска или сеть. Перед I4 acceptance lab runner должен заменить `LabOtaDriver` на hardware hooks и сохранить boot/rollback evidence.

## Hardware gate

1. Установить подписанный образ в pending slot.
2. Подменить образ битым и подтвердить rollback менее чем за 5 минут.
3. Остановить collector после healthy boot и подтвердить rollback.
4. Передать unsigned bundle и подтвердить отсутствие записи в слот.
5. Десять раз прервать download; подтвердить финальный hash и активный слот.
