# I4 — интеграционный визит и ПНР

## Назначение

Провести первую часть финального выезда: установить тот же OTA-образ, который прошёл CI, состыковать edge-стек с судовой АПС и зафиксировать расхождения карты тегов до приёмочного визита. Визит не считается завершённым, пока все расхождения не имеют владельца, решения и evidence.

## Границы визита

- **Входит:** доставка и установка подписанного образа, проверка A/B и RAID, подключение read-only gateway, сверка тегов, проверка экранов на реальных данных, обучение по процедурам, подготовка autonomy check.
- **Не входит:** запись в АПС, передача данных на берег, установка приватного signing key, изменение production-порогов без согласованного change record.
- **Результат:** подписанный integration protocol, discrepancy list и комплект evidence для acceptance visit.

## Участники и роли

| Роль | Ответственность | Подпись |
|---|---|---|
| Ответственный за выезд | окно работ, scope, остановка при нарушении safety gate | |
| Инженер edge | образ, OTA, health, логи и evidence | |
| Интегратор АПС | точки подключения, карта тегов, read-only подтверждение | |
| Старший механик | эксплуатационная проверка, доступ к шкафу и дискам | |
| Представитель экипажа | проверка понятности экранов и процедур | |

## Входные материалы и предусловия

Перед выходом подтвердить наличие:

- [ ] подписанный OTA bundle и digest release manifest;
- [ ] public key bundle для проверки подписи;
- [ ] контрольный SHA-256 образа и конфигурации gateway;
- [ ] approved tag map / Canonica и список ожидаемых KKS;
- [ ] T4 read-only protocol: `docs/acceptance/T4-readonly-protocol.md`;
- [ ] T5 OTA hardware gate: `docs/tests/T5-ota.md`;
- [ ] T6 disk hardware gate: `docs/tests/T6-disk.md`;
- [ ] A4 disk replacement: `docs/crew/storage-disk-replace-a4.md`;
- [ ] журнал изменений и пустой discrepancy list из этого runbook;
- [ ] резервное окно для rollback и контакт ответственного инженера.

Не начинать установку, если bundle unsigned, digest отсутствует, окно работ не подтверждено или доступ к rollback evidence невозможен.

## 1. Безопасность и исходный snapshot

1. Записать судно, дату, UTC-время начала, порт и идентификаторы участников.
2. Зафиксировать baseline:
   - active OTA slot и boot status;
   - версии edge, collector и gateway;
   - `zpool status -j shipsense` или эквивалентный storage snapshot;
   - свободное место и состояние backup volume;
   - состояние сети к АПС;
   - список процессов и health endpoint.
3. Сохранить baseline в каталог evidence с неизменяемым именем. Не перезаписывать исходные файлы.
4. Проверить, что приватный OTA signing key отсутствует на борту. Жизненный цикл ключа описан в `docs/security/ota-key-lifecycle.md`.

**Stop gate:** при unexpected disk serial/slot, `UNKNOWN` health, несанкционированном write path или отсутствии rollback evidence остановить работы и открыть discrepancy.

## 2. Deploy из OTA-образа

1. Сверить bundle digest с release manifest и записать результат.
2. Передать bundle в inactive slot через штатный I5 installer.
3. Зафиксировать signature verification до записи inactive slot.
4. Перезагрузить в inactive slot по согласованной процедуре.
5. Дождаться collector health check и проверить:
   - application health `pass`;
   - gateway доступен;
   - read-only policy загружена;
   - storage healthy;
   - active slot и version соответствуют manifest.
6. При любом health failure не повторять ручное переключение: сохранить boot log, вызвать штатный rollback и записать причину.
7. Повторить проверку после rollback; активным должен стать ранее healthy slot.

**Acceptance evidence:** bundle digest, signature result, slot before/after, health result, boot/rollback log и ответственный за подпись.

## 3. Проверка storage и backup

