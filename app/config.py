"""Application settings via pydantic-settings. Single source of truth for configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application configuration, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/fluentian"
    )

    # ── Redis ───────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Auth / JWT ──────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # ── AI ──────────────────────────────────────────────
    AI_GATEWAY_API_KEY: str = ""
    AI_GATEWAY_MODEL: str = "google/gemini-2.5-flash"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── Storage (S3-compatible) ─────────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "fluentian-media"
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: str = ""

    # ── Email (Brevo Transactional API) ─────────────────
    BREVO_API_KEY: str = ""
    MAIL_FROM_EMAIL: str = "no-reply@fluentian.binovatechnologies.com"
    MAIL_FROM_NAME: str = "Fluentian"

    # ── Legacy SMTP Email (deprecated, kept for backward compatibility) ──
    MAIL_HOST: str = "smtp.gmail.com"
    MAIL_PORT: int = 465
    MAIL_USER: str = ""
    MAIL_PASS: str = ""
    MAIL_FROM: str = "Fluentian <no-reply@example.com>"

    # ── App ─────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:8080"
    )

    @property
    def is_production(self) -> bool:
        """Check if the app is running in production mode."""
        return self.APP_ENV == "production"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
