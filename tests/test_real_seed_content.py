from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Course, Lesson, LessonBlock, PathUnit, Question
from scripts.seed_real_content import COURSE_CODE, seed_real_content


async def test_real_content_seed_is_display_ready(db_session: AsyncSession):
    course = await seed_real_content(db_session)

    saved_course = (
        await db_session.execute(select(Course).where(Course.id == course.id))
    ).scalar_one()
    assert saved_course.code == COURSE_CODE
    assert saved_course.is_published is True
    assert saved_course.level_min == "A1"

    unit_count = (
        await db_session.execute(
            select(func.count()).select_from(PathUnit).where(PathUnit.course_id == course.id)
        )
    ).scalar_one()
    lesson_count = (
        await db_session.execute(
            select(func.count()).select_from(Lesson).where(Lesson.course_id == course.id)
        )
    ).scalar_one()
    block_count = (
        await db_session.execute(
            select(func.count())
            .select_from(LessonBlock)
            .join(Lesson)
            .where(Lesson.course_id == course.id)
        )
    ).scalar_one()
    question_count = (
        await db_session.execute(
            select(func.count())
            .select_from(Question)
            .join(Lesson)
            .where(Lesson.course_id == course.id)
        )
    ).scalar_one()

    assert unit_count == 3
    assert lesson_count == 9
    assert block_count >= 45
    assert question_count >= 27

    questions = list(
        (
            await db_session.execute(select(Question).join(Lesson).where(Lesson.course_id == course.id))
        )
        .scalars()
        .all()
    )
    kinds = {q.question_kind.value for q in questions}
    assert {
        "mcq_single",
        "mcq_multi",
        "fill_blank",
        "reorder",
        "match_pairs",
        "short_text",
        "translation",
        "dictation",
        "listening_comprehension",
        "speech_record",
    }.issubset(kinds)

    for question in questions:
        prompt = question.prompt_payload
        grading = question.grading_payload
        assert prompt.get("question") or prompt.get("text")

        if question.question_kind.value in {"mcq_single", "mcq_multi", "listening_comprehension"}:
            assert prompt.get("options") or prompt.get("mcqOptions")

        if question.question_kind.value == "match_pairs":
            pairs = prompt.get("pairs")
            assert pairs
            assert all("left" in pair and "right" in pair for pair in pairs)

        if question.question_kind.value in {"fill_blank", "short_text", "translation", "dictation"}:
            assert grading.get("correct_answer")
            assert grading.get("accepted_answers")

        if question.question_kind.value == "reorder":
            assert grading.get("correct_order")
            assert grading.get("correct_answer")

