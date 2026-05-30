"""Shared Pydantic schemas: pagination, message responses."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    detail: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
