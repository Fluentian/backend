"""Progress service — lesson completion, XP, streaks, hearts, enrollment."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    PASS_THRESHOLD,
    XP_MULTIPLIER_FAIL,
    XP_MULTIPLIER_GOOD,
    XP_MULTIPLIER_PASS,
    XP_MULTIPLIER_PERFECT,
)
from app.core.exceptions import ConflictError, NotFoundError
from app.models.content import CourseEnrollment, Lesson, Question
from app.models.progress import UserLessonProgress, UserUnitProgress
from app.models.user import User
from app.schemas.progress import AnswerPayload
from app.utils.content_payloads import grade_answer, normalize_question_model

logger = logging.getLogger(__name__)


async def complete_lesson(
    db: AsyncSession,
    user: User,
    lesson_id: UUID,
    score: float,
    answers: list[AnswerPayload],
    time_seconds: int,
) -> dict:
    """Complete a lesson: award XP, update streak, deduct hearts."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise NotFoundError("Lesson not found")

    questions_result = await db.execute(
        select(Question).where(Question.lesson_id == lesson_id)
    )
    questions = list(questions_result.scalars().all())
    for question in questions:
        normalize_question_model(question)
    question_by_id = {q.id: q for q in questions}

    if answers and question_by_id:
        graded: list[AnswerPayload] = []
        correct_count = 0
        for submitted in answers:
            question = question_by_id.get(submitted.question_id)
            is_correct = (
                grade_answer(question, submitted.answer)
                if question is not None
                else submitted.is_correct
            )
            if is_correct:
                correct_count += 1
            graded.append(
                AnswerPayload(
                    question_id=submitted.question_id,
                    answer=submitted.answer,
                    is_correct=is_correct,
                )
            )
        answers = graded
        score = correct_count / len(answers)

    if score >= 1.0:
        multiplier = XP_MULTIPLIER_PERFECT
    elif score >= 0.8:
        multiplier = XP_MULTIPLIER_GOOD
    elif score >= PASS_THRESHOLD:
        multiplier = XP_MULTIPLIER_PASS
    else:
        multiplier = XP_MULTIPLIER_FAIL

    xp_earned = int(lesson.xp_reward * multiplier)
    wrong_answers = sum(1 for a in answers if not a.is_correct)
    user.hearts = max(0, user.hearts - wrong_answers)

    progress_result = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id == lesson_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    lesson_completed = score >= PASS_THRESHOLD
    now = datetime.now(UTC)

    if not progress:
        progress = UserLessonProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            mastery_score=score,
            completed=lesson_completed,
            completed_at=now if lesson_completed else None,
        )
        db.add(progress)
    else:
        progress.mastery_score = max(progress.mastery_score, score)
        if lesson_completed and not progress.completed:
            progress.completed = True
            progress.completed_at = now

    user.xp_total += xp_earned
    today = now.date()
    if user.last_activity_date is None or user.last_activity_date.date() != today:
        if user.last_activity_date and user.last_activity_date.date() == today - timedelta(days=1):
            user.streak_days += 1
        elif user.last_activity_date is None or user.last_activity_date.date() < today - timedelta(
            days=1
        ):
            user.streak_days = 1
        user.last_activity_date = now

    unit_completed = False
    if lesson_completed:
        unit_completed = await _check_unit_completion(db, user.id, lesson.unit_id)

    await db.commit()
    return {
        "xp_earned": xp_earned,
        "new_xp_total": user.xp_total,
        "streak_days": user.streak_days,
        "hearts_remaining": user.hearts,
        "lesson_completed": lesson_completed,
        "unit_completed": unit_completed,
    }


