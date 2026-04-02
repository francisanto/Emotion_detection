"""Emotion model using HuggingFace transformers."""

from __future__ import annotations

from typing import Any, Dict, List

from transformers import pipeline

from app.core.logging import get_logger
from app.utils.preprocessing import preprocess_text

logger = get_logger("emotion_model")

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

# Normalized emotion labels expected by the system
NORMALIZED_EMOTIONS = {"joy", "sadness", "anger", "fear", "neutral", "love", "surprise", "disgust"}


class EmotionModel:
    """
    Wrapper around a HuggingFace transformers pipeline for emotion detection.

    Uses the `j-hartmann/emotion-english-distilroberta-base` model and exposes:

      - load_model()
      - predict(text: str) -> {"emotion": str, "confidence": float}
      - predict_batch(texts: List[str]) -> List[dict]
    """

    def __init__(self) -> None:
        self._pipeline: Any | None = None
        self.load_model()

    def load_model(self) -> None:
        """Load the transformers pipeline once."""
        if self._pipeline is not None:
            return

        try:
            self._pipeline = pipeline(
                "text-classification",
                model=MODEL_NAME,
                top_k=None,
            )
            logger.info("HuggingFace emotion model loaded", extra={"model_name": MODEL_NAME})
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to load emotion model, falling back to heuristic", extra={"error": str(exc)})
            self._pipeline = None

    @staticmethod
    def _normalize_emotion(label: str) -> str:
        """Map model label to one of the normalized emotion categories."""
        base = label.lower().strip()

        if "surprise" in base:
            return "surprise"
        if "disgust" in base:
            return "disgust"
        if "love" in base:
            return "love"
        if any(k in base for k in ("joy", "happy", "happiness", "positive")):
            return "joy"
        if any(k in base for k in ("sad", "sadness", "sorrow", "depressed")):
            return "sadness"
        if any(k in base for k in ("anger", "angry", "annoy", "rage")):
            return "anger"
        if any(k in base for k in ("fear", "anxious", "anxiety", "worry")):
            return "fear"

        return "neutral"

    def _heuristic_predict(self, text: str) -> Dict[str, Any]:
        """Fallback heuristic prediction if transformers pipeline is unavailable."""
        cleaned = preprocess_text(text)
        lower = cleaned.lower()

        if any(w in lower for w in ("happy", "glad", "joy", "awesome", "great")):
            return {"emotion": "joy", "confidence": 0.8}
        if any(w in lower for w in ("love", "adore", "darling", "beloved", "dear")):
            return {"emotion": "love", "confidence": 0.8}
        if any(w in lower for w in ("sad", "unhappy", "depressed", "down")):
            return {"emotion": "sadness", "confidence": 0.8}
        if any(w in lower for w in ("angry", "mad", "furious", "annoyed")):
            return {"emotion": "anger", "confidence": 0.8}
        if any(w in lower for w in ("scared", "afraid", "worried", "anxious")):
            return {"emotion": "fear", "confidence": 0.8}
        if any(w in lower for w in ("wow", "omg", "amazing", "unexpected")):
            return {"emotion": "surprise", "confidence": 0.75}
        if any(w in lower for w in ("disgust", "gross", "awful", "nasty")):
            return {"emotion": "disgust", "confidence": 0.75}

        return {"emotion": "neutral", "confidence": 0.7}

    def _predict_single(self, text: str) -> Dict[str, Any]:
        if not text:
            return {"emotion": "neutral", "confidence": 0.0}

        if self._pipeline is None:
            return self._heuristic_predict(text)

        try:
            outputs = self._pipeline(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Emotion pipeline prediction failed; using heuristic", extra={"error": str(exc)})
            return self._heuristic_predict(text)

        # The pipeline with top_k=None returns a list of lists of dicts
        if isinstance(outputs, list) and outputs and isinstance(outputs[0], list):
            candidates = outputs[0]
        else:
            # top-1 only
            candidates = [outputs[0]] if isinstance(outputs, list) else [outputs]

        best = max(candidates, key=lambda c: float(c.get("score", 0.0)))
        emotion = self._normalize_emotion(str(best.get("label", "neutral")))
        confidence = float(best.get("score", 0.0))

        return {"emotion": emotion, "confidence": confidence}

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict the dominant emotion for a single text.

        Returns:
            {"emotion": <joy|sadness|anger|fear|neutral>, "confidence": float}
        """
        return self._predict_single(text)

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Batch prediction for a list of texts.
        """
        if not texts:
            return []

        if self._pipeline is None:
            return [self._heuristic_predict(t) for t in texts]

        try:
            outputs = self._pipeline(texts)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Emotion pipeline batch prediction failed; using heuristic", extra={"error": str(exc)})
            return [self._heuristic_predict(t) for t in texts]

        results: List[Dict[str, Any]] = []
        for i, text in enumerate(texts):
            out = outputs[i]
            if isinstance(out, list):
                candidates = out
            else:
                candidates = [out]
            best = max(candidates, key=lambda c: float(c.get("score", 0.0)))
            emotion = self._normalize_emotion(str(best.get("label", "neutral")))
            confidence = float(best.get("score", 0.0))
            results.append({"emotion": emotion, "confidence": confidence})

        return results

