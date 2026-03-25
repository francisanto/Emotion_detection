"""Voice analysis API routes."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.dependencies import VoiceServiceDep
from app.core.config import get_settings
from app.core.logging import get_logger
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
        return APIResponse(
            success=True,
            data=result,
            metadata={
                "api_version": get_settings().app_version,
                "file_name": audio.filename,
                "file_size_bytes": len(content),
            },
        )
    except Exception as e:
        logger.exception("Voice analysis failed: %s", str(e))
        raise
