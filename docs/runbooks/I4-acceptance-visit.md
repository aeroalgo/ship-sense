# I4 — приёмочный визит и 24-часовая проверка автономности

## Назначение

Провести приёмку полного v1-стека на борту после integration visit: подтвердить воспроизводимый OTA deploy, read-only интеграцию с АПС, T4/T10, обучение экипажа и автономную работу без внешнего канала в течение 24 часов.

## Критерий выпуска

Приёмка имеет статус `pass`, только если все обязательные gates закрыты, evidence сохранён, открытые расхождения либо закрыты, либо явно приняты владельцем с указанным сроком и влиянием. Не считать отсутствие ошибки в UI доказательством свежести данных.

## Участники

| Роль | Область подписи |
|---|---|
| Заказчик / представитель судна | итоговый acceptance |
| Ответственный за I4 | координация и stop/no-go |
| Инженер edge/API | OTA, health, API/WS и архив |
| Интегратор АПС | T4 и карта тегов |
| Старший механик | storage, stale и operational readiness |
| Тренер / наблюдатель | практические задания экипажа |

## Предусловия и входной пакет

- [ ] integration visit подписан как `go` или `go with accepted risks`;
- [ ] нет открытого P1 discrepancy;
- [ ] release bundle, public key и digest доступны;
- [ ] baseline, backup manifest и storage snapshot приложены;
- [ ] T4 protocol готов к повторному sign-off;
- [ ] T5/T6 manual hardware gates подготовлены;
- [ ] T9 report fixtures/expected outputs и T10 load procedure доступны;
- [ ] acceptance window и rollback owner назначены.

## 1. Повторяемый deploy и health gate

1. Сверить текущий active slot, version и baseline.
2. Установить тот же подписанный OTA bundle, который использован в CI/release evidence.
3. Сохранить digest, signature result, inactive slot, boot result и health gate.
4. Проверить collector, API, WS, gateway, archive writer и storage health.
5. При failed health gate сохранить логи и подтвердить автоматический rollback. Ручное принудительное продолжение запрещено.
6. Подписать результат по I4-F1.

| Поле | Значение |
|---|---|
| Release version | |
| Bundle SHA-256 | |
| Config SHA-256 | |
| Slot before | |
| Slot after | |
| Health result | pass / fail |
| Rollback evidence | path / n/a |

## 2. T4 read-only acceptance

Выполнить `docs/acceptance/T4-readonly-protocol.md` повторно на acceptance build:

- [ ] FC 03/04 проходят и дают ожидаемый ответ;
- [ ] FC 05/06/15/16 отклоняются до upstream;
- [ ] exception и reject log имеют обязательные поля;
- [ ] proof PDF начинается с `%PDF-`, содержит `config_sha256` и samples;
- [ ] повторный proof сохраняет тот же config hash;
- [ ] signed T4 protocol приложен.

Любой факт записи в АПС — `no-go`, даже если пользовательский экран показывает корректное значение.

## 3. T9 report acceptance

Проверить четыре golden fixture сценария отчётного стека:

1. получить canonical body без `generated_at`;
2. сравнить SHA-256 с ожидаемым fixture hash;
3. проверить `watch`, `daily`, `fuel` и error/waiver markers;
4. подтвердить, что повторная генерация с теми же входами детерминирована;
5. сохранить generated artifact, expected hash и operator initials.

| Fixture / report | Expected hash | Actual hash | Result | Evidence |
|---|---|---|---|---|
| watch | | | ☐ | |
| daily | | | ☐ | |
| fuel | | | ☐ | |
| error/waiver | | | ☐ | |

Если T9 fixture не совпадает, открыть discrepancy и не подписывать report acceptance как pass.

## 4. T10 API/WS acceptance на шести постах

Цель — подтвердить API/WS для шести одновременных постов без подмены stale/quarantine состояния.

1. Подключить шесть разрешённых клиентов или эквивалентный lab simulator.
2. Для каждого поста открыть требуемые API и WebSocket subscriptions.
3. Внести controlled read-only sample/update и проверить доставку события всем ожидаемым подписчикам.
4. Проверить reconnect одного клиента без потери общей работоспособности остальных.
5. Зафиксировать latency, error count, active connections и timestamps.
6. Проверить отсутствие write endpoint/path и отсутствие передачи данных на берег.

