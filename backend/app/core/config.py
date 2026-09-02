from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    environment: str = "dev"
    jwt_secret: str
    jwt_ttl_seconds: int = 60 * 60 * 24 * 30
    anthropic_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
