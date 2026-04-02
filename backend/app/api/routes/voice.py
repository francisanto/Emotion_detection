"""Voice analysis API routes."""

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import VoiceServiceDep
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import AnalysisRecord
from app.schemas.response_schema import APIResponse
from app.schemas.voice_schema import VoiceAnalyzeResponse

router = APIRouter(prefix="/voice", tags=["voice"])
logger = get_logger("routes.voice")

# Max file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = (".wav", ".mp3", ".ogg", ".flac", ".m4a")


@router.post("/analyze", response_model=APIResponse[VoiceAnalyzeResponse])
async def analyze_voice(
    service: VoiceServiceDep,
    audio: UploadFile = File(..., description="Audio file (wav, mp3, etc.)"),
    analysis_date: date | None = Form(default=None),
    conversation_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
) -> APIResponse[VoiceAnalyzeResponse]:
    """
    Analyze voice for stress level, emotional intensity, and confidence.

    Accepts audio file upload, extracts MFCC features using librosa.

    Returns:
        stress_level, emotional_intensity, voice_confidence
    """
    if audio.filename and not audio.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Use wav, mp3, ogg, flac, or m4a.",
        )

    content = await audio.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)} MB",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        result = await service.analyze(content)
        if conversation_id is not None:
            db.add(
                AnalysisRecord(
                    conversation_id=conversation_id,
                    analysis_type="voice",
                    payload={
                        "analysis_date": analysis_date.isoformat() if analysis_date else None,
                        "dominant_emotion": result.dominant_emotion,
                        "stress_level": result.stress_level,
                        "emotional_intensity": result.emotional_intensity,
                        "voice_confidence": result.voice_confidence,
                    },
                )
            )
            db.commit()
        return APIResponse(
            success=True,
            data=result,
            metadata={
                "api_version": get_settings().app_version,
                "file_name": audio.filename,
                "file_size_bytes": len(content),
                "analysis_date": analysis_date.isoformat() if analysis_date else None,
                "conversation_id": conversation_id,
            },
        )
    except Exception as e:
        logger.exception("Voice analysis failed: %s", str(e))
        raise
