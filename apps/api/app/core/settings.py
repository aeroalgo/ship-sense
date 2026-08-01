from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./shipsense.db"
    SHIP_PACK_PATH: str = "/app/ship-pack"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_STR: str = "/api"
    API_SESSION_IDLE_SEC: int = 28_800
    API_SERIES_MAX_WINDOW_DAYS: int = 90
    API_WS_BUFFER_SIZE: int = 5_000
    API_WS_MAX_TAGS: int = 100
    API_STALE_THRESHOLD_SEC: int = 10
    API_RATE_LIMIT_SERIES: str = "30/min"
    API_RATE_LIMIT_GLOBAL: str = "120/min"
    API_RATE_LIMIT_EVENTS: str = "60/min"
    API_RATE_LIMIT_SESSION: str = "20/min"
    API_COLLECTOR_HEALTH_PATH: str = "/var/lib/shipsense/health/collector.json"
    API_MNEMO_INCLUDE_GENERATORS: bool = False
    BACKUP_DIR: str = "/mnt/backup"
    BACKUP_MAX_AGE_HOURS: float = 24.0
    STORAGE_RAID_POOL: str = "shipsense"
    STORAGE_RAID_COMMAND_TIMEOUT_SEC: float = 10.0
    STORAGE_HEALTH_EVENTS_ENABLED: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = ApiSettings()
