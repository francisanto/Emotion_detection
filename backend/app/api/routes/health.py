"""Health check endpoint."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.schemas.response_schema import APIResponse

router = APIRouter(tags=["health"])


class HealthData(BaseModel):
    """Health check response data."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="UTC timestamp")


@router.get("/health", response_model=APIResponse[HealthData])
async def health_check() -> APIResponse[HealthData]:
    """Check service health and readiness."""
    settings = get_settings()
    return APIResponse(
        success=True,
        data=HealthData(
            status="healthy",
            version=settings.app_version,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
        metadata={"service": settings.app_name},
    )
