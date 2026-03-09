"""Text analysis API routes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.dependencies import TextServiceDep
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.response_schema import APIResponse
from app.schemas.text_schema import TextAnalyzeRequest, TextAnalyzeResponse

router = APIRouter(prefix="/text", tags=["text"])
logger = get_logger("routes.text")


@router.post("/analyze", response_model=APIResponse[TextAnalyzeResponse])
async def analyze_text(
    request: TextAnalyzeRequest,
    service: TextServiceDep,
) -> APIResponse[TextAnalyzeResponse] | JSONResponse:
    """
    Analyze text for emotion, stress level, and social intent.

    Returns:
        emotion, stress_level, social_intent, confidence_score
    """
    try:
        result = await service.analyze(request.text)
        return APIResponse(
            success=True,
            data=result,
            metadata={
                "api_version": get_settings().app_version,
                "input_length": len(request.text),
            },
        )
    except Exception as e:
        logger.exception("Text analysis failed: %s", str(e))
        raise
