from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Values can be overridden using environment variables
    or a .env file.
    """

    app_name: str = Field(
        default="Recur AI Revenue Recovery",
    )

    environment: str = Field(
        default="development",
    )

    debug: bool = Field(
        default=False,
    )

    database_url: str = Field(
        default=(
            f"sqlite:///"
            f"{PROJECT_ROOT / 'data' / 'database' / 'recur.db'}"
        ),
    )

    api_host: str = Field(
        default="0.0.0.0",
    )

    api_port: int = Field(
        default=8000,
    )

    payment_provider: str = Field(
        default="simulator",
    )

    log_level: str = Field(
        default="INFO",
    )

    max_retry_attempts: int = Field(
        default=3,
        ge=1,
    )

    max_customer_contact_count: int = Field(
        default=3,
        ge=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached application settings instance.
    """

    return Settings()