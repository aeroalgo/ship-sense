# BACK CREATIVE — T-005 v1-p2-ship: CR-P2-03 RAID mirror, backup и alerts

**Creative ID:** CR-P2-03  
**Plan:** [plan-v1-p2-ship.md](../../plan/plan-v1-p2-ship.md)  
**Decompose:** [decompose-v1-p2-ship/index.md](../../plan/decompose-v1-p2-ship/index.md)  
**Связанный шаг:** [s13-i6-raid-backup.md](../../plan/decompose-v1-p2-ship/s13-i6-raid-backup.md)  
**Дата:** 2026-07-31  
**Режим:** BACK CREATIVE  
**Уровень:** L3  
**Статус:** closed

## Skills gate

- `.agents/skills/brainstorming/SKILL.md`
- `.agents/skills/architecture-patterns/SKILL.md`
- `.agents/skills/improve-codebase-architecture/SKILL.md`
- `.agents/skills/python-design-patterns/SKILL.md`
- `.agents/skills/property-based-testing/SKILL.md`

**Почему выбраны situational skills:**

- `improve-codebase-architecture` — отделить глубокий storage-модуль (топология, snapshot/backup state, restore verification) от ОС, PostgreSQL и shell adapters; интерфейс модуля должен быть тестовой поверхностью.
- `python-design-patterns` — сохранить KISS/SRP: typed snapshot и backup decisions — pure data/logic, внешние `zpool`, `pg_dump`, `tar` и filesystem — узкие adapters; generic plugin registry не нужен.
- `property-based-testing` — проверить инварианты manifest, атомарного backup directory и degraded/threshold transitions за пределами нескольких happy-path fixtures.

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture — CR-P2-03 storage topology

## Проблема и границы

I6 должен переживать отказ одного диска, сохранять конфигурацию и events на локальном зеркале, выдавать понятный degraded status и оставлять проверяемый backup для T6. Storage-модуль не должен импортировать FastAPI, SQLAlchemy или конкретный subprocess runner. ОС и PostgreSQL остаются adapters.

Есть важное различие в требованиях RPO: зеркальная запись в два диска даёт RPO 0 для отказа одного диска, но **ежедневный** `pg_dump` сам по себе не даёт RPO 0 при потере всего узла. В v1 фиксируем: disk-failure RPO=0; disaster-recovery backup RPO≤24h. Настоящий host-loss RPO=0 потребует WAL/archive destination и не входит в s13.

## Компонент A — mirror topology and replacement

### Вариант A1 — ZFS mirror (рекомендуемый)

- Отдельный `shipsense` pool из двух NVMe; PostgreSQL data и ship-pack находятся на dataset с sync-политикой, backup NVMe не входит в pool.
- `zpool status -j` — единственный источник topology state; `zpool scrub` запускается по расписанию, результат входит в health snapshot.
- Замена диска: оператор подтверждает serial/slot, затем adapter выполняет `zpool replace`; resilver progress остаётся видимым.

**Плюсы:** встроенные checksum, scrub, понятная degraded/resilvering модель, snapshot seam и однозначный serial для A4.  
**Минусы:** ZFS-пакет и boot/storage layout нужно закрепить для Ubuntu edge image; неправильно выбранный disk может сделать замену опасной.

### Вариант A2 — mdraid1 + обычная filesystem

- `mdadm --detail --scan` и `/proc/mdstat` дают mirror state; filesystem лежит поверх mdraid.
- Замена диска: `mdadm --fail/remove/add`; отдельный health adapter парсит rebuild state.

**Плюсы:** более привычный Linux tooling и меньше требований к image.  
**Минусы:** scrub/checksum/snapshot semantics нужно собирать отдельно; больше разрозненных источников truth и выше шанс, что health покажет mounted filesystem вместо реального degraded RAID.

### Решение

