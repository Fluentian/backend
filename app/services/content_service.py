"""Content service — courses, units, lessons, blocks, questions."""

import logging
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.content import (
    Course,
    Lesson,
    LessonBlock,
    PathUnit,
    Question,
)

logger = logging.getLogger(__name__)


# ── Courses ─────────────────────────────────────────────


async def list_courses(
    db: AsyncSession,
    level: str | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Course], int]:
    """List published courses with optional level filter."""
    query = (
        select(Course)
        .where(Course.is_published.is_(True))
        .order_by(case((Course.code.like("E2E_%"), 1), else_=0), Course.created_at.desc())
    )
    count_query = select(func.count()).select_from(Course).where(Course.is_published.is_(True))

    if level:
        query = query.where(Course.level_min <= level, Course.level_max >= level)
        count_query = count_query.where(Course.level_min <= level, Course.level_max >= level)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    courses = list(result.scalars().all())

    return courses, total


async def get_course(db: AsyncSession, course_id: UUID) -> Course:
    """Get a single course by ID."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found")
    return course


async def create_course(db: AsyncSession, **kwargs: object) -> Course:
    """Create a new course."""
    course = Course(**kwargs)  # type: ignore[arg-type]
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def update_course(db: AsyncSession, course_id: UUID, **kwargs: object) -> Course:
    """Update a course's metadata."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found")

    for key, value in kwargs.items():
        if hasattr(course, key):
            setattr(course, key, value)

    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course_id: UUID) -> None:
    """Delete a course."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course:
        await db.delete(course)
        await db.commit()


# ── Units ───────────────────────────────────────────────


async def get_course_units(db: AsyncSession, course_id: UUID) -> list[PathUnit]:
    """Get all units for a course."""
    result = await db.execute(
        select(PathUnit).where(PathUnit.course_id == course_id).order_by(PathUnit.unit_no)
    )
    return list(result.scalars().all())


async def create_unit(db: AsyncSession, course_id: UUID, **kwargs: object) -> PathUnit:
    """Create a unit within a course."""
    unit = PathUnit(course_id=course_id, **kwargs)  # type: ignore[arg-type]
    db.add(unit)
    await db.commit()
    await db.refresh(unit)
    return unit


# ── Lessons ─────────────────────────────────────────────


async def list_lessons(
    db: AsyncSession,
    course_id: UUID | None = None,
    unit_id: UUID | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Lesson], int]:
    """List lessons with optional filters."""
    query = select(Lesson)
    count_query = select(func.count()).select_from(Lesson)

    if course_id:
        query = query.where(Lesson.course_id == course_id)
        count_query = count_query.where(Lesson.course_id == course_id)
    if unit_id:
        query = query.where(Lesson.unit_id == unit_id)
        count_query = count_query.where(Lesson.unit_id == unit_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(offset).limit(limit).order_by(Lesson.created_at.desc())
    result = await db.execute(query)
    lessons = list(result.scalars().all())

    return lessons, total


async def get_lesson(db: AsyncSession, lesson_id: UUID) -> Lesson:
    """Get a lesson with its blocks and questions."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise NotFoundError("Lesson not found")
    return lesson


async def get_lesson_questions(db: AsyncSession, lesson_id: UUID) -> list[Question]:
    """Get all questions for a lesson."""
    result = await db.execute(
        select(Question).where(Question.lesson_id == lesson_id).order_by(Question.sequence_no)
    )
    return list(result.scalars().all())


async def create_lesson(db: AsyncSession, unit_id: UUID, **kwargs: object) -> Lesson:
    """Create a lesson within a unit."""
    # Get the unit to find course_id
    result = await db.execute(select(PathUnit).where(PathUnit.id == unit_id))
    unit = result.scalar_one_or_none()
    if unit is None:
        raise NotFoundError("Unit not found")

    lesson = Lesson(unit_id=unit_id, course_id=unit.course_id, **kwargs)  # type: ignore[arg-type]
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def update_lesson(db: AsyncSession, lesson_id: UUID, **kwargs: object) -> Lesson:
    """Update a lesson's metadata."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    from app.core.exceptions import NotFoundError

    if lesson is None:
        raise NotFoundError("Lesson not found")

    for key, value in kwargs.items():
        if hasattr(lesson, key):
            setattr(lesson, key, value)

    await db.commit()
    await db.refresh(lesson)
    return lesson


async def delete_lesson(db: AsyncSession, lesson_id: UUID) -> None:
    """Delete a lesson."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if lesson:
        await db.delete(lesson)
        await db.commit()


async def create_block(db: AsyncSession, lesson_id: UUID, **kwargs: object) -> LessonBlock:
    """Add a content block to a lesson."""
    block = LessonBlock(lesson_id=lesson_id, **kwargs)  # type: ignore[arg-type]
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def create_question(db: AsyncSession, lesson_id: UUID, **kwargs: object) -> Question:
    """Add a question to a lesson."""
    question = Question(lesson_id=lesson_id, **kwargs)  # type: ignore[arg-type]
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


async def update_block(db: AsyncSession, block_id: UUID, **kwargs: object) -> LessonBlock:
    """Update a content block."""
    result = await db.execute(select(LessonBlock).where(LessonBlock.id == block_id))
    block = result.scalar_one_or_none()
    from app.core.exceptions import NotFoundError

    if block is None:
        raise NotFoundError("Block not found")

    for key, value in kwargs.items():
        if hasattr(block, key):
            setattr(block, key, value)

    await db.commit()
    await db.refresh(block)
    return block


async def delete_block(db: AsyncSession, block_id: UUID) -> None:
    """Delete a content block."""
    result = await db.execute(select(LessonBlock).where(LessonBlock.id == block_id))
    block = result.scalar_one_or_none()
    if block:
        await db.delete(block)
        await db.commit()


async def update_question(db: AsyncSession, question_id: UUID, **kwargs: object) -> Question:
    """Update a question."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    from app.core.exceptions import NotFoundError

    if question is None:
        raise NotFoundError("Question not found")

    for key, value in kwargs.items():
        if hasattr(question, key):
            setattr(question, key, value)

    await db.commit()
    await db.refresh(question)
    return question


async def delete_question(db: AsyncSession, question_id: UUID) -> None:
    """Delete a question."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if question:
        await db.delete(question)
        await db.commit()
