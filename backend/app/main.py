"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased

from app.api.routes import api_router, root_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.database import get_db, init_db
from app.db.models import Conversation, DailyRelationshipMetrics, Message, RelationshipStage, User
from app.services.conversation_service import ConversationService
from app.services.model_loader import warmup_models
from app.services.ocr_service import extract_chat_text

settings = get_settings()
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Application starting up")
    init_db()
    if settings.preload_models_on_startup:
        warmup_models()
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow frontend dev servers to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    analysis_date: Optional[date] = Field(default=None)
    conversation_id: Optional[int] = Field(default=None)


def _get_or_create_user(db: Session, name: str) -> User:
    """Get or create a user by name (used for test endpoint only)."""
    normalized = (name or "").strip() or "Unknown"
    user = db.query(User).filter(User.name == normalized).one_or_none()
    if user is None:
        user = User(name=normalized)
        db.add(user)
        db.flush()
    return user


def _get_current_mood(db: Session, conversation_id: int) -> str:
    """Return latest detected mood for a conversation."""
    last_message = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.desc())
        .first()
    )
    if not last_message or not last_message.emotion:
        return "neutral"
    return str(last_message.emotion).lower()


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

    conversation: Conversation | None = None
    if payload.conversation_id is not None:
        conversation = db.get(Conversation, payload.conversation_id)

    if conversation is None:
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

    default_ts = None
    if payload.analysis_date is not None:
        default_ts = datetime.combine(payload.analysis_date, time(hour=12, minute=0, second=0)).replace(tzinfo=timezone.utc)

    messages_payload: List[Dict[str, Any]] = []
    for m in payload.messages:
        messages_payload.append(
            {
                "sender": m.sender,
                "text": m.text,
                "timestamp": m.timestamp or default_ts,
            }
        )

    chat_summary = ConversationService(db).process_chat(
        conversation_id=conversation.id,
        messages=messages_payload,
        analysis_day=payload.analysis_date,
    )

    return {
        "success": True,
        "data": {
            "conversation_id": conversation.id,
            "chat_summary": chat_summary,
            "relationship_metrics": chat_summary.get("relationship_metrics"),
            "relationship_stage": chat_summary.get("relationship_stage"),
            "current_mood": _get_current_mood(db, conversation.id),
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


@app.post("/analyze-chat-image")
async def analyze_chat_image(
    image: UploadFile = File(..., description="Chat screenshot image"),
    analysis_date: date | None = None,
    conversation_id: int | None = None,
    sender_a: str | None = None,
    sender_b: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Analyze a chat screenshot:
      image -> OCR -> structured messages -> emotion/relationship pipeline.
    """
    content = await image.read()
    if not content:
        return {
            "success": False,
            "data": None,
            "metadata": {"error": "Empty image file"},
        }

    import tempfile
    from pathlib import Path

    suffix = Path(image.filename or "upload.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        extracted_messages = extract_chat_text(tmp_path)
    except Exception as exc:
        logger.exception("Image OCR processing failed: %s", str(exc))
        return {
            "success": False,
            "data": None,
            "metadata": {"error": "Image to text processing failed. Ensure Tesseract OCR is installed."},
        }
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass

    if not extracted_messages:
        extracted_messages = [
            {
                "sender": "Unknown",
                "text": "Image text was unclear; using fallback message for analysis.",
            }
        ]

    if analysis_date is not None:
        default_ts = datetime.combine(analysis_date, time(hour=12, minute=0, second=0)).replace(tzinfo=timezone.utc)
        extracted_messages = [
            {**m, "timestamp": m.get("timestamp") or default_ts}
            for m in extracted_messages
        ]

    conversation: Conversation | None = None
    if conversation_id is not None:
        conversation = db.get(Conversation, conversation_id)

    if conversation is None and sender_a and sender_b:
        user_a = _get_or_create_user(db, sender_a)
        user_b = _get_or_create_user(db, sender_b)
    elif conversation is None:
        unique_senders: List[str] = []
        for m in extracted_messages:
            s = str(m.get("sender", "")).strip()
            if s and s not in unique_senders:
                unique_senders.append(s)
        sa = unique_senders[0] if unique_senders else "Unknown"
        sb = unique_senders[1] if len(unique_senders) > 1 else sa
        user_a = _get_or_create_user(db, sa)
        user_b = _get_or_create_user(db, sb)

        conversation = (
            db.query(Conversation)
            .filter(Conversation.person_a_id == user_a.id, Conversation.person_b_id == user_b.id)
            .one_or_none()
        )
        if conversation is None:
            conversation = Conversation(person_a_id=user_a.id, person_b_id=user_b.id)
            db.add(conversation)
            db.flush()

    chat_summary = ConversationService(db).process_chat(
        conversation_id=conversation.id,
        messages=extracted_messages,
        analysis_day=analysis_date,
    )

    return {
        "success": True,
        "data": {
            "conversation_id": conversation.id,
            "extracted_message_count": len(extracted_messages),
            "chat_summary": chat_summary,
            "relationship_metrics": chat_summary.get("relationship_metrics"),
            "relationship_stage": chat_summary.get("relationship_stage"),
            "current_mood": _get_current_mood(db, conversation.id),
        },
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ocr_warning": "Low-confidence OCR fallback was used." if len(extracted_messages) == 1 and extracted_messages[0].get("sender") == "Unknown" else None,
        },
    }


@app.get("/conversations/{conversation_id}/relationship-summary")
async def get_relationship_summary(
    conversation_id: int,
    end_date: date | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
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

    by_date = {
        m.date: {
            "date": m.date.isoformat(),
            "positive_score": m.positive_score,
            "negative_score": m.negative_score,
            "affection_score": m.affection_score,
            "message_count": m.message_count,
        }
        for m in metrics_rows
    }
    latest_day = end_date or (max(by_date.keys()) if by_date else date.today())
    metrics_data = []
    for i in range(6, -1, -1):
        day = latest_day - timedelta(days=i)
        row = by_date.get(
            day,
            {
                "date": day.isoformat(),
                "positive_score": 0.0,
                "negative_score": 0.0,
                "affection_score": 0.0,
                "message_count": 0,
            },
        )
        metrics_data.append(row)
    emotion_rows = (
        db.query(Message.emotion)
        .filter(Message.conversation_id == conversation_id)
        .all()
    )
    emotion_counts: Dict[str, int] = {}
    for (emo,) in emotion_rows:
        key = (emo or "neutral").lower()
        emotion_counts[key] = emotion_counts.get(key, 0) + 1

    return {
        "success": True,
        "data": {
            "conversation_id": conversation_id,
            "participants": {
                "person_a": conversation.person_a.name if conversation.person_a else None,
                "person_b": conversation.person_b.name if conversation.person_b else None,
            },
            "relationship_stage": stage_row.stage if stage_row else "stranger",
            "current_mood": _get_current_mood(db, conversation_id),
            "stage_updated_at": stage_row.updated_at.isoformat() if stage_row and stage_row.updated_at else None,
            "metrics_last_7_days": metrics_data,
            "graph_analysis": {
                "labels": [m["date"] for m in metrics_data],
                "positive_series": [m["positive_score"] for m in metrics_data],
                "negative_series": [m["negative_score"] for m in metrics_data],
                "affection_series": [m["affection_score"] for m in metrics_data],
            },
            "emotion_counts": emotion_counts,
        },
        "metadata": {"generated_at": datetime.now(timezone.utc).isoformat()},
    }


@app.get("/relationship-stages")
async def get_relationship_stage_groups(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Group known conversations by current relationship stage, including participant names.
    """
    person_a_alias = aliased(User)
    person_b_alias = aliased(User)
    rows = (
        db.query(RelationshipStage, Conversation, person_a_alias, person_b_alias)
        .join(Conversation, RelationshipStage.conversation_id == Conversation.id)
        .join(person_a_alias, Conversation.person_a_id == person_a_alias.id)
        .join(person_b_alias, Conversation.person_b_id == person_b_alias.id)
        .all()
    )

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for stage_row, conversation, person_a, person_b in rows:
        stage = stage_row.stage
        grouped.setdefault(stage, []).append(
            {
                "conversation_id": conversation.id,
                "person_a": person_a.name,
                "person_b": person_b.name,
                "updated_at": stage_row.updated_at.isoformat() if stage_row.updated_at else None,
            }
        )

    return {
        "success": True,
        "data": grouped,
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
