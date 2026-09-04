from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "recur"
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./recur.db"

    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None

    llm_api_key: str | None = None
    llm_model: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()