Выбрать **A1 ZFS mirror** для v1. `apps/edge/storage/raid/` предоставляет typed `RaidSnapshot` и `RaidCommand` contract; только adapter знает CLI и serial mapping. A2 оставить документированным fallback при невозможности поставить ZFS в утверждённый edge image, без параллельной реализации двух backends в s13.

Инварианты:

1. backup NVMe (`/mnt/backup`) не является членом mirror pool.
2. `degraded=true`, если pool не `ONLINE`; `resilvering` не маскируется под healthy.
3. неизвестный/невалидный CLI output → `unknown`, который health policy трактует fail-closed.
4. replacement command никогда не принимает только человекочитаемый label; нужен validated serial/slot pair.

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Architecture — backup and restore seam

## Компонент B — daily events/config backup

### Вариант B1 — один shell script

`shipsense-backup-events.sh` с `set -Eeuo pipefail` создаёт staging directory, выполняет `pg_dump --table=events --data-only`, добавляет ship-pack/formulas/warnings YAML, пишет manifest и делает atomic rename в `/mnt/backup/YYYY-MM-DD/`.

**Плюсы:** совпадает с operational deliverable, легко вызвать systemd timer и вручную на судне.  
**Минусы:** parsing/manifest/restore validation быстро превращают shell в не тестируемый монолит; ошибки частично записываются только в текстовый log.

### Вариант B2 — Python coordinator + thin shell entrypoint (рекомендуемый)

- `scripts/shipsense-backup-events.sh` — только environment loading, lock и вызов `.venv/bin/python -m ...`.
- Python-модуль в `apps/edge/storage/backup/` получает injected `CommandRunner`, `Clock` и `Filesystem`; orchestration order и manifest validation остаются тестируемыми.
- Backup layout:

```text
/mnt/backup/YYYY-MM-DD/
  events.sql
  ship-pack.tar
  formulas/
  warnings.yaml
  manifest.json
  COMPLETE
```

- Сначала staging `YYYY-MM-DD.tmp-<run_id>`, затем `fsync` файлов/директории и `rename` в final path. `COMPLETE` — последняя запись; каталог без marker не считается backup.
- `manifest.json` содержит schema version, UTC created_at, row-count (если доступен), byte sizes и SHA-256 каждого payload. Секреты и DSN в manifest не попадают.
- Повторный запуск того же UTC дня не перезаписывает complete backup: создаётся новая run directory либо выполняется explicit operator cleanup. Это исключает silent replacement.

**Плюсы:** shell остаётся требуемым интерфейсом, а pure manifest/layout decisions и failures тестируются без PostgreSQL/ZFS; можно одинаково использовать T6 restore harness и production runner.  
**Минусы:** появляется небольшой Python coordinator и необходимость согласовать subprocess exit/timeout contract.

### Вариант B3 — PostgreSQL base backup/WAL archive

Помимо `pg_dump` включить WAL archiving и point-in-time restore.

**Плюсы:** существенно меньше RPO для потери host и лучшее восстановление больших events таблиц.  
**Минусы:** scope и storage budget заметно растут, backup destination становится operational dependency; это уже отдельный recovery design, а не простой daily export.

### Решение

Выбрать **B2**. `pg_dump` остаётся каноническим payload для s13, а B3 зафиксирован как post-v1 enhancement для disaster RPO. Ship-pack собирается только из allowlisted paths (config/formulas/warnings), не из всего репозитория. Ошибка любого payload, checksum или atomic finalize делает run failed и не создаёт `COMPLETE`.

Backup retention в s13 минимальна: сохранять daily directories согласно available backup volume, не удалять последний complete backup при cleanup. Retention policy и encryption-at-rest — отдельные follow-up, но manifest format не должен им мешать.

## Компонент C — restore verification / T6

### Вариант C1 — ручная инструкция restore

Оператор распаковывает tar, импортирует SQL и вручную сравнивает таблицы.

