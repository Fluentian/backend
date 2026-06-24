"""Content service — courses, units, lessons, blocks, questions."""

import logging
import random
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.content import (
    Course,
    CultureStory,
    Lesson,
    LessonBlock,
    PathUnit,
    Question,
)
from app.models.user import User
from app.utils.content_payloads import (
    normalize_block,
    normalize_block_model,
    normalize_question,
    normalize_question_model,
)

logger = logging.getLogger(__name__)


def _select_dynamic_questions(questions: list, user: User | None) -> list:
    """Dynamically select and shuffle questions based on user experience (XP).
    Each user gets a uniquely shuffled sequence of questions.
    """
    if not questions or not user:
        return questions

    # Filter by difficulty based on user level
    level_difficulty_map = {
        "a0": [1],
        "a1": [1, 2],
        "a2": [2, 3],
        "b1": [3, 4],
        "b2": [4, 5],
        "c1": [5],
        "c2": [5]
    }
    allowed_difficulties = level_difficulty_map.get(user.current_level.value, [1, 2, 3, 4, 5])
    
    filtered_questions = [q for q in questions if getattr(q, 'difficulty', 1) in allowed_difficulties]
    if len(filtered_questions) < 3:
        filtered_questions = questions

    # Seed based on user id, their XP milestone, and the specific questions
    # This ensures the shuffle is unique to the user and the specific lesson
    questions_hash = sum(getattr(q, 'sequence_no', 0) for q in filtered_questions)
    seed_val = f"{user.id}_{user.xp_total // 50}_{questions_hash}"
    rnd = random.Random(seed_val)
    
    total = len(filtered_questions)
    if total <= 3:
        shuffled = list(filtered_questions)
        rnd.shuffle(shuffled)
        return shuffled
        
    # Select a subset of questions (e.g., 80%) to provide variety
    num_to_select = max(3, int(total * 0.8))
    
    selected = rnd.sample(filtered_questions, num_to_select)
    # We DO NOT sort by sequence_no here because the goal is to show 
    # a different sequence of questions to different users.
    rnd.shuffle(selected)
    
    return selected


def _jsonable(value: object) -> object:
    """Convert Pydantic models and nested containers into JSON-compatible data."""
    if hasattr(value, "model_dump"):
        return value.model_dump()  # type: ignore[attr-defined]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


async def get_course(db: AsyncSession, course_id: UUID, user: User | None = None) -> Course:
    """Get a single course by ID."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course is None:
        raise NotFoundError("Course not found")
    return course


async def get_course_units(db: AsyncSession, course_id: UUID, user: User | None = None) -> list[PathUnit]:
    """Get all units for a course."""
    result = await db.execute(
        select(PathUnit).where(PathUnit.course_id == course_id).order_by(PathUnit.unit_no)
    )
    return list(result.scalars().all())


async def create_lesson(db: AsyncSession, unit_id: UUID, **kwargs: object) -> Lesson:
    """Create a new lesson."""
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


async def get_lesson(db: AsyncSession, lesson_id: UUID, user: User | None = None) -> Lesson:
    """Get a lesson with its blocks and questions."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise NotFoundError("Lesson not found")
    
    # Materialize relationships
    blocks_list = list(lesson.blocks)
    questions_list = list(lesson.questions)

    for block in blocks_list:
        normalize_block_model(block)
        
    for question in questions_list:
        normalize_question_model(question)

    # Only apply dynamic selection to questions
    dynamic_questions = _select_dynamic_questions(questions_list, user)
    
    lesson.blocks = blocks_list  # type: ignore[assignment]
    lesson.questions = dynamic_questions  # type: ignore[assignment]
    
    return lesson


async def update_lesson(db: AsyncSession, lesson_id: UUID, **kwargs: object) -> Lesson:
    """Update a lesson's metadata."""
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    
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
    data = dict(kwargs)
    kind, payload = normalize_block(
        str(data.get("block_kind", "rich_text")),
        data.get("block_payload") or {},
    )
    data["block_kind"] = kind
    data["block_payload"] = payload
    block = LessonBlock(lesson_id=lesson_id, **data)  # type: ignore[arg-type]
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def create_question(db: AsyncSession, lesson_id: UUID, **kwargs: object) -> Question:
    """Add a question to a lesson."""
    data = dict(kwargs)
    qkind = str(data.get("question_kind", "mcq_single"))
    prompt, grading = normalize_question(
        qkind,
        data.get("prompt_payload") or {},
        data.get("grading_payload") or {},
    )
    data["prompt_payload"] = prompt
    data["grading_payload"] = grading
    question = Question(lesson_id=lesson_id, **data)  # type: ignore[arg-type]
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


