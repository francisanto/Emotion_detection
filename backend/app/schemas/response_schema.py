"""Pydantic schemas for API response wrappers and fusion results."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Consistent JSON response wrapper for all endpoints."""

    success: bool = Field(..., description="Whether the request succeeded")
    data: T | None = Field(default=None, description="Response payload")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Request metadata")


class FusionAnalyzeRequest(BaseModel):
    """Request schema for fusion analysis (text + voice predictions)."""

    text_prediction: dict[str, Any] = Field(
        ...,
        description="Text analysis output containing emotion, stress_level, social_intent, confidence_score",
    )
    voice_prediction: dict[str, Any] = Field(
        ...,
        description="Voice analysis output containing stress_level, emotional_intensity, voice_confidence",
    )


class FusionAnalyzeResponse(BaseModel):
    """Response schema for fusion analysis results."""

    final_emotion: str = Field(..., description="Combined emotional state")
    final_social_intent: str = Field(..., description="Combined social intent")
    combined_stress_level: float = Field(..., ge=0.0, le=1.0, description="Weighted stress level")
    combined_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    fusion_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Details about fusion weights and contributing factors",
    )
