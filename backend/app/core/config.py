"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Emotion & Social Intent Detection API"
    app_version: str = "1.0.0"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "mysql+pymysql://root:root@127.0.0.1:3306/emotion_detection"
    auto_create_database: bool = True
    db_echo: bool = False

    # Model paths (for text emotion model)
    text_model_path: Optional[str] = None
    preload_models_on_startup: bool = True

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
