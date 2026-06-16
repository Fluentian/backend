"""MVP learning workflows: lesson feedback and placement scoring."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.content import Lesson
from app.models.learning import LessonFeedback, PlacementAttempt
from app.models.user import ProficiencyLevel, User


async def create_lesson_feedback(
    db: AsyncSession,
    user: User,
    lesson_id: UUID,
    rating: int,
    category: str,
    comment: str | None,
) -> LessonFeedback:
    """Create learner feedback for a real lesson."""
    lesson = (
        await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    ).scalar_one_or_none()
    if lesson is None:
        raise NotFoundError("Lesson not found")

    feedback = LessonFeedback(
        user_id=user.id,
        lesson_id=lesson_id,
        rating=rating,
        category=category.strip().lower() or "general",
        comment=comment.strip() if comment else None,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def list_lesson_feedback(
    db: AsyncSession, lesson_id: UUID | None = None
) -> list[LessonFeedback]:
    """List feedback for admin review/export."""
    query = select(LessonFeedback).order_by(LessonFeedback.created_at.desc())
    if lesson_id is not None:
        query = query.where(LessonFeedback.lesson_id == lesson_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def submit_placement(
    db: AsyncSession,
    user: User,
    answers: list[bool],
    detail: dict,
) -> PlacementAttempt:
    """Score a basic placement attempt and update the learner's current level."""
    total = len(answers)
    if total == 0:
        assigned = ProficiencyLevel.a0
        score = 0
    else:
        score = sum(1 for answer in answers if answer)
        ratio = score / total
        if ratio >= 0.8:
            assigned = ProficiencyLevel.a2
        elif ratio >= 0.5:
            assigned = ProficiencyLevel.a1
        else:
            assigned = ProficiencyLevel.a0

    user.current_level = assigned
    attempt = PlacementAttempt(
        user_id=user.id,
        score=score,
        total_questions=total,
        assigned_level=assigned.value,
        answers={"correct": answers, "detail": detail},
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt
