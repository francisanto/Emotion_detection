"""Fusion service to combine text and voice predictions."""

from app.core.logging import get_logger
from app.schemas.response_schema import FusionAnalyzeResponse
from app.schemas.text_schema import TextAnalyzeResponse
from app.schemas.voice_schema import VoiceAnalyzeResponse

logger = get_logger("fusion_service")

# Fusion weights (tune based on modality reliability)
TEXT_WEIGHT = 0.6
VOICE_WEIGHT = 0.4


class FusionService:
    """Service for combining text and voice analysis predictions."""

    def _text_from_dict(self, d: dict) -> tuple[str, float, str, float]:
        """Extract text prediction fields from dict."""
        emotion = str(d.get("emotion", "neutral"))
        stress = float(d.get("stress_level", 0.0))
        intent = str(d.get("social_intent", "informational"))
        confidence = float(d.get("confidence_score", 0.5))
        return emotion, stress, intent, confidence

    def _voice_from_dict(self, d: dict) -> tuple[float, float, float, str | None]:
        """Extract voice prediction fields from dict."""
        stress = float(d.get("stress_level", 0.0))
        intensity = float(d.get("emotional_intensity", 0.0))
        confidence = float(d.get("voice_confidence", 0.5))
        emotion = d.get("dominant_emotion")
        return stress, intensity, confidence, emotion

    def _merge_emotion(
        self,
        text_emotion: str,
        voice_emotion: str | None,
        text_confidence: float,
        voice_confidence: float,
    ) -> str:
        """Combine emotions with weighted confidence."""
        if voice_emotion is None or voice_emotion == "":
            return text_emotion
        # Prefer higher-confidence modality
        if text_confidence >= voice_confidence:
            return text_emotion
        return voice_emotion

    def _merge_intent(
        self,
        text_intent: str,
        text_confidence: float,
    ) -> str:
        """Return social intent (text-only for now)."""
        return text_intent

    async def analyze(
        self,
        text_prediction: dict,
        voice_prediction: dict,
    ) -> FusionAnalyzeResponse:
        """
        Combine text and voice predictions into final emotional state and social intent.

        Args:
            text_prediction: Output from text analysis endpoint.
            voice_prediction: Output from voice analysis endpoint.

        Returns:
            FusionAnalyzeResponse with final_emotion, final_social_intent, etc.
        """
        logger.info("Fusion analysis started")

        te, ts, ti, tc = self._text_from_dict(text_prediction)
        vs, vi, vc, ve = self._voice_from_dict(voice_prediction)

        combined_stress = ts * TEXT_WEIGHT + vs * VOICE_WEIGHT
        combined_confidence = tc * TEXT_WEIGHT + vc * VOICE_WEIGHT
        final_emotion = self._merge_emotion(te, ve, tc, vc)
        final_intent = self._merge_intent(ti, tc)

        metadata = {
            "text_weight": TEXT_WEIGHT,
            "voice_weight": VOICE_WEIGHT,
            "text_emotion": te,
            "voice_emotion": ve,
            "text_stress": ts,
            "voice_stress": vs,
        }

        result = FusionAnalyzeResponse(
            final_emotion=final_emotion,
            final_social_intent=final_intent,
            combined_stress_level=round(combined_stress, 4),
            combined_confidence=round(combined_confidence, 4),
            fusion_metadata=metadata,
        )

        logger.info(
            "Fusion analysis completed",
            extra={
                "final_emotion": result.final_emotion,
                "final_social_intent": result.final_social_intent,
            },
        )
        return result