**Плюсы:** почти нет automation.  
**Минусы:** не даёт reproducible proof, легко пропустить warnings/config или импортировать неполный каталог.

### Вариант C2 — disposable restore harness (рекомендуемый)

- Создать временную staging PostgreSQL database/container.
- Проверить `COMPLETE`, schema version и SHA-256 до SQL import.
- Импортировать `events.sql`, посчитать rows и сравнить с manifest; проверить наличие ship-pack/formulas/warnings и их checksums.
- Удалить disposable database даже при assertion failure; вернуть typed result `passed | failed | unknown` и stable failure code.

**Плюсы:** T6 получает повторяемую проверку row-count/content, не трогает production DB и покрывает реальный restore path.  
**Минусы:** CI нужен PostgreSQL service; часть environment checks остаётся integration-only.

### Вариант C3 — полный backup/restore в lab на том же edge image

Проверять не только payload, но и boot/mount/RAID replacement на реальном image.

**Плюсы:** максимальная близость к судовой процедуре.  
**Минусы:** медленно и аппаратно зависимо; непригодно как targeted test каждого изменения.

### Решение

Выбрать **C2** для s13 и оставить C3 как weekly lab job. `test_backup_restore.py` покрывает C2 через fake command/filesystem и, если CI service доступен, один integration marker. Ни один test не запускает replacement command against a real pool.

---

# 🎨🎨🎨 ENTERING CREATIVE PHASE: Algorithm — status, thresholds and alerts

## Компонент D — typed health snapshot

### Вариант D1 — health собирает raw CLI и backup files

`/api/health` сам вызывает `zpool`, `statvfs` и читает backup directory.

**Плюсы:** один endpoint.  
**Минусы:** HTTP слой знает shell parsing, timeout и backup semantics; трудно тестировать и легко задержать health request.

### Вариант D2 — periodic collector + pure status reducer (рекомендуемый)

- Collector adapters с bounded timeout собирают `RaidSnapshot`, `DiskUsage`, `BackupSnapshot` и timestamp.
- Pure reducer преобразует их в `StorageHealth`: `raid_degraded`, `disk_pct`, `backup_last_ok`, `backup_age`, stable `reason_codes`.
- `/api/health` читает последний snapshot; отсутствие свежего snapshot — `unknown`/not-ready, а не успешный empty response.

**Плюсы:** глубокий seam между I/O и policy, быстрый и deterministic API, один snapshot можно отдать exporter и optional event.  
**Минусы:** появляется scheduler/last-sample freshness contract; нужно явно наблюдать stale collector.

### Решение

Выбрать **D2**. Для s13 достаточно callable collector/adapter и pure reducer; production scheduler wiring может быть тонким service entrypoint. Health contract:

- `disk_pct >= 80` → `disk_warning=true` и stable alert code `storage.disk_high`.
- `raid_degraded=true` → unhealthy, отдельный `storage.raid_degraded`.
- backup отсутствует, не complete, checksum failed или `backup_age` превышает configured daily window → unhealthy/stale code.
- threshold comparison inclusive (`80.0` уже alert); unknown input никогда не превращается в 0% или `backup_last_ok=true`.
- optional event имеет dedup key `(code, day)`; health response остаётся источником truth, event failure не скрывает health failure.

---

# Data flow and implementation seams

```mermaid
flowchart LR
  PG[(PostgreSQL events)] --> D[Backup coordinator]
  PACK[Ship-pack allowlist] --> D
  D --> TMP[Atomic staging]
  TMP --> BK[(Backup NVMe)]
  RAID[ZFS adapter] --> R[RaidSnapshot]
  BK --> B[BackupSnapshot]
  R --> H[Pure storage reducer]
  B --> H
  H --> API[/api/health]
  H --> EVT[Optional health event]
  BK --> T6[Disposable restore harness]
```

### Предлагаемый layout

