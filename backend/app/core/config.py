"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
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

    # Model paths (for future real model loading)
    text_model_path: Optional[str] = None
    voice_model_path: Optional[str] = None

    # Audio processing
    sample_rate: int = 22050
    n_mfcc: int = 13
    max_audio_duration_seconds: float = 30.0

    # Logging
    log_level: str = "INFO"

    @property
    def max_audio_samples(self) -> int:
        """Maximum number of audio samples based on duration."""
        return int(self.sample_rate * self.max_audio_duration_seconds)


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
