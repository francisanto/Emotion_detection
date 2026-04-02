"""Conversation processing service with SQLAlchemy persistence."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import AnalysisRecord, Conversation, Message, User
from app.services.model_loader import get_text_model
from app.services.relationship_metrics_service import RelationshipMetricsService
from app.services.relationship_stage_service import RelationshipStageService

logger = get_logger("conversation_service")


def predict_emotion(text: str) -> Tuple[str, float]:
    """
    Predict emotion for a single text.

    Returns:
      (emotion_category, confidence)
    """
    try:
        prediction = get_text_model().predict(text)
        emotion = str(prediction.get("emotion", "neutral")).strip().lower()
        confidence = float(prediction.get("confidence", 0.5))
        return emotion or "neutral", float(max(0.0, min(1.0, confidence)))
    except Exception as exc:
        logger.warning("Emotion prediction failed; using neutral fallback", extra={"error": str(exc)})
        return "neutral", 0.5


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

    def process_chat(self, conversation_id: int, messages: List[Dict], analysis_day: date | None = None) -> Dict[str, Any]:
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

        # Store relationship metrics for requested analysis day.
        target_day = analysis_day or date.today()
        relationship_metrics = RelationshipMetricsService(self._db).calculate_relationship_metrics(
            conversation_id=conversation_id,
            day=target_day,
        )

        relationship_stage = RelationshipStageService(self._db).update_relationship_stage(conversation_id=conversation_id)

        summary = {
            "participants": {
                "person_a": conversation.person_a.name if conversation.person_a else None,
                "person_b": conversation.person_b.name if conversation.person_b else None,
            },
            "message_count": message_count,
            "emotions_detected": dict(emotion_counter),
            "relationship_metrics": relationship_metrics,
            "relationship_stage": relationship_stage,
        }

        self._db.add(
            AnalysisRecord(
                conversation_id=conversation_id,
                analysis_type="chat",
                payload=summary,
            )
        )
        self._db.commit()
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


def process_chat(conversation_id: int, messages: List[Dict], analysis_day: date | None = None) -> Dict[str, Any]:
    """
    Convenience wrapper with the required signature.

    This opens its own DB session, so it can be called from simple scripts/tests.
    """
    db = SessionLocal()
    try:
        return ConversationService(db).process_chat(conversation_id=conversation_id, messages=messages, analysis_day=analysis_day)
    finally:
        db.close()

