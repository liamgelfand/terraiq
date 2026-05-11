from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://terraiq:terraiq@localhost:5432/terraiq"
    database_url_sync: str = "postgresql+psycopg2://terraiq:terraiq@localhost:5432/terraiq"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30


settings = Settings()
