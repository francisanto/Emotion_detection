"""Service for relationship stage detection based on historical daily metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import DailyRelationshipMetrics, RelationshipStage

logger = get_logger("relationship_stage_service")


def detect_relationship_stage(metrics_list: List[DailyRelationshipMetrics]) -> str:
    """
    Detect relationship stage from historical DailyRelationshipMetrics.

    Rules:
      - If total_messages < 10 => "stranger"
      - avg_affection thresholds:
        <0.05: friend
        <0.15: interested
        <0.3: crush
        else: romantic
    """
    if not metrics_list:
        return "stranger"

    total_affection = 0.0
    total_positive = 0.0  # computed for completeness (may be used in future rules)
    total_messages = 0

    for m in metrics_list:
        msg_count = int(getattr(m, "message_count", 0) or 0)
        total_messages += msg_count
        # affection_score / positive_score are fractions; weight by message_count
        total_affection += float(getattr(m, "affection_score", 0.0) or 0.0) * msg_count
        total_positive += float(getattr(m, "positive_score", 0.0) or 0.0) * msg_count

    if total_messages < 10:
        return "stranger"

    avg_affection = total_affection / max(1, total_messages)

    if avg_affection < 0.05:
        return "friend"
    if avg_affection < 0.15:
        return "interested"
    if avg_affection < 0.3:
        return "crush"
    return "romantic"


class RelationshipStageService:
    """Compute and persist relationship stage for a conversation."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def update_relationship_stage(self, conversation_id: int) -> str:
        """
        Update relationship stage for a conversation using last 7 days of metrics.
        """
        metrics_list: List[DailyRelationshipMetrics] = (
            self._db.query(DailyRelationshipMetrics)
            .filter(DailyRelationshipMetrics.conversation_id == conversation_id)
            .order_by(DailyRelationshipMetrics.date.desc())
            .limit(7)
            .all()
        )

        stage = detect_relationship_stage(metrics_list)

        existing = (
            self._db.query(RelationshipStage)
            .filter(RelationshipStage.conversation_id == conversation_id)
            .one_or_none()
        )

        updated_at = datetime.utcnow()
        if existing is None:
            existing = RelationshipStage(
                conversation_id=conversation_id,
                stage=stage,
                updated_at=updated_at,
            )
            self._db.add(existing)
        else:
            existing.stage = stage
            existing.updated_at = updated_at

        self._db.commit()

        logger.info(
            "Relationship stage updated",
            extra={
                "conversation_id": conversation_id,
                "stage": stage,
                "updated_at": updated_at.isoformat(),
                "metrics_days_used": len(metrics_list),
            },
        )
        return stage


def update_relationship_stage(conversation_id: int) -> str:
    """
    Convenience wrapper with the required signature.

    Opens its own DB session so it can be called from scripts/tests.
    """
    db = SessionLocal()
    try:
        return RelationshipStageService(db).update_relationship_stage(conversation_id=conversation_id)
    finally:
        db.close()

