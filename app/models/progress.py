"""Progress domain models: UserLessonProgress, UserUnitProgress."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class UserLessonProgress(UUIDMixin, Base):
    """Tracks a user's progress and mastery on a single lesson."""

    __tablename__ = "user_lesson_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<UserLessonProgress id={self.id} user={self.user_id} "
            f"lesson={self.lesson_id} score={self.mastery_score}>"
        )


class UserUnitProgress(UUIDMixin, Base):
    """Tracks whether a user has completed an entire unit."""

    __tablename__ = "user_unit_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("path_units.id", ondelete="CASCADE"), nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<UserUnitProgress id={self.id} user={self.user_id} "
            f"unit={self.unit_id} done={self.is_completed}>"
        )


class SpacedRepetitionItem(UUIDMixin, Base):
    """Tracks a user's progress on a specific question for spaced repetition."""

    __tablename__ = "spaced_repetition_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    easiness_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    next_review_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<SpacedRepetitionItem id={self.id} user={self.user_id} "
            f"question={self.question_id} next_review={self.next_review_date}>"
        )
