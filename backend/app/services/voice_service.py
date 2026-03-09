"""Voice analysis service using MFCC features."""

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.voice_schema import VoiceAnalyzeResponse
from app.services.model_loader import get_voice_model
from app.utils.feature_extraction import extract_mfcc_from_bytes

logger = get_logger("voice_service")


class VoiceService:
    """Service for voice-based emotion and stress detection."""

    def __init__(self) -> None:
        self._model = get_voice_model()
        self._settings = get_settings()

    async def analyze(self, audio_bytes: bytes) -> VoiceAnalyzeResponse:
        """
        Analyze audio for stress, emotional intensity, and confidence.

        Args:
            audio_bytes: Raw audio file bytes (wav, mp3, etc.).

        Returns:
            VoiceAnalyzeResponse with stress_level, emotional_intensity, voice_confidence.
        """
        logger.info("Voice analysis started", extra={"audio_size_bytes": len(audio_bytes)})

        mfcc = extract_mfcc_from_bytes(
            audio_bytes,
            sr=self._settings.sample_rate,
            n_mfcc=self._settings.n_mfcc,
        )
        prediction = self._model.predict(mfcc)

        result = VoiceAnalyzeResponse(
            stress_level=prediction.stress_level,
            emotional_intensity=prediction.emotional_intensity,
            voice_confidence=prediction.voice_confidence,
            dominant_emotion=prediction.dominant_emotion,
        )

        logger.info(
            "Voice analysis completed",
            extra={
                "stress_level": result.stress_level,
                "emotional_intensity": result.emotional_intensity,
            },
        )
        return result
