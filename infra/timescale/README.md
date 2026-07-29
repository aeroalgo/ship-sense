# Локальная инфраструктура базы данных (TimescaleDB)

Этот каталог содержит конфигурацию базы данных для разработки проекта ShipSense.

## Подключение и параметры
* **СУБД**: TimescaleDB 16 (основано на PostgreSQL 16)
* **Docker Image**: `timescale/timescaledb:2.14.2-pg16`
* **Имя контейнера**: `shipsense-db`
* **Credentials**: `POSTGRES_DB=shipsense`, `POSTGRES_USER=shipsense`, `POSTGRES_PASSWORD=shipsense`
* **Порт**: `5432:5432`
* **Volume**: `tsdata` (именованный том для сохранения данных)
* **shm_size**: `512mb`
* **DATABASE_URL**: `postgresql://shipsense:shipsense@localhost:5432/shipsense`

## Управление базой данных

### 1. Запуск базы данных
Для запуска СУБД отдельно от всего остального стека используется профиль `storage-dev`:
```bash
docker compose --profile storage-dev up -d db
```

Или с помощью вспомогательного скрипта:
```bash
./scripts/dev-db-up.sh
```

### 2. Проверка статуса (Healthcheck)
Убедиться, что база данных запущена и принимает подключения:
```bash
docker compose --profile storage-dev exec db pg_isready -U shipsense
```

### 3. Применение миграций (Alembic)
Для применения миграций используйте следующую команду из корня репозитория:
```bash
DATABASE_URL=postgresql://shipsense:shipsense@localhost:5432/shipsense .venv/bin/alembic upgrade head
```

### 4. Проверка расширений и схемы
Подключитесь к базе данных и проверьте установленные расширения и схему:
```bash
docker compose --profile storage-dev exec -it db psql -U shipsense -d shipsense
```
Внутри консоли psql можно выполнить запросы для проверки:
* Проверка расширений: `\dx` (должны быть включены `timescaledb` и `uuid-ossp`)
* Проверка схем: `\dn` (должна быть схема `shipsense`)

### 5. Откат и повторное применение миграций (Downgrade/Upgrade)
Для отката миграции на один шаг назад:
```bash
DATABASE_URL=postgresql://shipsense:shipsense@localhost:5432/shipsense .venv/bin/alembic downgrade -1
```

Для наката миграций:
```bash
DATABASE_URL=postgresql://shipsense:shipsense@localhost:5432/shipsense .venv/bin/alembic upgrade head
```

### 6. Остановка и очистка данных (Teardown)
Для остановки базы данных с сохранением тома данных:
```bash
docker compose --profile storage-dev stop db
```

Для полной очистки (удаления контейнера и тома данных):
```bash
docker compose --profile storage-dev down -v
```
