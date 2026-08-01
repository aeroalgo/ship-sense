# T6 disk lab

## Назначение

CI harness проверяет mockable часть I6: disk degradation alert, сохранение event path, замену диска с началом resilvering и целостность backup restore. Физические операции остаются ручным hardware gate.

## Сценарии

| Сценарий | Проверка | Ожидаемый результат |
|---|---|---|
| Disk yank | usage выше alert threshold и sample quota превышена | alert, chunks удаляются, SQL не затрагивает `events` |
| ZIP insert | zpool status сообщает `resilvering` | degraded + resilvering |
| Events restore | backup manifest и `events.sql` | restore passed, row count равен backup metadata |
| Crew replacement | ручная замена по A4 checklist | signed evidence с указанием disk slot |

## CI

```bash
.venv/bin/pytest apps/edge/storage/tests/lab/test_t6_scenarios.py -q --tb=line
```

## Hardware gate

1. Извлечь disk1 и сохранить `zpool status -j`.
2. Убедиться, что запись продолжается, health API выдаёт degraded alert.
3. Вставить spare NVMe из ЗИП и сохранить начало resilver.
4. Восстановить events backup в чистую БД; сверить row count и manifest hash.
5. Член экипажа выполняет A4-инструкцию, подписывает checklist и прикладывает evidence.
