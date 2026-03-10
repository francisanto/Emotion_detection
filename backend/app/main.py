"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import api_router, root_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.database import init_db

settings = get_settings()
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Application starting up")
    init_db()
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Validation error handler (consistent JSON format)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors with consistent response format."""
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "metadata": {
                "error": "Validation error",
                "detail": exc.errors(),
            },
        },
    )


# HTTPException handler (consistent JSON format)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle HTTPException with consistent response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "metadata": {
                "error": exc.detail if isinstance(exc.detail, str) else "HTTP error",
                "detail": exc.detail,
            },
        },
    )


# Unhandled exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return consistent error response."""
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "metadata": {
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else "An unexpected error occurred",
            },
        },
    )


# Include routers
app.include_router(root_router)  # GET /health
app.include_router(api_router)   # /api/v1/*


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "success": True,
        "data": {
            "message": "Emotion & Social Intent Detection API",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "api_v1": settings.api_v1_prefix,
        },
        "metadata": {},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
