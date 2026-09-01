# 讀環境變數 / .env。DATABASE_URL、JWT secret（Phase 3 起）都從這裡集中取得，
# 不要在其他地方直接讀 os.environ。

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    environment: str = "dev"
    jwt_secret: str
    jwt_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 天，見 AUTH.md


@lru_cache
def get_settings() -> Settings:
    return Settings()
