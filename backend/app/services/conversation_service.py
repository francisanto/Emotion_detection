"""Conversation processing service (scikit-learn emotion + SQLAlchemy persistence)."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import Conversation, Message, User
from app.services.relationship_metrics_service import RelationshipMetricsService
from app.services.relationship_stage_service import RelationshipStageService
from app.utils.preprocessing import preprocess_text

logger = get_logger("conversation_service")


# --- Model loading (singleton / lazy) ---
_MODEL_DIR = Path(__file__).resolve().parents[2] / "models"  # backend/models/
_EMOTION_MODEL_PATH = _MODEL_DIR / "emotion_model.pkl"
_VECTORIZER_PATH = _MODEL_DIR / "vectorizer.pkl"

_emotion_model: Any | None = None
_vectorizer: Any | None = None
_resources_loaded: bool = False


def _normalize_emotion_label(label: str) -> str:
    """
    Normalize predicted labels into system categories.

    Required categories:
      joy, sadness, anger, fear, neutral
    """
    base = (label or "").strip().lower()
    if base in {"joy", "happy", "happiness"}:
        return "joy"
    if base in {"sadness", "sad", "down", "unhappy", "sorrow"}:
        return "sadness"
    if base in {"anger", "angry"}:
        return "anger"
    if base in {"fear", "scared", "afraid", "anxious", "anxiety"}:
        return "fear"
    if base in {"love"}:
        return "joy"
    if base in {"neutral"}:
        return "neutral"
    return "neutral"


def _load_resources() -> None:
    """Load emotion model + vectorizer once. Fallback to heuristic if missing."""
    global _emotion_model, _vectorizer, _resources_loaded
    if _resources_loaded:
        return

    _resources_loaded = True
    try:
        _emotion_model = joblib.load(_EMOTION_MODEL_PATH)
        _vectorizer = joblib.load(_VECTORIZER_PATH)
        logger.info(
            "Loaded scikit-learn emotion model",
            extra={"emotion_model_path": str(_EMOTION_MODEL_PATH), "vectorizer_path": str(_VECTORIZER_PATH)},
        )
    except Exception as exc:
        # Model files might not be present yet for student projects.
        logger.warning(
            "Could not load emotion_model/vectorizer; using heuristic fallback",
            extra={"error": str(exc), "emotion_model_path": str(_EMOTION_MODEL_PATH), "vectorizer_path": str(_VECTORIZER_PATH)},
        )
        _emotion_model = None
        _vectorizer = None


def predict_emotion(text: str) -> Tuple[str, float]:
    """
    Predict emotion for a single text.

    Returns:
      (emotion_category, confidence)
    """
    _load_resources()
    cleaned = preprocess_text(text)
    lower = cleaned.lower()

    # Fallback heuristic when model isn't available
    if _emotion_model is None or _vectorizer is None:
        if any(w in lower for w in ("happy", "glad", "joy", "awesome", "great", "love")):
            return "joy", 0.70
        if any(w in lower for w in ("sad", "unhappy", "depressed", "down")):
            return "sadness", 0.70
        if any(w in lower for w in ("angry", "mad", "furious", "annoyed")):
            return "anger", 0.75
        if any(w in lower for w in ("scared", "afraid", "fear", "anxious", "worried")):
            return "fear", 0.75
        return "neutral", 0.60

    # sklearn path: vectorizer -> model
    try:
        X = _vectorizer.transform([cleaned])
        pred_label = _emotion_model.predict(X)[0]
        emotion = _normalize_emotion_label(str(pred_label))

        confidence = 0.5
        if hasattr(_emotion_model, "predict_proba"):
            proba = _emotion_model.predict_proba(X)
            # max probability is a reasonable confidence proxy
            if proba is not None and len(proba) > 0:
                confidence = float(max(proba[0]))
        return emotion, float(max(0.0, min(1.0, confidence)))
    except Exception as exc:
        logger.warning("Emotion prediction failed; using heuristic fallback", extra={"error": str(exc)})
        return predict_emotion(text)


def _parse_timestamp(value: Any, default_ts: datetime) -> datetime:
    """Best-effort parsing for optional message timestamp."""
    if value is None:
        return default_ts
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return default_ts
    return default_ts


class ConversationService:
    """Store OCR/extracted messages and their emotion predictions in the database."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _get_or_create_user(self, name: str) -> User:
        """Resolve a sender name to a `User` row, creating it if necessary."""
        normalized = (name or "").strip() or "Unknown"
        user = self._db.query(User).filter(User.name == normalized).one_or_none()
        if user is None:
            user = User(name=normalized)
            self._db.add(user)
            self._db.flush()  # assign id
            logger.info("Created new user for conversation message", extra={"name": normalized, "user_id": user.id})
        return user

    def process_chat(self, conversation_id: int, messages: List[Dict]) -> Dict[str, Any]:
        """
        Process and persist a list of chat messages.

        Input message dict fields:
          - sender: str
          - text: str
          - timestamp: optional (datetime / ISO string / epoch seconds)
        """
        logger.info(
            "Processing chat messages",
            extra={"conversation_id": conversation_id, "message_count": len(messages)},
        )

        # Ensure the conversation exists (defensive)
        conversation = self._db.get(Conversation, conversation_id)
        if conversation is None:
            raise ValueError(f"Conversation with id {conversation_id} does not exist")

        emotion_counter: Counter[str] = Counter()
        now = datetime.now(timezone.utc)

        for msg in messages:
            sender_name = str(msg.get("sender", "")).strip()
            text = str(msg.get("text", "")).strip()
            if not text:
                continue

            timestamp_value = msg.get("timestamp")
            ts = _parse_timestamp(timestamp_value, default_ts=now)

            user = self._get_or_create_user(sender_name)
            emotion, confidence = predict_emotion(text)

            emotion_counter[emotion] += 1

            self._db.add(
                Message(
                    conversation_id=conversation_id,
                    sender_id=user.id,
                    message_text=text,
                    emotion=emotion,
                    emotion_score=confidence,
                    timestamp=ts,
                )
            )

        self._db.commit()

        message_count = sum(emotion_counter.values())

        # Store today's relationship metrics (used later to compute the stage).
        relationship_metrics = RelationshipMetricsService(self._db).calculate_relationship_metrics(
            conversation_id=conversation_id,
            day=date.today(),
        )

        relationship_stage = RelationshipStageService(self._db).update_relationship_stage(conversation_id=conversation_id)

        summary = {
            "message_count": message_count,
            "emotions_detected": dict(emotion_counter),
            "relationship_metrics": relationship_metrics,
            "relationship_stage": relationship_stage,
        }
        logger.info(
            "Conversation processing completed",
            extra={
                "conversation_id": conversation_id,
                "message_count": message_count,
                "emotions_detected": summary["emotions_detected"],
                "relationship_stage": relationship_stage,
            },
        )
        return summary


def process_chat(conversation_id: int, messages: List[Dict]) -> Dict[str, Any]:
    """
    Convenience wrapper with the required signature.

    This opens its own DB session, so it can be called from simple scripts/tests.
    """
    db = SessionLocal()
    try:
        return ConversationService(db).process_chat(conversation_id=conversation_id, messages=messages)
    finally:
        db.close()

