from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-production-use-a-long-random-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://terraiq:terraiq@localhost:5432/terraiq"
    database_url_sync: str = "postgresql+psycopg2://terraiq:terraiq@localhost:5432/terraiq"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30

    # Set DEBUG=true in .env for local dev; production must explicitly set DEBUG=false
    debug: bool = True

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        if not self.debug and self.jwt_secret == _DEFAULT_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET must be changed from the default before running in production. "
                "Set a long random string in your environment (e.g. via .env)."
            )
        return self


settings = Settings()
