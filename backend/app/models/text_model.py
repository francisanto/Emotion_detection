"""Text ML model for emotion and social intent detection using scikit-learn."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import joblib

from app.core.logging import get_logger
from app.utils.preprocessing import preprocess_text

logger = get_logger("text_model")

DEFAULT_TEXT_MODEL_PATH = "models/text_model.joblib"


class TextModel:
    """
    Text model for emotion and social intent detection.

    The model is expected to be a scikit-learn Pipeline persisted with joblib at
    ``models/text_model.joblib`` (or a custom path). The typical pipeline is:

        [text preprocessing] -> TfidfVectorizer -> classifier

    The loaded object should expose a ``predict`` method. By default we assume that
    ``predict([text])`` returns either:

    - A dict with keys: ``emotion``, ``stress_level``, ``social_intent``,
      and optional ``confidence``; or
    - A sequence of three labels: ``(emotion, stress_level, social_intent)``.

    If the model file is missing or prediction fails, the class falls back to a
    lightweight heuristic mock predictor.
    """

    def __init__(self, model_path: str | None = None) -> None:
        """
        Initialize text model.

        Args:
            model_path: Path to a joblib-saved scikit-learn pipeline. If None,
                defaults to ``models/text_model.joblib``.
        """
        self._model_path = model_path or DEFAULT_TEXT_MODEL_PATH
        self._pipeline: Any | None = None
        self.load_model()

    def load_model(self) -> None:
        """
        Load the scikit-learn pipeline from disk using joblib.

        If the file does not exist or loading fails, the model falls back to
        mock predictions.
        """
        path = Path(self._model_path)
        if not path.is_file():
            logger.warning(
                "Text model file not found, using mock predictions",
                extra={"model_path": str(path)},
            )
            self._pipeline = None
            return

        try:
            self._pipeline = joblib.load(path)
            logger.info(
                "Text model loaded successfully",
                extra={"model_path": str(path)},
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Failed to load text model, using mock predictions",
                extra={"model_path": str(path), "error": str(exc)},
            )
            self._pipeline = None

    def _mock_predict(self, text: str) -> Dict[str, Any]:
        """
        Fallback heuristic prediction used when a real model is not available.
        """
        cleaned = preprocess_text(text)
        lower = cleaned.lower()

        emotion = "neutral"
        social_intent = "informational"
        stress_level = "medium"
        confidence = 0.7

        if any(w in lower for w in ("happy", "glad", "joy", "awesome", "great")):
            emotion = "happy"
            social_intent = "positive_social"
            stress_level = "low"
            confidence = 0.8
        elif any(w in lower for w in ("sad", "unhappy", "depressed", "down")):
            emotion = "sad"
            social_intent = "withdrawn"
            stress_level = "medium"
            confidence = 0.8
        elif any(w in lower for w in ("angry", "mad", "furious", "annoyed")):
            emotion = "angry"
            social_intent = "confrontational"
            stress_level = "high"
            confidence = 0.85
        elif "help" in lower or "support" in lower:
            social_intent = "help_seeking"
            stress_level = "medium"
            confidence = 0.8

        return {
            "emotion": emotion,
            "stress_level": stress_level,
            "social_intent": social_intent,
            "confidence": float(confidence),
        }

    def _predict_with_pipeline(self, text: str) -> Dict[str, Any]:
        """
        Run prediction using the loaded scikit-learn pipeline.

        This method is deliberately tolerant of different shapes of model output.
        """
        assert self._pipeline is not None  # for type-checkers

        try:
            raw = self._pipeline.predict([text])
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Text model pipeline prediction failed, using mock predictions",
                extra={"error": str(exc)},
            )
            return self._mock_predict(text)

        # Handle various common output formats
        pred = raw[0]
        result: Dict[str, Any]

        if isinstance(pred, dict):
            result = dict(pred)  # shallow copy
        elif isinstance(pred, (list, tuple)) and len(pred) >= 3:
            emotion, stress_level, social_intent = pred[:3]
            result = {
                "emotion": str(emotion),
                "stress_level": str(stress_level),
                "social_intent": str(social_intent),
            }
        else:
            # Single label model – treat as emotion-only
            result = {
                "emotion": str(pred),
                "stress_level": "medium",
                "social_intent": "informational",
            }

        # Attach a default confidence if not provided by the model
        confidence = result.get("confidence")
        try:
            confidence_val = float(confidence) if confidence is not None else 0.85
        except (TypeError, ValueError):
            confidence_val = 0.85
        result["confidence"] = confidence_val

        return result

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict emotion, stress level, and social intent for a given text.

        Args:
            text: Raw input text.

        Returns:
            dict with keys:
                - ``emotion`` (str)
                - ``stress_level`` (str)
                - ``social_intent`` (str)
                - ``confidence`` (float in [0, 1] as best-effort)
        """
        if not text:
            return self._mock_predict("")

        if self._pipeline is None:
            return self._mock_predict(text)

        return self._predict_with_pipeline(text)