1. Выполнить `zpool status -j shipsense`; до приёмки состояние должно быть healthy.
2. Проверить, что backup volume не используется как замена data disk.
3. Подтвердить наличие последнего backup manifest и row-count metadata.
4. Не выполнять физическую замену диска во время интеграции без согласованного hardware gate. Процедура экипажа — `docs/training/disk-replace-a4.md`.
5. Записать storage snapshot в evidence.

## 4. Стыковка с АПС

1. Проверить физический и сетевой путь до upstream emulator/АПС.
2. Отправить только read-запросы FC 03 и FC 04.
3. Подтвердить, что gateway передаёт разрешённые чтения и не изменяет исходные значения.
4. Отправить тестовые write FC 05, FC 06, FC 15 и FC 16 в контролируемом окне.
5. Подтвердить отсутствие upstream forwarding, Modbus exception `0x80 | function_code`, exception code `0x01` и обязательные поля reject log.
6. Сформировать T4 proof artifact и сохранить config SHA-256.

Полная последовательность и sign-off находятся в `docs/acceptance/T4-readonly-protocol.md`. Любое write forwarding — немедленный stop gate и P1 discrepancy.

## 5. Сверка карты и discrepancy list

Для каждой точки из approved map проверить KKS/tag id, единицу, диапазон, обновление и отображение на экране. Расхождение фиксировать до исправления, а не заменять молча ближайшим тегом.

| # | Source KKS/tag | Expected | Actual | Impact | Owner | Решение / срок | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | open |
| 2 | | | | | | | | open |
| 3 | | | | | | | | open |

Статусы: `open`, `accepted-risk`, `fixed`, `retest`, `closed`. `closed` разрешён только после повторного чтения и подписи владельца.

## 6. Проверка экранов и training handoff

1. Пройти экраны 1–10 по ролям, используя реальный read-only поток.
2. Проверить единообразие timestamp, units, stale banner, warning state и значения `unknown/null` для quarantine.
3. Зафиксировать скриншоты без секретов и персональных данных.
4. Передать экипажу материалы:
   - `docs/training/crew-screens.md`;
   - `docs/training/disk-replace-a4.md`;
   - `docs/training/stale-quarantine-card.md`;
   - `docs/training/ota-anchorage.md`.
5. Записать вопросы экипажа в discrepancy list как usability/operations items.

## 7. Подготовка autonomy check

Перед отключением спутникового/внешнего канала:

- [ ] записан baseline archive row count и timestamp;
- [ ] локальная запись и rotation подтверждены;
- [ ] UI умеет показать stale banner без подмены последнего значения на свежий статус;
- [ ] назначен наблюдатель и периодические checkpoints;
- [ ] внешняя связь отключается только по согласованному окну;
- [ ] определены критерии abort: data loss, storage error, process crash, неотмеченный write path.

Цикл 24 часа описан в `docs/runbooks/I4-acceptance-visit.md`; integration visit готовит только baseline и процедуру наблюдения.

## 8. Выходной пакет

- [ ] integration protocol с датой, версиями и подписями;
- [ ] T4 proof artifact и reject log;
- [ ] OTA install/rollback evidence;
- [ ] storage и backup snapshot;
- [ ] discrepancy list с владельцами и статусами;
- [ ] список открытых рисков для acceptance visit;
- [ ] attendance/training record;
- [ ] рекомендация `go`, `go with accepted risks` или `no-go`.

## Sign-off интеграционного визита

| Проверка | Результат | Подпись / дата |
|---|---|---|
| OTA bundle и digest совпадают | ☐ | |
| Health gate и active slot подтверждены | ☐ | |
| Storage healthy, backup manifest найден | ☐ | |
| T4 read-only protocol пройден | ☐ | |
| Discrepancy list создан и назначен | ☐ | |
| Экраны 1–10 пройдены по ролям | ☐ | |
| Baseline autonomy check сохранён | ☐ | |
| Решение о переходе к acceptance | ☐ | |

**Решение:** `go / go with accepted risks / no-go`

**Ответственный:** ____________________  **UTC дата:** ____________________
