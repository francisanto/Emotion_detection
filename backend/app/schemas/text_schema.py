"""Pydantic schemas for text analysis."""

from pydantic import BaseModel, Field


class TextAnalyzeRequest(BaseModel):
    """Request schema for text analysis endpoint."""

    text: str = Field(..., min_length=1, max_length=10000, description="Input text to analyze")


class TextAnalyzeResponse(BaseModel):
    """Response schema for text analysis results."""

    emotion: str = Field(..., description="Detected emotion label")
    stress_level: float = Field(..., ge=0.0, le=1.0, description="Stress level from 0 to 1")
    social_intent: str = Field(..., description="Detected social intent")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence 0-1")
