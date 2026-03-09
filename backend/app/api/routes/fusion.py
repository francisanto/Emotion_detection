"""Fusion analysis API routes."""

from fastapi import APIRouter

from app.api.dependencies import FusionServiceDep
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.response_schema import APIResponse, FusionAnalyzeRequest, FusionAnalyzeResponse

router = APIRouter(prefix="/fusion", tags=["fusion"])
logger = get_logger("routes.fusion")


@router.post("/analyze", response_model=APIResponse[FusionAnalyzeResponse])
async def analyze_fusion(
    request: FusionAnalyzeRequest,
    service: FusionServiceDep,
) -> APIResponse[FusionAnalyzeResponse]:
    """
    Combine text and voice predictions into final emotional state and social intent.

    Accepts text_prediction and voice_prediction from respective endpoints.
    """
    try:
        result = await service.analyze(
            text_prediction=request.text_prediction,
            voice_prediction=request.voice_prediction,
        )
        return APIResponse(
            success=True,
            data=result,
            metadata={
                "api_version": get_settings().app_version,
            },
        )
    except Exception as e:
        logger.exception("Fusion analysis failed: %s", str(e))
        raise
