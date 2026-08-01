# T4 — протокол доказательства read-only gateway

## Назначение

Подтвердить, что I1 gateway пропускает read-запросы, отклоняет write-запросы и сохраняет воспроизводимый proof artifact с SHA-256 конфигурации.

## Предусловия

- Запущен gateway с конфигурацией, доступной только для чтения.
- Путь reject log задан через `SHIPSSENSE_GATEWAY_LOG_PATH`.
- Тестовый Modbus-клиент и upstream emulator доступны в лабораторной сети.

## Процедура

1. Сохранить неизменяемую копию gateway config и записать её SHA-256.
2. Отправить read-запросы FC 03 и FC 04.
   - Ожидание: запросы переданы upstream и получили обычный ответ.
3. Отправить write-запросы FC 05, FC 06, FC 15 и FC 16.
   - Ожидание: gateway не передал запросы upstream.
   - Ожидание: клиент получил Modbus exception response с function code `0x80 | request_function_code` и exception code `0x01`.
4. Проверить reject log.
   - Для каждого отклонённого запроса присутствуют `ts`, `function_code`, `source_ip` и `raw_pdu_hash`.
5. Сгенерировать proof artifact:

   ```python
   from apps.edge.gateway.proof.generator import build_proof

   result = build_proof("gateway.yaml", "/var/log/shipsense/rejected_writes.log")
   print(result)
   ```

6. Проверить результат.
   - PDF начинается с `%PDF-`.
   - В PDF присутствуют `config_sha256` и примеры отклонённых запросов.
   - Повторный запуск с теми же входными файлами выдаёт тот же `config_sha256`.

## Результат и sign-off

| Проверка | Результат | Подпись / дата |
| --- | --- | --- |
| Read FC 03/04 разрешены | ☐ | |
| Write FC 05/06/15/16 отклонены | ☐ | |
| Reject log содержит обязательные поля | ☐ | |
| Proof PDF создан и содержит hash | ☐ | |
| Инспектор / ответственный за приёмку | ☐ | |
