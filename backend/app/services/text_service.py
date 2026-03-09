"""Text analysis service."""

from typing import Any, Dict

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.text_schema import TextAnalyzeResponse
from app.services.model_loader import get_text_model

logger = get_logger("text_service")


class TextService:
    """Service for text-based emotion and social intent detection."""

    def __init__(self) -> None:
        self._model = get_text_model()
        self._settings = get_settings()

    @staticmethod
    def _stress_label_to_score(label: str) -> float:
        """
        Map a categorical stress level label to a numeric score in [0, 1].
        """
        if not label:
            return 0.5

        normalized = label.strip().lower()
        mapping = {
            "low": 0.2,
            "medium": 0.5,
            "med": 0.5,
            "high": 0.8,
            "very_high": 0.9,
            "very high": 0.9,
        }

        if normalized in mapping:
            return mapping[normalized]

        # Allow numeric labels like "0.7" or "70%"
        try:
            if normalized.endswith("%"):
                value = float(normalized.rstrip("%")) / 100.0
            else:
                value = float(normalized)
            return max(0.0, min(1.0, value))
        except ValueError:
            return 0.5

    async def analyze(self, text: str) -> TextAnalyzeResponse:
        """
        Analyze text for emotion, stress, and social intent.

        Args:
            text: Raw input text.

        Returns:
            TextAnalyzeResponse with emotion, numeric stress_level, social_intent,
            and confidence_score.
        """
        logger.info("Text analysis started", extra={"text_length": len(text)})

        raw_prediction: Dict[str, Any] = self._model.predict(text)

        emotion = str(raw_prediction.get("emotion", "neutral"))
        stress_label = str(raw_prediction.get("stress_level", "medium"))
        social_intent = str(raw_prediction.get("social_intent", "informational"))

        confidence_raw = raw_prediction.get("confidence", 0.85)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.85
        confidence = max(0.0, min(1.0, confidence))

        stress_score = self._stress_label_to_score(stress_label)

        result = TextAnalyzeResponse(
            emotion=emotion,
            stress_level=stress_score,
            social_intent=social_intent,
            confidence_score=confidence,
        )

        logger.info(
            "Text analysis completed",
            extra={
                "emotion": result.emotion,
                "social_intent": result.social_intent,
            },
        )
        return result
