"""FastAPI dependency injection."""

from typing import Annotated

from fastapi import Depends

from app.services.text_service import TextService


def get_text_service() -> TextService:
    """Get text service instance."""
    return TextService()


TextServiceDep = Annotated[TextService, Depends(get_text_service)]
