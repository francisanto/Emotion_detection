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
    def _stress_from_emotion(emotion: str) -> float:
        """
        Derive a numeric stress score from the dominant emotion.
        """
        emo = emotion.strip().lower()
        if emo == "joy":
            return 0.2
        if emo == "love":
            return 0.15
        if emo == "surprise":
            return 0.45
        if emo == "disgust":
            return 0.7
        if emo == "neutral":
            return 0.4
        if emo == "sadness":
            return 0.6
        if emo == "fear":
            return 0.8
        if emo == "anger":
            return 0.85
        return 0.5

    @staticmethod
    def _social_intent_from_emotion(emotion: str) -> str:
        """
        Heuristic mapping from emotion to social intent category.
        """
        emo = emotion.strip().lower()
        if emo == "joy":
            return "positive_social"
        if emo == "love":
            return "romantic_affection"
        if emo == "surprise":
            return "high_attention"
        if emo == "disgust":
            return "avoidant"
        if emo == "sadness":
            return "support_seeking"
        if emo == "anger":
            return "confrontational"
        if emo == "fear":
            return "reassurance_seeking"
        return "informational"

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
        social_intent = self._social_intent_from_emotion(emotion)

        confidence_raw = raw_prediction.get("confidence", 0.85)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.85
        confidence = max(0.0, min(1.0, confidence))

        stress_score = self._stress_from_emotion(emotion)

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
