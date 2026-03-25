"""Relationship metrics computation service (daily metrics)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Set, Tuple, Union

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import DailyRelationshipMetrics, Message

logger = get_logger("relationship_metrics_service")


POSITIVE_EMOTIONS: Set[str] = {"joy", "love", "happy"}
NEGATIVE_EMOTIONS: Set[str] = {"anger", "sadness", "fear"}

AFFECTION_KEYWORDS: List[str] = [
    "miss you",
    "love you",
    "take care",
    "nice",
    "proud",
    "thinking of you",
]


def _coerce_to_date(value: Union[date, datetime, str]) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return datetime.fromisoformat(value).date()
    raise TypeError("day must be date, datetime, or ISO date string")


def _affection_present(text: str) -> bool:
    lower = (text or "").lower()
    return any(kw in lower for kw in AFFECTION_KEYWORDS)


class RelationshipMetricsService:
    """Compute and persist daily relationship metrics for a conversation."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def calculate_relationship_metrics(self, conversation_id: int, day: Union[date, datetime, str]) -> Dict[str, Any]:
        """
        Calculate daily relationship metrics between two people.

        Stores results in `DailyRelationshipMetrics`.
        """
        target_day = _coerce_to_date(day)

        # Use naive datetime range for SQLite compatibility
        start_dt = datetime.combine(target_day, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)

        messages: List[Message] = (
            self._db.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.timestamp >= start_dt,
                Message.timestamp < end_dt,
            )
            .all()
        )

        total = len(messages)
        if total == 0:
            positive_score = 0.0
            negative_score = 0.0
            affection_score = 0.0
        else:
            positive_count = 0
            negative_count = 0
            affection_count = 0

            for msg in messages:
                emo = (msg.emotion or "").strip().lower()
                if emo in POSITIVE_EMOTIONS:
                    positive_count += 1
                if emo in NEGATIVE_EMOTIONS:
                    negative_count += 1
                if _affection_present(msg.message_text):
                    affection_count += 1

            positive_score = positive_count / total
            negative_score = negative_count / total
            affection_score = affection_count / total

        # Upsert
        metrics = (
            self._db.query(DailyRelationshipMetrics)
            .filter(
                DailyRelationshipMetrics.conversation_id == conversation_id,
                DailyRelationshipMetrics.date == target_day,
            )
            .one_or_none()
        )

        if metrics is None:
            metrics = DailyRelationshipMetrics(
                conversation_id=conversation_id,
                date=target_day,
                positive_score=positive_score,
                negative_score=negative_score,
                affection_score=affection_score,
                message_count=total,
            )
            self._db.add(metrics)
        else:
            metrics.positive_score = positive_score
            metrics.negative_score = negative_score
            metrics.affection_score = affection_score
            metrics.message_count = total

        self._db.commit()
        self._db.refresh(metrics)

        logger.info(
            "Daily relationship metrics computed",
            extra={
                "conversation_id": conversation_id,
                "date": target_day.isoformat(),
                "positive_score": positive_score,
                "negative_score": negative_score,
                "affection_score": affection_score,
                "message_count": total,
            },
        )

        return {
            "conversation_id": conversation_id,
            "date": target_day.isoformat(),
            "positive_score": positive_score,
            "negative_score": negative_score,
            "affection_score": affection_score,
            "message_count": total,
        }

    def compute_historical_metrics(
        self,
        conversation_id: int,
        start_date: Union[date, datetime, str],
        end_date: Union[date, datetime, str],
    ) -> List[Dict[str, Any]]:
        """Compute metrics for each day in a date range (historical analysis)."""
        start = _coerce_to_date(start_date)
        end = _coerce_to_date(end_date)
        if end < start:
            raise ValueError("end_date must be on or after start_date")

        results: List[Dict[str, Any]] = []
        current = start
        while current <= end:
            results.append(self.calculate_relationship_metrics(conversation_id=conversation_id, day=current))
            current += timedelta(days=1)
        return results


def calculate_relationship_metrics(conversation_id: int, day: Union[date, datetime, str]) -> Dict[str, Any]:
    """
    Convenience wrapper with the required signature.

    Opens its own DB session so it can be used from standalone scripts/tests.
    """
    db = SessionLocal()
    try:
        return RelationshipMetricsService(db).calculate_relationship_metrics(conversation_id=conversation_id, day=day)
    finally:
        db.close()

