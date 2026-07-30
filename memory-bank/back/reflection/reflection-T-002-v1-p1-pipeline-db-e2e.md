# BACK REFLECT — T-002 / v1-p1-pipeline-db-e2e

**Дата:** 2026-07-30  
**Уровень:** L3  
**Статус:** completed  
**Основание:** [Epic QA PASS](../../archive/back/qa/v1-p1-pipeline-db-e2e/qa-20260730-v1-p1-pipeline-db-e2e.md)  
**Scope:** s01–s08, AC-PIPE-01..10, FR-7

## Сравнение с планом и decompose

План требовал доказать реальный путь `emulator → collector → writer → TimescaleDB` для L0 IPC, L1 MQTT/Modbus и L2 compose, а также добавить fail-loud smoke и документационный контракт. Все восемь атомарных шагов decompose завершены:

- s01 добавил `WriterService.start_tcp(host, port=0)` с возвратом bound address и сохранил совместимость `run_tcp`/compose-порта.
- s02 подготовил Timescale testcontainer и Alembic fixture для настоящей DB-проверки.
- s03 доказал IPC-запись samples и events без моков repository layer.
- s04–s05 доказали MQTT samples и lifecycle events через broker, collector stack и writer.
- s06 доказал Modbus TCP → collector → IPC → writer → samples.
- s07 добавил bounded compose smoke для default и MQTT profile с SQL count assertion.
- s08 зафиксировал README layer matrix, команды запуска, expected SQL и pytest marker/runner contract.

Epic QA подтвердил AC-PIPE-07/08 по live evidence s07, AC-PIPE-09 по документации и AC-PIPE-10 по storage/non-slow regression. Все AC-PIPE-01..10 покрыты реальными тестами или smoke/documentation evidence согласно плану.

Ограничение плана не скрыто: в текущем QA slow-тесты были исключены, поэтому полный suite green не заявляется. Это не блокирует закрытие данного pipeline-db-e2e scope, но остаётся отдельной проверкой при необходимости расширения QA.

## Что сработало

1. Декомпозиция по уровням L0/L1/L2 разделила транспортные контуры и позволила локализовать ошибки до compose smoke.
2. TDD для s01 и s03–s06 выявил реальные несовместимости: отсутствие bound-port API, lifecycle async fixtures, преобразование MQTT map entry и пустой input-register профиль Modbus.
3. Polling с явным timeout оказался надёжнее фиксированных sleep: тесты и smoke завершаются с диагностируемым `AssertionError`/`FAIL`, а не маскируют зависание.
4. Запись проверялась через настоящие TimescaleDB таблицы и SQL count/value/tag assertions; repository mocks не использовались как доказательство persistence.
5. Compose smoke остался отдельным исполняемым скриптом и не расширил runtime API writer или compose topology.
6. QA-артефакт честно разделил green non-slow regression и непроверенный slow scope. Reviewer gate подтвердил PASS без открытых issues.

## Проблемы и их разрешение

- Начальный writer API не позволял безопасно получить ephemeral bound port. Исправлено выделением `start_tcp`; legacy `run_tcp` делегирует новый путь.
- Testcontainers/async lifecycle требовал explicit pytest-asyncio plugin, bounded readiness checks и корректного `PYTHONPATH`/Alembic runner. Эти условия закреплены в pipeline fixtures.
- MQTT collector ожидал native tag-map entry, а harness передавал channel-map entry. Добавлена явная конверсия на границе тестового контура.
- Modbus emulator падал при пустом `input_registers`; профиль получил минимальный input signal, необходимый для живого TCP-потока.
- В раннем storage QA были runtime/compose blockers. Они были вынесены в отдельный BUGFIX и повторно подтверждены до запуска этого эпика; pipeline scope не замаскировал их fallback-логикой.

## Уроки

- Для интеграционного backend-теста bound-port lifecycle лучше сделать первым самостоятельным контрактом: это уменьшает зависимость от фиксированных портов и ускоряет параллельные проверки.
- Harness должен адаптировать только типы на границах компонентов, не подменяя transport/repository реальными моками.
- Каждый long-running integration path должен иметь readiness poll, bounded timeout и loud failure с полезным контекстом.
- Live evidence и документационный контракт нужно фиксировать раздельно: README не заменяет compose run, а compose run не заменяет воспроизводимую команду.
- Разделение `not slow` и slow в QA-отчёте необходимо сохранять, чтобы отсутствие slow execution не превращалось в ложное утверждение о полном suite.

## Улучшения процесса

1. В следующем цикле добавить отдельный scheduled/explicit QA-прогон slow suite и сохранять его результат рядом с non-slow evidence.
2. Перед L2 smoke заранее проверять health/readiness всех compose dependencies и очищать старые контейнеры/данные отдельной documented командой.
3. Для новых transport contours использовать общий bounded-poll helper и единый формат diagnostics, если это не ухудшает изоляцию тестов.
4. После изменения test marker/config запускать targeted pipeline tests и marker discovery до финального regression, как сделано в s08.
5. При расширении scope повторно проверить live SQL counts после restart/reconnect, но не смешивать эту проверку с уже закрытым atomic шагом.

## Итог

T-002 pipeline-db-e2e завершён: decompose s01–s08 completed, Epic QA PASS, открытых issues и blockers нет. Следующий workflow — `BACK ARCHIVE NOW`; code_changed для REFLECT = no.
