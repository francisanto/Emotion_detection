"""Pydantic schemas for API response wrappers."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Consistent JSON response wrapper for all endpoints."""

    success: bool = Field(..., description="Whether the request succeeded")
    data: T | None = Field(default=None, description="Response payload")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Request metadata")
