from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration.

    Secrets are supplied through environment variables or a local .env file.
    Defaults are intentionally limited to non-sensitive local-development values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "telegram-file-store"
    app_env: str = Field(default="development", pattern="^(development|test|staging|production)$")
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    telegram_bot_token: str = Field(min_length=1)
    telegram_admin_ids: str = ""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/telegram_file_store"
    redis_url: str = "redis://localhost:6379/0"

    @property
    def admin_ids(self) -> frozenset[int]:
        values: set[int] = set()
        for raw in self.telegram_admin_ids.split(","):
            item = raw.strip()
            if item:
                values.add(int(item))
        return frozenset(values)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
