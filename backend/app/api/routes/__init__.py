"""API route modules."""

from fastapi import APIRouter

from app.api.routes import fusion, health, text, voice
from app.core.config import get_settings

settings = get_settings()

# Root router for /health (GET /health)
root_router = APIRouter()
root_router.include_router(health.router)

# API v1 router for /api/v1/*
api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(text.router)
api_router.include_router(voice.router)
api_router.include_router(fusion.router)
