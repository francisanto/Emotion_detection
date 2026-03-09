"""FastAPI dependency injection."""

from typing import Annotated

from fastapi import Depends

from app.services.fusion_service import FusionService
from app.services.text_service import TextService
from app.services.voice_service import VoiceService


def get_text_service() -> TextService:
    """Get text service instance."""
    return TextService()


def get_voice_service() -> VoiceService:
    """Get voice service instance."""
    return VoiceService()


def get_fusion_service() -> FusionService:
    """Get fusion service instance."""
    return FusionService()


TextServiceDep = Annotated[TextService, Depends(get_text_service)]
VoiceServiceDep = Annotated[VoiceService, Depends(get_voice_service)]
FusionServiceDep = Annotated[FusionService, Depends(get_fusion_service)]
