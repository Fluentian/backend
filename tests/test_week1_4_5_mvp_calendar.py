"""Calendar MVP checks for enrollment, settings, feedback, and placement."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Course, Language, Lesson, LessonKind, PathUnit, UnitKind
from app.models.user import User
from app.services import learning_service, progress_service, user_service


def _user(username: str = "learner") -> User:
    return User(
        username=username,
        email=f"{username}@example.com",
        password_hash="not-used",
        email_verified=True,
    )


async def _published_course(db_session: AsyncSession) -> tuple[Course, PathUnit, Lesson]:
    suffix = uuid4().hex[:8]
    language = Language(
        iso_code=f"fr-{suffix}", english_name="French", native_name="Francais"
    )
    db_session.add(language)
    await db_session.flush()

    course = Course(
        target_language_id=language.id,
        code=f"FR-STAGE-1-{suffix}",
        level_min="a0",
        level_max="a1",
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()

    unit = PathUnit(course_id=course.id, unit_kind=UnitKind.core, unit_no=1, title="Start")
    db_session.add(unit)
    await db_session.flush()

    lesson = Lesson(
        course_id=course.id,
        unit_id=unit.id,
        lesson_kind=LessonKind.vocabulary,
        sequence_no=1,
        title="Bonjour",
        is_published=True,
    )
    db_session.add(lesson)
    await db_session.flush()
    return course, unit, lesson


@pytest.mark.asyncio
async def test_enrollment_is_idempotent_and_listed(db_session: AsyncSession):
    user = _user()
    db_session.add(user)
    course, _, _ = await _published_course(db_session)

    first = await progress_service.enroll_in_course(db_session, user.id, course.id)
    second = await progress_service.enroll_in_course(db_session, user.id, course.id)
    enrollments = await progress_service.get_user_enrollments(db_session, user.id)

    assert second.id == first.id
    assert len(enrollments) == 1
    assert enrollments[0].course_id == course.id
    assert enrollments[0].is_active is True


@pytest.mark.asyncio
async def test_settings_update_creates_missing_settings_row(db_session: AsyncSession):
    user = _user("settings")
    db_session.add(user)
    await db_session.flush()

    settings = await user_service.update_settings(
        db_session,
        user.id,
        notifications_enabled=False,
        autoplay_audio=False,
    )

    assert settings.user_id == user.id
    assert settings.notifications_enabled is False
    assert settings.autoplay_audio is False


@pytest.mark.asyncio
async def test_feedback_and_placement_update_expected_records(db_session: AsyncSession):
    user = _user("calendar")
    db_session.add(user)
    _, _, lesson = await _published_course(db_session)

    feedback = await learning_service.create_lesson_feedback(
        db_session,
        user,
        lesson.id,
        rating=4,
        category="content",
        comment="Clear, but needs more examples.",
    )
    attempt = await learning_service.submit_placement(
        db_session,
        user,
        answers=[True, True, False, True],
        detail={"source": "mvp"},
    )

    assert feedback.lesson_id == lesson.id
    assert feedback.rating == 4
    assert attempt.score == 3
    assert attempt.total_questions == 4
    assert attempt.assigned_level == "a1"
    assert user.current_level.value == "a1"
