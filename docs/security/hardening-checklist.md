# Hardening checklist — ShipSense Edge v1

Чеклист применяется к судовому образу и локальному runtime. Каждый пункт должен иметь владельца и дату в release evidence.

## Образ и контейнеры

- [x] Все runtime Dockerfile создают пользователя `shipsense` и используют `USER shipsense`.
- [x] Установка пакетов использует `--no-cache-dir` или `--no-install-recommends`.
- [x] В image не копируются `.env`, приватные ключи и customer secrets.
- [x] Runtime-процесс не запускается от root.
- [ ] В production deployment capabilities сброшены до минимального набора.
- [ ] Root filesystem read-only; writable directories перечислены явно как volumes.
- [x] В v1 compose отсутствуют `forwarder`, `delivery_cursor` и `shore_ingest`.
- [x] В edge source отсутствуют `sklearn`, `torch` и `predict(`.

## Сеть

- [x] OT доступен через read-only gateway.
- [x] Внешняя публикация Modbus отсутствует у emulator; порт публикуется gateway.
- [ ] UFW policy: deny incoming по умолчанию.
- [ ] Разрешены только локальный UI proxy, maintenance VLAN и необходимые health endpoints.
- [ ] Исходящие соединения ограничены NTP и будущим I2; береговая отправка выключена.
- [x] OT и collector соединены отдельными compose networks.

## SSH и обслуживание

- [ ] SSH выключен в production image или разрешён только по ключу из maintenance VLAN.
- [ ] Парольная аутентификация SSH отключена.
- [ ] Доступ обслуживающего персонала записывается в `access_audit`.
- [ ] Обновления выполняются только штатным I5 OTA flow.

## Данные и аудит

- [x] Таблица `access_audit` имеет append-only trigger.
- [x] Login/logout записывают person, session, action, source IP и details.
- [x] Audit pagination имеет bounded limit.
- [ ] Admin read endpoint и explicit role gate поставляются в s16.
- [x] PostgreSQL credentials задаются через runtime environment, не через source.

## Release gate

Release блокируется, если любой `[x]` пункт регрессировал, если появился запрещённый shore/ML marker или если runtime image снова запускается от root. Пункты `[ ]` требуют выполнения на целевом судовом OS image и прикладываются как deployment evidence.