- `apps/edge/storage/raid/`: typed parsing/contract, ZFS adapter boundary, replacement command validation.
- `apps/edge/storage/backup/`: manifest/layout and coordinator; no FastAPI imports.
- `apps/edge/storage/health.py`: pure reducer and stable reason codes; no subprocess.
- `scripts/shipsense-backup-events.sh`: operational entrypoint only.
- `/usr/local/bin/shipsense-backup-events.sh`: install target generated/installed from repo script, not a second source of truth.
- `apps/edge/storage/tests/test_backup_restore.py`: manifest, atomic finalize, restore row-count and degraded/threshold parsing tests.
- `docs/crew/storage-disk-replace-a4.md`: A4 inputs with serial/slot, LED, `zpool status`, replace, resilver, scrub and escalation steps.

## Error and safety contract

- Every subprocess has argv list, timeout and captured exit status; shell strings are never assembled from operator labels.
- Staging is removed on failure; final directory is published only with `COMPLETE` marker.
- Existing complete backups are immutable from the normal daily command.
- Restore verifies checksums before import and uses a disposable target; production DSN is rejected by harness configuration.
- CLI malformed output and missing backup state are explicit `unknown`, not healthy defaults.
- Alert emits once per `(stable_code, UTC date)` and keeps the raw snapshot for diagnosis.

## Test and verification plan

1. Given valid payloads, backup publishes all required files, manifest hashes and final `COMPLETE`.
2. Given command failure, timeout, missing ship-pack file or checksum mismatch, no complete directory is published.
3. Given a complete backup, restore harness imports fixture events and row count equals manifest.
4. Given missing/corrupt SQL or config, restore returns a stable failure code and removes temporary DB.
5. Given ZFS `ONLINE`, `DEGRADED`, `RESILVERING`, malformed and empty outputs, parser maps states without healthy fallback.
6. Given disk usage `79.9`, `80.0`, `100`, missing and invalid values, reducer alerts exactly at inclusive threshold and fails closed on unknown.
7. Given stale/missing backup snapshot, `/api/health` does not report `backup_last_ok=true`.
8. Property tests: `final_path exists ⇒ COMPLETE exists`; published manifest hashes match payload; reducer is monotonic with respect to degraded/unknown inputs; no cleanup removes the only complete backup.

## Acceptance decisions for IMPLEMENT s13

- [x] ZFS mirror chosen; mdraid fallback documented, not implemented in parallel.
- [x] Backup NVMe is outside mirror and has immutable complete-directory marker.
- [x] Daily payload is events + allowlisted ship-pack/config/formulas/warnings.
- [x] Python coordinator + thin shell entrypoint chosen for testability.
- [x] T6 disposable restore harness and weekly real-lab job boundary defined.
- [x] `disk_pct >= 80` and degraded/unknown fail-closed alert policy defined.
- [x] RPO wording corrected: mirror protects single-disk RPO 0; daily export is ≤24h for total-host loss.
- [x] Crew A4 must identify failed disk by serial/slot, not only by ordinal label.

## Rewire

- [x] s13: CR-P2-03 — `closed`; [creative-raid-storage.md](creative-raid-storage.md); Next Phase `BACK IMPLEMENT`.
- [x] decompose index: CR-P2-03 marked ✅; s13 removed from `needs_creative` queue.

## Handoff

- **Done:** BACK CREATIVE CR-P2-03 — selected ZFS mirror, atomic daily backup contract, disposable restore verification, typed storage health and inclusive 80% alert threshold.
- **Files:** [creative-raid-storage.md](creative-raid-storage.md); rewired [s13-i6-raid-backup.md](../../plan/decompose-v1-p2-ship/s13-i6-raid-backup.md) and [decompose index](../../plan/decompose-v1-p2-ship/index.md).
- **Next:** `BACK IMPLEMENT` @s13.
- **Tool / model:** Claude Code + GPT for CREATIVE; implementation runs in a new chat.
- **New chat:** yes — один чат = один atomic subtask.
- **code_changed:** no.
