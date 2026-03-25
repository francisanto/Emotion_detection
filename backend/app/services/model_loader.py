"""Singleton model loader to avoid reloading models per request."""

from typing import Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.text_model import EmotionModel
from app.models.voice_model import VoiceModel

logger = get_logger("model_loader")

_text_model_instance: Optional[EmotionModel] = None
_voice_model_instance: Optional[VoiceModel] = None


def get_text_model() -> EmotionModel:
    """Get or create emotion model singleton."""
    global _text_model_instance
    if _text_model_instance is None:
        # settings currently unused but kept for future configurability
        _ = get_settings()
        _text_model_instance = EmotionModel()
        logger.info("Emotion model singleton initialized")
    return _text_model_instance


def get_voice_model() -> VoiceModel:
    """Get or create voice model singleton."""
    global _voice_model_instance
    if _voice_model_instance is None:
        settings = get_settings()
        _voice_model_instance = VoiceModel(model_path=settings.voice_model_path)
        logger.info("Voice model loaded", extra={"model_path": settings.voice_model_path})
    return _voice_model_instance


def reset_models() -> None:
    """Reset model singletons (useful for testing or hot-reload)."""
    global _text_model_instance, _voice_model_instance
    _text_model_instance = None
    _voice_model_instance = None
    logger.info("Models reset")
