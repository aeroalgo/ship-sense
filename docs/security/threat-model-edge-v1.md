# Модель угроз ShipSense Edge v1

## Назначение и границы

Документ описывает автономный судовой контур ShipSense v1: промышленный источник данных, read-only gateway, collector, локальное хранилище, API и локальный операторский интерфейс. Контур работает без передачи телеметрии на берег. Внешний IdP, береговой forwarder и I2 PKI относятся к будущим версиям и не являются доверенными компонентами v1.

## Активы

| Актив | Требование |
|---|---|
| Телеметрия и события | целостность, временная упорядоченность, доступность |
| Журнал `access_audit` | доказуемая добавляемость, запрет UPDATE/DELETE |
| OTA-артефакт и публичный ключ | проверка подписи до установки |
| Ship-pack и roster | контроль доступа и воспроизводимость конфигурации |
| Секреты и ключи | отсутствие в Git и runtime image |
| Операторские действия | привязка к person/session/source IP |

## Доверенные границы

1. OT-источник находится за read-only gateway. Collector не получает write-path к промышленному устройству.
2. Gateway и collector соединены отдельной сетью; наружу публикуется только необходимый локальный порт.
3. API и хранилище доступны только локальному судовому контуру.
4. OTA-проверка является обязательным барьером перед применением обновления.
5. `access_audit` хранится append-only на уровне PostgreSQL trigger.

## STRIDE-анализ

| Угроза | Вектор | Митигирование v1 | Проверка |
|---|---|---|---|
| Spoofing | подмена person/session cookie | session snapshot, явные роли в roster, HttpOnly cookie | session tests; роль без claim не получает admin permission |
| Tampering | запись команд в OT или изменение журнала | read-only gateway, запрет write services, append-only trigger | gateway rejection tests; migration audit tests |
| Repudiation | отрицание login/logout/admin действия | запись `ts`, person, session, action, source IP и details | `AccessAuditWriter` tests; журнал недоступен для mutation |
| Information disclosure | публикация OT/API наружу или секреты в image | локальные bind/network правила, secrets не копируются в image | compose review; image checklist |
| Denial of service | неконтролируемый входящий порт или oversized request | UFW deny-by-default, bounded pagination, health checks | hardening checklist; targeted API tests |
| Elevation of privilege | rank используется вместо роли или контейнер root | explicit roles, fail-closed role gate, `USER shipsense` | role tests; Dockerfile exclusion test |

## Остаточные риски

- Customer/RMRS access checklist ещё не предоставлен; org package остаётся шаблоном.
- Полный mTLS PKI и береговая интеграция относятся к v2.
- UFW и SSH применяются образом ОС/операционной процедурой, а не Dockerfile.

## Реакция на инцидент

1. Зафиксировать время, person/session и affected service.
2. Сохранить append-only audit rows и OTA verification output.
3. Остановить подозрительный доступ через maintenance VLAN.
4. Не удалять журнал и не заменять ship-pack вручную.
5. Выполнить rollback только через штатный OTA health gate и оформить действие в судовом журнале.
