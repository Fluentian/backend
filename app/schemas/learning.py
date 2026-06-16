"""Schemas for MVP feedback and placement workflows."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateLessonFeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    category: str = Field(default="general", max_length=50)
    comment: str | None = Field(default=None, max_length=1000)


class LessonFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    lesson_id: UUID
    rating: int
    category: str
    comment: str | None = None
    created_at: datetime


class PlacementSubmissionRequest(BaseModel):
    answers: list[bool]
    detail: dict[str, Any] = Field(default_factory=dict)


class PlacementResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    score: int
    total_questions: int
    assigned_level: str
    created_at: datetime
