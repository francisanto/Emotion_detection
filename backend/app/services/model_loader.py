"""Singleton model loader to avoid reloading models per request."""

from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.text_model import EmotionModel

logger = get_logger("model_loader")

_text_model_instance: Optional[EmotionModel] = None


def get_text_model() -> EmotionModel:
    """Get or create emotion model singleton."""
    global _text_model_instance
    if _text_model_instance is None:
        _ = get_settings()
        _text_model_instance = EmotionModel()
        logger.info("Emotion model singleton initialized")
    return _text_model_instance


def reset_models() -> None:
    """Reset model singletons (useful for testing or hot-reload)."""
    global _text_model_instance
    _text_model_instance = None
    logger.info("Models reset")


def warmup_models() -> None:
    """
    Load and cache models once at startup.

    This also triggers automatic download for remote model weights
    (for example HuggingFace emotion models) on first run.
    """
    get_text_model()
    logger.info("Model warmup completed")
