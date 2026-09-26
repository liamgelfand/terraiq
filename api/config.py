from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-production-use-a-long-random-string"
_DEFAULT_WEBHOOK_SECRET = "change-me-webhook-signing-secret"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://terraiq:terraiq@localhost:5432/terraiq"
    database_url_sync: str = "postgresql+psycopg2://terraiq:terraiq@localhost:5432/terraiq"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]

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
    webhook_signing_secret: str = _DEFAULT_WEBHOOK_SECRET

    # Stripe (optional) — checkout + customer portal for pilots
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_pilot_monthly: str | None = None

    # Inbox for landing-page demo / pilot requests (Resend). Logged if unset.
    demo_request_email: str | None = None

    # Email that can open the founder leads inbox. Falls back to demo_request_email.
    founding_admin_email: str | None = None

    # Sentry (optional). Frontend uses VITE_SENTRY_DSN separately.
    sentry_dsn: str | None = None

    # Email fleet admins when an optimize job completes or fails.
    notify_job_email: bool = True

    # Plan quotas (None-equivalent: set very high via enterprise plan, not these fields)
    free_jobs_per_month: int = 25
    free_max_corridors: int = 15
    pilot_jobs_per_month: int = 500
    pilot_max_corridors: int = 100

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
        if not self.debug and self.webhook_signing_secret == _DEFAULT_WEBHOOK_SECRET:
            raise ValueError(
                "WEBHOOK_SIGNING_SECRET must be changed from the default before running in production."
            )
        return self


settings = Settings()
