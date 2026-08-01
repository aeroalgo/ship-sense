# OTA в стоянке — карточка решения для старшего механика

## Цель

Обновлять edge только в согласованной стоянке и только подписанным образом. Карточка не заменяет I5 runbook: она помогает принять или отклонить окно обновления на борту.

**Reference:** `docs/tests/T5-ota.md`, `docs/security/ota-key-lifecycle.md`, `docs/runbooks/I4-acceptance-visit.md`

## Когда OTA разрешено

Перед approval должны быть одновременно выполнены все пункты:

- [ ] судно стоит в approved anchorage/maintenance window;
- [ ] ответственный за I4 и bridge/operations подтвердили окно;
- [ ] нет активного рейса, манёвра или операции, требующей непрерывного edge;
- [ ] подписанный bundle получен через approved delivery path;
- [ ] bundle SHA-256 совпадает с release manifest;
- [ ] signature verification пройдена до записи inactive slot;
- [ ] rollback owner и контакт доступны;
- [ ] backup/storage health healthy;
- [ ] экипаж знает, как выглядит temporary stale/maintenance state;
- [ ] evidence directory подготовлен и не перезапишет прошлые логи.

Если хотя бы один пункт не выполнен — **не approve**, открыть discrepancy или перенести окно.

## Процедура approval

1. Записать vessel, UTC-время, current version, active slot и operator.
2. Сверить bundle version и SHA-256 с manifest.
3. Проверить, что приватный signing key отсутствует на судне.
4. Подтвердить staging только в inactive slot.
5. Зафиксировать signature result и slot transition.
6. Дождаться health gate: collector, API, gateway, storage и archive writer.
7. После healthy boot подтвердить active version и сохранить evidence.
8. Если health gate failed, не повторять ручное переключение: дождаться штатного rollback и сохранить boot/rollback logs.

## После обновления

- [ ] экран 10 показывает ожидаемые version/slot;
- [ ] экран 9 показывает healthy storage и backup;
- [ ] T4 read-only smoke выполнен;
- [ ] critical tags получают новые samples;
- [ ] stale banner отсутствует только там, где есть свежие данные;
- [ ] журнал update подписан.

## Немедленно остановить и эскалировать

- unsigned/invalid bundle;
- digest mismatch;
- попытка записи в active slot напрямую;
- failed health gate без rollback evidence;
- collector/API crashloop;
- storage degraded или backup unavailable;
- неожиданное изменение gateway policy;
- запрос на передачу signing key или telemetry на берег.

## Sign-off OTA в стоянке

| Поле | Значение |
|---|---|
| Vessel / anchorage | |
| Window UTC start/end | |
| Current version / slot | |
| Bundle version / SHA-256 | |
| Signature result | pass / fail |
| New version / slot | |
| Health result | pass / rollback |
| T4 smoke evidence | |
| Rollback evidence (если был) | |
| Operator / approver | |

**Решение:** `approve / defer / rollback / escalate`
