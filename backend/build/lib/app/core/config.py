from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="dev", validation_alias="APP_ENV")
    app_name: str = "Aerotrust Trusted Messages MVP"
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://aerotrust:aerotrust@localhost:5432/aerotrust",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    admin_jwt_secret: str = Field(
        default="change-me-for-prod",
        validation_alias="ADMIN_JWT_SECRET",
    )
    admin_jwt_algorithm: str = Field(default="HS256", validation_alias="ADMIN_JWT_ALGORITHM")
    admin_access_token_ttl_minutes: int = Field(
        default=480,
        validation_alias="ADMIN_ACCESS_TOKEN_TTL_MINUTES",
    )
    admin_password_hash_iterations: int = Field(
        default=390000,
        validation_alias="ADMIN_PASSWORD_HASH_ITERATIONS",
    )

    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    bot_polling_timeout: int = Field(default=30, validation_alias="BOT_POLLING_TIMEOUT")
    bot_rate_limit_enabled: bool = Field(default=True, validation_alias="BOT_RATE_LIMIT_ENABLED")
    bot_rate_limit_max_events: int = Field(default=10, validation_alias="BOT_RATE_LIMIT_MAX_EVENTS")
    bot_rate_limit_window_seconds: int = Field(
        default=10,
        validation_alias="BOT_RATE_LIMIT_WINDOW_SECONDS",
    )
    bot_rate_limit_block_seconds: int = Field(
        default=30,
        validation_alias="BOT_RATE_LIMIT_BLOCK_SECONDS",
    )
    uploads_root: str = Field(default="/app/uploads", validation_alias="UPLOADS_ROOT")
    max_attachment_size_mb: int = Field(default=10, validation_alias="MAX_ATTACHMENT_SIZE_MB")
    max_attachments_per_report: int = Field(default=5, validation_alias="MAX_ATTACHMENTS_PER_REPORT")
    allowed_document_extensions: str = Field(
        default=".pdf,.doc,.docx,.xls,.xlsx,.txt,.csv,.jpg,.jpeg,.png",
        validation_alias="ALLOWED_DOCUMENT_EXTENSIONS",
    )
    allowed_document_mime_types: str = Field(
        default=(
            "application/pdf,"
            "application/msword,"
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
            "application/vnd.ms-excel,"
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
            "text/plain,"
            "text/csv,"
            "image/jpeg,"
            "image/png"
        ),
        validation_alias="ALLOWED_DOCUMENT_MIME_TYPES",
    )

    @property
    def sync_database_url(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url.replace(
                "postgresql+asyncpg://",
                "postgresql+psycopg://",
                1,
            )
        return self.database_url

    @property
    def max_attachment_size_bytes(self) -> int:
        return self.max_attachment_size_mb * 1024 * 1024

    @property
    def allowed_document_extensions_set(self) -> set[str]:
        return {
            extension.strip().lower()
            for extension in self.allowed_document_extensions.split(",")
            if extension.strip()
        }

    @property
    def allowed_document_mime_types_set(self) -> set[str]:
        return {
            mime_type.strip().lower()
            for mime_type in self.allowed_document_mime_types.split(",")
            if mime_type.strip()
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