async def get_user_lesson_progress(
    db: AsyncSession, user_id: UUID, completed: bool | None = None, offset: int = 0, limit: int = 20
) -> tuple[list[UserLessonProgress], int]:
    """Get lesson progress records for a user."""
    query = select(UserLessonProgress).where(UserLessonProgress.user_id == user_id)
    count_query = (
        select(func.count())
        .select_from(UserLessonProgress)
        .where(UserLessonProgress.user_id == user_id)
    )
    if completed is not None:
        query = query.where(UserLessonProgress.completed == completed)
        count_query = count_query.where(UserLessonProgress.completed == completed)
    total = (await db.execute(count_query)).scalar() or 0
    items = list((await db.execute(query.offset(offset).limit(limit))).scalars().all())
    return items, total


async def get_user_unit_progress(
    db: AsyncSession, user_id: UUID, offset: int = 0, limit: int = 20
) -> tuple[list[UserUnitProgress], int]:
    """Get unit progress records for a user."""
    total = (
        await db.execute(
            select(func.count())
            .select_from(UserUnitProgress)
            .where(UserUnitProgress.user_id == user_id)
        )
    ).scalar() or 0
    items = list(
        (
            await db.execute(
                select(UserUnitProgress)
                .where(UserUnitProgress.user_id == user_id)
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return items, total


async def get_user_stats(db: AsyncSession, user: User) -> dict:
    """Aggregate stats for the current user."""
    now = datetime.now(UTC)
    week_start = now - timedelta(days=7)
    lessons_completed = (
        await db.execute(
            select(func.count())
            .select_from(UserLessonProgress)
            .where(UserLessonProgress.user_id == user.id, UserLessonProgress.completed.is_(True))
        )
    ).scalar() or 0
    units_completed = (
        await db.execute(
            select(func.count())
            .select_from(UserUnitProgress)
            .where(UserUnitProgress.user_id == user.id, UserUnitProgress.is_completed.is_(True))
        )
    ).scalar() or 0
    weekly_xp = (
        await db.execute(
            select(func.coalesce(func.sum(Lesson.xp_reward), 0))
            .select_from(UserLessonProgress)
            .join(Lesson, UserLessonProgress.lesson_id == Lesson.id)
            .where(
                UserLessonProgress.user_id == user.id,
                UserLessonProgress.completed.is_(True),
                UserLessonProgress.completed_at >= week_start,
            )
        )
    ).scalar() or 0
    return {
        "total_xp": user.xp_total,
        "streak_days": user.streak_days,
        "lessons_completed": lessons_completed,
        "units_completed": units_completed,
        "hearts": user.hearts,
        "current_level": user.current_level.value,
        "weekly_xp": int(weekly_xp),
    }


async def enroll_in_course(db: AsyncSession, user_id: UUID, course_id: UUID) -> CourseEnrollment:
    """Enroll a user in a course."""
    existing = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == user_id, CourseEnrollment.course_id == course_id
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Already enrolled in this course")
    enrollment = CourseEnrollment(user_id=user_id, course_id=course_id)
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def _check_unit_completion(db: AsyncSession, user_id: UUID, unit_id: UUID) -> bool:
    """Check if all lessons in a unit are completed."""
    total_lessons = (
        await db.execute(select(func.count()).select_from(Lesson).where(Lesson.unit_id == unit_id))
    ).scalar() or 0
    if total_lessons == 0:
        return False
    completed_lessons = (
        await db.execute(
            select(func.count())
            .select_from(UserLessonProgress)
            .join(Lesson, UserLessonProgress.lesson_id == Lesson.id)
            .where(
                UserLessonProgress.user_id == user_id,
                Lesson.unit_id == unit_id,
                UserLessonProgress.completed.is_(True),
            )
        )
    ).scalar() or 0
    if completed_lessons >= total_lessons:
        up_result = await db.execute(
            select(UserUnitProgress).where(
                UserUnitProgress.user_id == user_id, UserUnitProgress.unit_id == unit_id
            )
        )
        unit_progress = up_result.scalar_one_or_none()
        if not unit_progress:
            db.add(UserUnitProgress(user_id=user_id, unit_id=unit_id, is_completed=True))
        else:
            unit_progress.is_completed = True
        return True
    return False
