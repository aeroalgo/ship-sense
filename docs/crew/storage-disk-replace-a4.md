# A4: замена диска ZFS mirror

1. Остановить операции записи и подтвердить окно обслуживания.
2. Выполнить `zpool status -j shipsense`; определить неисправный диск по `serial` и `slot`, не по порядковому индексу.
3. Проверить, что новый диск соответствует approved serial/slot и не является backup NVMe `/mnt/backup`.
4. Выполнить `zpool offline shipsense <old-device>` и `zpool replace shipsense <old-device> <new-device>`.
5. Наблюдать `zpool status -j shipsense` до завершения resilvering; degraded/resilvering считать нездоровым состоянием.
6. После resilvering запустить scrub и сохранить вывод вместе с health snapshot.
7. При `UNKNOWN`, неожиданном serial/slot или повторной деградации остановить замену и передать эскалацию дежурному инженеру.
