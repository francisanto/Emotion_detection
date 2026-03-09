"""Pydantic schemas for voice analysis."""

from typing import Optional

from pydantic import BaseModel, Field


class VoiceAnalyzeResponse(BaseModel):
    """Response schema for voice analysis results."""

    stress_level: float = Field(..., ge=0.0, le=1.0, description="Voice stress level 0-1")
    emotional_intensity: float = Field(..., ge=0.0, le=1.0, description="Emotional intensity 0-1")
    voice_confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence 0-1")
    dominant_emotion: Optional[str] = Field(None, description="Dominant emotion from voice")
