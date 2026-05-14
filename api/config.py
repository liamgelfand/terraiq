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

    # Public URL of the SPA (password reset links, webhook docs). No trailing slash.
    public_app_url: str = "http://localhost:5173"

    # Resend (https://resend.com) — transactional email. If unset, reset links log only.
    resend_api_key: str | None = None
    email_from: str = "TerraIQ <onboarding@resend.dev>"

    # HMAC secret for signing outbound webhooks to customer URLs (job.completed / job.failed)
    webhook_signing_secret: str = "change-me-webhook-signing-secret"

    # Stripe (optional) — checkout + customer portal for pilots
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_pilot_monthly: str | None = None

    # dev | pilot | production — informational for logs/headers
    deployment_profile: str = "dev"

    # Documented retention target for pilot exports / purge copy
    data_retention_days: int = 365

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        if not self.debug and self.jwt_secret == _DEFAULT_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET must be changed from the default before running in production. "
                "Set a long random string in your environment (e.g. via .env)."
            )
        return self


settings = Settings()
