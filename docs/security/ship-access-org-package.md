# Ship access org package — шаблон

Документ заполняется перед customer/RMRS handover. До получения customer checklist значения остаются шаблонами и не считаются разрешением доступа.

## Организация и роли

| Поле | Значение |
|---|---|
| Vessel / IMO | `<заполнить>` |
| Customer owner | `<заполнить>` |
| Ship master | `<заполнить>` |
| Chief engineer | `<заполнить>` |
| Electromechanic | `<заполнить>` |
| Maintenance VLAN owner | `<заполнить>` |
| Emergency contact | `<заполнить>` |

## Access procedure

- Доступ выдаётся конкретному человеку, а не общей учётной записи.
- Роль задаётся явным `roles` claim в ship-pack; `rank` является только отображаемой метаинформацией.
- Maintenance доступ разрешён только по key-only SSH из maintenance VLAN.
- Login, logout, denied admin access и OTA actions фиксируются в `access_audit`.
- По окончании окна обслуживания доступ отзывается и evidence прикладывается к handover.

## Acceptance evidence

- [ ] Customer/RMRS checklist приложен.
- [ ] Roster reviewed by ship master and customer owner.
- [ ] Public OTA key fingerprint recorded.
- [ ] UFW/SSH verification output attached.
- [ ] Backup and restore evidence attached.
- [ ] Emergency revoke contact tested.