async def update_block(db: AsyncSession, block_id: UUID, **kwargs: object) -> LessonBlock:
    """Update a content block."""
    result = await db.execute(select(LessonBlock).where(LessonBlock.id == block_id))
    block = result.scalar_one_or_none()
    
    if block is None:
        raise NotFoundError("Block not found")

    for key, value in kwargs.items():
        if hasattr(block, key):
            setattr(block, key, value)

    if "block_kind" in kwargs or "block_payload" in kwargs:
        kind, payload = normalize_block(block.block_kind, block.block_payload)
        block.block_kind = kind
        block.block_payload = payload

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


async def get_lesson_questions(db: AsyncSession, lesson_id: UUID, user: User | None = None) -> list[Question]:
    """Get all questions for a lesson."""
    result = await db.execute(
        select(Question).where(Question.lesson_id == lesson_id).order_by(Question.sequence_no)
    )
    questions = list(result.scalars().all())
    for question in questions:
        normalize_question_model(question)
        
    return _select_dynamic_questions(questions, user)


async def update_question(db: AsyncSession, question_id: UUID, **kwargs: object) -> Question:
    """Update a question."""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    
    if question is None:
        raise NotFoundError("Question not found")

    for key, value in kwargs.items():
        if hasattr(question, key):
            setattr(question, key, value)

    qkind = (
        question.question_kind.value
        if hasattr(question.question_kind, "value")
        else str(question.question_kind)
    )
    prompt, grading = normalize_question(
        qkind, question.prompt_payload, question.grading_payload
    )
    question.prompt_payload = prompt
    question.grading_payload = grading

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


async def get_due_srs_questions(db: AsyncSession, user: User) -> list[Question]:
    """Get questions that are due for spaced repetition review for the user."""
    from app.models.progress import SpacedRepetitionItem
    from datetime import datetime, UTC
    
    now = datetime.now(UTC)
    result = await db.execute(
        select(Question)
        .join(SpacedRepetitionItem, SpacedRepetitionItem.question_id == Question.id)
        .where(
            SpacedRepetitionItem.user_id == user.id,
            SpacedRepetitionItem.next_review_date <= now
        )
        .order_by(SpacedRepetitionItem.next_review_date.asc())
        .limit(20) # cap review lesson at 20 questions
    )
    questions = list(result.scalars().all())
    for question in questions:
        normalize_question_model(question)
        
    # We DO NOT apply dynamic subset selection here because the user
    # specifically needs to review exactly these due questions.
    return questions


# Culture stories


async def list_culture_stories(
    db: AsyncSession,
    include_unpublished: bool = False,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[CultureStory], int]:
    """List culture exploration stories."""
    query = select(CultureStory)
    count_query = select(func.count()).select_from(CultureStory)

    if not include_unpublished:
        query = query.where(CultureStory.is_published.is_(True))
        count_query = count_query.where(CultureStory.is_published.is_(True))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(CultureStory.sequence_no, CultureStory.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def get_culture_story(
    db: AsyncSession,
    story_id: UUID,
    include_unpublished: bool = False,
) -> CultureStory:
    """Get one culture story."""
    query = select(CultureStory).where(CultureStory.id == story_id)
    if not include_unpublished:
        query = query.where(CultureStory.is_published.is_(True))
    result = await db.execute(query)
    story = result.scalar_one_or_none()
    if story is None:
        raise NotFoundError("Culture story not found")
    return story


async def create_culture_story(db: AsyncSession, **kwargs: object) -> CultureStory:
    """Create a culture story."""
    data = dict(kwargs)
    data["media"] = _jsonable(data.get("media") or [])
    data["paragraphs"] = _jsonable(data.get("paragraphs") or [])
    story = CultureStory(**data)  # type: ignore[arg-type]
    db.add(story)
    await db.commit()
    await db.refresh(story)
    return story


async def update_culture_story(
    db: AsyncSession,
    story_id: UUID,
    **kwargs: object,
) -> CultureStory:
    """Update a culture story."""
    result = await db.execute(select(CultureStory).where(CultureStory.id == story_id))
    story = result.scalar_one_or_none()
    if story is None:
        raise NotFoundError("Culture story not found")

    for key, value in kwargs.items():
        if value is None or not hasattr(story, key):
            continue
        if key in {"media", "paragraphs"}:
            value = _jsonable(value)
        setattr(story, key, value)

    await db.commit()
    await db.refresh(story)
    return story


async def delete_culture_story(db: AsyncSession, story_id: UUID) -> None:
    """Delete a culture story."""
    result = await db.execute(select(CultureStory).where(CultureStory.id == story_id))
    story = result.scalar_one_or_none()
    if story:
        await db.delete(story)
        await db.commit()
