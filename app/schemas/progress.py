"""Progress schemas: lesson completion, stats, enrollment."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

# ── Lesson Completion ───────────────────────────────────


class AnswerPayload(BaseModel):
    question_id: UUID
    answer: Any
    is_correct: bool


class CompleteLessonRequest(BaseModel):
    score: float
    answers: list[AnswerPayload]
    time_seconds: int

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Score must be between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            msg = "Score must be between 0.0 and 1.0"
            raise ValueError(msg)
        return v


class CompleteLessonResponse(BaseModel):
    xp_earned: int
    new_xp_total: int
    streak_days: int
    hearts_remaining: int
    lesson_completed: bool
    unit_completed: bool


# ── Progress Records ────────────────────────────────────


class LessonProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    lesson_id: UUID
    mastery_score: float
    completed: bool
    completed_at: datetime | None = None
    created_at: datetime


class UnitProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    unit_id: UUID
    is_completed: bool
    created_at: datetime


# ── Stats ───────────────────────────────────────────────


class UserStatsResponse(BaseModel):
    total_xp: int
    streak_days: int
    lessons_completed: int
    units_completed: int
    hearts: int
    current_level: str
    weekly_xp: int


# ── Enrollment ──────────────────────────────────────────


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    course_id: UUID
    enrolled_at: datetime
    is_active: bool
