"""Progress domain models: UserLessonProgress, UserUnitProgress."""

from datetime import datetime
import uuid
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, func
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
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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
