"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session

from app.api.routes import api_router, root_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.database import get_db, init_db
from app.db.models import Conversation, DailyRelationshipMetrics, RelationshipStage, User
from app.services.conversation_service import ConversationService

settings = get_settings()
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Application starting up")
    init_db()
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Validation error handler (consistent JSON format)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors with consistent response format."""
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "metadata": {
                "error": "Validation error",
                "detail": exc.errors(),
            },
        },
    )


# HTTPException handler (consistent JSON format)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle HTTPException with consistent response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "metadata": {
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP error",
                "detail": exc.detail,
            },
        },
    )


# Unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return consistent error response."""
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "metadata": {
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred",
            },
        },
    )


# Include routers
app.include_router(root_router)  # GET /health
app.include_router(api_router)   # /api/v1/*


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "success": True,
        "data": {
            "message": "Emotion & Social Intent Detection API",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "api_v1": settings.api_v1_prefix,
        },
        "metadata": {},
    }


class TestChatMessage(BaseModel):
    """Incoming message for the /test-chat endpoint."""

    sender: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    timestamp: Optional[datetime] = Field(default=None)


class TestChatRequest(BaseModel):
    """Request body for /test-chat."""

    messages: List[TestChatMessage]


def _get_or_create_user(db: Session, name: str) -> User:
    """Get or create a user by name (used for test endpoint only)."""
    normalized = (name or "").strip() or "Unknown"
    user = db.query(User).filter(User.name == normalized).one_or_none()
    if user is None:
        user = User(name=normalized)
        db.add(user)
        db.flush()
    return user


@app.post("/test-chat")
async def test_chat(payload: TestChatRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Test endpoint to ingest raw chat messages, predict emotions, and compute daily relationship metrics.

    Input:
      { "messages": [ { "sender": "...", "text": "...", "timestamp": optional } ] }
    """
    if not payload.messages:
        return {
            "success": False,
            "data": None,
            "metadata": {"error": "messages must not be empty"},
        }

    unique_senders: List[str] = []
    for m in payload.messages:
        s = (m.sender or "").strip()
        if s and s not in unique_senders:
            unique_senders.append(s)

    # Create a conversation automatically from the first two distinct senders.
    # If only one sender exists, person_a_id == person_b_id.
    sender_a = unique_senders[0] if unique_senders else "Unknown"
    sender_b = unique_senders[1] if len(unique_senders) > 1 else sender_a

    user_a = _get_or_create_user(db, sender_a)
    user_b = _get_or_create_user(db, sender_b)

    conversation = (
        db.query(Conversation)
        .filter(Conversation.person_a_id == user_a.id, Conversation.person_b_id == user_b.id)
        .one_or_none()
    )
    if conversation is None:
        conversation = Conversation(person_a_id=user_a.id, person_b_id=user_b.id)
        db.add(conversation)
        db.flush()

    messages_payload: List[Dict[str, Any]] = [
        {
            "sender": m.sender,
            "text": m.text,
            "timestamp": m.timestamp,
        }
        for m in payload.messages
    ]

    chat_summary = ConversationService(db).process_chat(
        conversation_id=conversation.id,
        messages=messages_payload,
    )

    return {
        "success": True,
        "data": {
            "conversation_id": conversation.id,
            "chat_summary": chat_summary,
            "relationship_metrics": chat_summary.get("relationship_metrics"),
            "relationship_stage": chat_summary.get("relationship_stage"),
        },
        "metadata": {"generated_at": datetime.now(timezone.utc).isoformat()},
    }


@app.post("/analyze-chat")
async def analyze_chat(payload: TestChatRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Analyze chat messages and return relationship stage.

    Input JSON:
      { "messages": [ { "sender": "...", "text": "...", "timestamp": optional } ] }
    """
    # Reuse /test-chat flow
    return await test_chat(payload=payload, db=db)


@app.get("/conversations/{conversation_id}/relationship-summary")
async def get_relationship_summary(conversation_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Return the last 7 days of relationship metrics and current stage.
    """
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        return {
            "success": False,
            "data": None,
            "metadata": {"error": f"Conversation {conversation_id} not found"},
        }

    metrics_rows = (
        db.query(DailyRelationshipMetrics)
        .filter(DailyRelationshipMetrics.conversation_id == conversation_id)
        .order_by(DailyRelationshipMetrics.date.desc())
        .limit(7)
        .all()
    )

    stage_row = (
        db.query(RelationshipStage)
        .filter(RelationshipStage.conversation_id == conversation_id)
        .one_or_none()
    )

    metrics_data = [
        {
            "date": m.date.isoformat(),
            "positive_score": m.positive_score,
            "negative_score": m.negative_score,
            "affection_score": m.affection_score,
            "message_count": m.message_count,
        }
        for m in metrics_rows
    ]

    return {
        "success": True,
        "data": {
            "conversation_id": conversation_id,
            "relationship_stage": stage_row.stage if stage_row else "stranger",
            "stage_updated_at": stage_row.updated_at.isoformat() if stage_row and stage_row.updated_at else None,
            "metrics_last_7_days": metrics_data,
        },
        "metadata": {"generated_at": datetime.now(timezone.utc).isoformat()},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
