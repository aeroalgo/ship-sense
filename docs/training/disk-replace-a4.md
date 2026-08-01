# A4 — карточка замены диска экипажем

## Назначение

Одностраничная процедура для электромеханика: безопасно заменить неисправный data disk в ZFS mirror, не перепутав его с backup NVMe и не скрыв degraded/resilvering state.

**Полная reference procedure:** `docs/crew/storage-disk-replace-a4.md`  
**Hardware evidence:** `docs/tests/T6-disk.md`

## Перед началом

- [ ] maintenance window одобрено;
- [ ] ответственный инженер на связи;
- [ ] backup manifest найден и читается;
- [ ] новый approved disk имеет подтверждённые serial/slot;
- [ ] новый диск не является `/mnt/backup`;
- [ ] сохранены исходные `zpool status -j shipsense` и health snapshot;
- [ ] операции записи остановлены или разрешены ответственным по window.

**STOP:** `UNKNOWN`, неожиданный serial/slot, повторная деградация или отсутствие backup evidence — не продолжать, вызвать ответственного.

## Процедура

1. Выполнить `zpool status -j shipsense` и определить неисправный device по **serial и slot**, не по индексу.
2. Сверить old device с журналом и фото/label шкафа.
3. Сверить approved serial/slot replacement и убедиться, что это не backup NVMe.
4. Выполнить только по команде ответственного:

   ```bash
   zpool offline shipsense <old-device>
   zpool replace shipsense <old-device> <new-device>
   ```

5. Сохранить вывод и UTC timestamp начала resilvering.
6. Наблюдать `zpool status -j shipsense`; `degraded` и `resilvering` считать нездоровым промежуточным состоянием.
7. После завершения resilvering выполнить scrub и сохранить итоговый health snapshot.
8. Проверить, что archive writes, backup и health API восстановились.
9. Подписать evidence: old/new serial, slots, команды, timestamps и operator.

## Не делать

- Не извлекать диск по порядковому индексу.
- Не использовать backup NVMe как replacement.
- Не запускать `zpool clear` для сокрытия причины.
- Не объявлять замену завершённой до конца resilvering и scrub.
- Не удалять исходные snapshots или логи.

## Ожидаемый результат

- новый disk serial/slot соответствует approved inventory;
- `zpool status` после scrub показывает healthy;
- backup manifest и row-count metadata доступны;
- события и archive writes не потеряны;
- T6 evidence приложен к acceptance package.

## Sign-off

| Поле | Значение |
|---|---|
| Vessel / date UTC | |
| Old serial / slot | |
| New serial / slot | |
| Resilver start/end | |
| Scrub result | pass / fail |
| Backup restore evidence | |
| Health snapshot | |
| Operator | |
| Ответственный инженер | |

**Результат:** `pass / escalate`