| Проверка | Ожидание | Факт | Result |
|---|---|---|---|
| 6 concurrent posts | все подключены | | ☐ |
| API response | schema/status корректны | | ☐ |
| WS delivery | событие доставлено ожидаемым clients | | ☐ |
| reconnect | клиент восстановлен | | ☐ |
| stale/quarantine | state честно отражён | | ☐ |
| external forwarding | отсутствует | | ☐ |

T10 evidence: client matrix, timestamps, API/WS logs, connection count, error summary и подпись инженера.

## 5. Hardware gates T5 и T6

### T5 OTA

По `docs/tests/T5-ota.md` выполнить и приложить evidence:

- [ ] bad image приводит к rollback;
- [ ] dead collector после healthy boot приводит к rollback;
- [ ] unsigned bundle отклоняется до staging;
- [ ] десять прерываний download восстанавливаются до полного payload и совпадающего SHA-256.

### T6 storage

По `docs/tests/T6-disk.md` и `docs/crew/storage-disk-replace-a4.md`:

- [ ] disk yank даёт degraded alert и сохраняет event path;
- [ ] spare disk начинает resilvering;
- [ ] backup restore row count равен manifest metadata;
- [ ] serial/slot нового диска проверены;
- [ ] после resilvering выполнен scrub и сохранён health snapshot.

Физические действия выполнять только при approved maintenance window и с журналом оператора.

## 6. Обучение и практическая проверка

Экипаж должен выполнить задания из всех one-pager:

- [ ] вахтенный находит нужный экран и отличает fresh/stale/quarantine;
- [ ] стармех объясняет, когда можно одобрить OTA в стоянке;
- [ ] электромеханик по A4 card определяет disk serial/slot и не трогает backup NVMe;
- [ ] каждый участник объясняет, что делать при stale/quarantine и кому эскалировать;
- [ ] attendance и результаты практики подписаны.

## 7. Autonomy check — 24 часа без спутника

### Setup (T+0)

1. Зафиксировать UTC timestamp, active slot/version и baseline archive row count.
2. Сохранить storage health, свободное место, process health, API/WS connection count и последние sample timestamps.
3. Отключить satellite/external channel в согласованном окне. Локальная запись должна продолжаться.
4. Убедиться, что UI показывает stale banner для данных, которые больше не обновляются, и не маркирует их как свежие.

### Checkpoints

Снимать snapshot на T+1h, T+4h, T+8h, T+12h, T+18h и T+24h. В каждом snapshot записать:

- archive row count и delta от предыдущего checkpoint;
- последний timestamp входного sample по критическим tags;
- stale/quarantine state и видимый banner;
- process health, API/WS health и error count;
- storage usage, backup status и rotation result;
- active slot и отсутствие непланового restart;
- operator, UTC-время и путь к evidence.

| Checkpoint | Rows / delta | Critical sample age | Stale banner | Storage | Health | Operator |
|---|---|---|---|---|---|---|
| T+0 | | | | | | |
| T+1h | | | | | | |
| T+4h | | | | | | |
| T+8h | | | | | | |
| T+12h | | | | | | |
| T+18h | | | | | | |
| T+24h | | | | | | |

### Pass / abort

**Pass:** локальная запись продолжалась весь период; archive rows не терялись; storage и process health оставались допустимыми; stale banner появлялся честно; не было непланового write path, crash или data corruption.

**Abort:** пропуск записи, повреждение архива, storage error, crashloop, неожиданный write в АПС, отсутствие stale indication или невозможность доказать состояние. При abort сохранить последний snapshot, вернуть внешний канал только по safety procedure и открыть discrepancy.

## 8. Итоговый sign-off

| Gate | Result | Evidence | Подпись / дата |
|---|---|---|---|
| I4-F1 deploy from same OTA image | ☐ | | |
| I4-F2 A/B + RAID state | ☐ | | |
| I4-F3 APS read-only integration | ☐ | | |
| I4-F4 integration/acceptance visits | ☐ | | |
| I4-F5 training complete | ☐ | | |
| T4 protocol | ☐ | | |
| T9 deterministic reports | ☐ | | |
| T10 six posts | ☐ | | |
| T5 OTA hardware gate | ☐ | | |
| T6 disk hardware gate | ☐ | | |
| 24h autonomy | ☐ | | |

**Итог:** `pass / pass with accepted risks / fail`

**Открытые расхождения и срок:**

| ID | Описание | Влияние | Владелец | Срок | Принято кем |
|---|---|---|---|---|---|
| | | | | | |

**Заказчик:** ____________________  **Ответственный I4:** ____________________

**UTC дата:** ____________________
