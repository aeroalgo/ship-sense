from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./shipsense.db"
    SHIP_PACK_PATH: str = ""
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_V1_STR: str = "/api"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = ApiSettings()
