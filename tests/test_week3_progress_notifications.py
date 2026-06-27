"""Week 3 progress/profile/notification trust checks."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Course, Language, Lesson, LessonKind, PathUnit, Question, QuestionKind, UnitKind
from app.models.progress import UserLessonProgress
from app.models.user import AppRole, ProficiencyLevel, User, UserSettings
from app.services import content_service, notification_service, progress_service


def _user(username: str, email: str, role: AppRole = AppRole.student) -> User:
    return User(
        username=username,
        email=email,
        password_hash="not-used",
        role=role,
        email_verified=True,
    )


@pytest.mark.asyncio
async def test_weekly_xp_uses_recent_completed_lessons(db_session: AsyncSession):
    user = _user("weekly", "weekly@example.com")
    language = Language(iso_code="fr", english_name="French", native_name="Francais")
    db_session.add_all([user, language])
    await db_session.flush()

    course = Course(
        target_language_id=language.id,
        code="FR-A0",
        level_min="a0",
        level_max="a1",
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()

    unit = PathUnit(course_id=course.id, unit_kind=UnitKind.core, unit_no=1, title="Start")
    db_session.add(unit)
    await db_session.flush()

    recent_lesson = Lesson(
        course_id=course.id,
        unit_id=unit.id,
        lesson_kind=LessonKind.vocabulary,
        sequence_no=1,
        title="Recent",
        xp_reward=15,
    )
    old_lesson = Lesson(
        course_id=course.id,
        unit_id=unit.id,
        lesson_kind=LessonKind.vocabulary,
        sequence_no=2,
        title="Old",
        xp_reward=30,
    )
    db_session.add_all([recent_lesson, old_lesson])
    await db_session.flush()

    now = datetime.now(UTC)
    db_session.add_all(
        [
            UserLessonProgress(
                user_id=user.id,
                lesson_id=recent_lesson.id,
                mastery_score=1,
                completed=True,
                completed_at=now - timedelta(days=1),
            ),
            UserLessonProgress(
                user_id=user.id,
                lesson_id=old_lesson.id,
                mastery_score=1,
                completed=True,
                completed_at=now - timedelta(days=10),
            ),
        ]
    )
    await db_session.flush()

    user.xp_total = 999
    stats = await progress_service.get_user_stats(db_session, user)

    assert stats["weekly_xp"] == 15
    assert stats["total_xp"] == 999


@pytest.mark.asyncio
async def test_broadcast_notification_respects_active_student_settings(
    db_session: AsyncSession,
):
    active = _user("active", "active@example.com")
    opted_out = _user("optout", "optout@example.com")
    inactive = _user("inactive", "inactive@example.com")
    inactive.is_active = False
    admin = _user("admin", "admin@example.com", AppRole.admin)
    db_session.add_all([active, opted_out, inactive, admin])
    await db_session.flush()
    db_session.add(UserSettings(user_id=opted_out.id, notifications_enabled=False))
    await db_session.commit()

    sent_count = await notification_service.broadcast_notification(
        db_session,
        "Launch update",
        "Stage 1 lessons are ready.",
    )

    active_items, active_total, active_unread = await notification_service.list_notifications(
        db_session, active.id
    )
    opted_out_items, opted_out_total, _ = await notification_service.list_notifications(
        db_session, opted_out.id
    )

    assert sent_count >= 1
    assert active_total == 1
    assert active_unread == 1
    assert active_items[0].title == "Launch update"
    assert opted_out_total == 0
    assert opted_out_items == []


@pytest.mark.asyncio
async def test_lesson_questions_are_filtered_by_user_level(db_session: AsyncSession):
    suffix = uuid4().hex[:6]
    user = _user(f"advanced_{suffix}", f"advanced-{suffix}@example.com")
    user.current_level = ProficiencyLevel.b2
    language = Language(iso_code=f"fr-{suffix}", english_name="French", native_name="Francais")
    db_session.add_all([user, language])
    await db_session.flush()

    course = Course(
        target_language_id=language.id,
        code=f"FR-ADV-{suffix}",
        level_min="a0",
        level_max="b2",
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()

    unit = PathUnit(course_id=course.id, unit_kind=UnitKind.core, unit_no=1, title="Advanced")
    db_session.add(unit)
    await db_session.flush()

    lesson = Lesson(
        course_id=course.id,
        unit_id=unit.id,
        lesson_kind=LessonKind.vocabulary,
        sequence_no=1,
        title="Difficulty mix",
        is_published=True,
    )
    db_session.add(lesson)
    await db_session.flush()

    questions = [
        Question(
            lesson_id=lesson.id,
            question_kind=QuestionKind.mcq_single,
            sequence_no=idx,
            difficulty=difficulty,
            prompt_payload={"question": f"Question {idx}", "options": ["a", "b"]},
            grading_payload={"correct_answer": "a"},
        )
        for idx, difficulty in enumerate([1, 2, 3, 4, 4, 5, 5], start=1)
    ]
    db_session.add_all(questions)
    await db_session.commit()

    selected = await content_service.get_lesson_questions(db_session, lesson.id, user)

    assert len(selected) == 3
    assert {question.difficulty for question in selected}.issubset({4, 5})


@pytest.mark.asyncio
async def test_daily_reminders_respect_notification_opt_out(db_session: AsyncSession):
    active = _user("reminder_active", "reminder-active@example.com")
    opted_out = _user("reminder_optout", "reminder-optout@example.com")
    yesterday = datetime.now(UTC) - timedelta(days=1)
    active.streak_days = 3
    active.last_activity_date = yesterday
    opted_out.streak_days = 4
    opted_out.last_activity_date = yesterday
    db_session.add_all([active, opted_out])
    await db_session.flush()
    db_session.add(UserSettings(user_id=opted_out.id, notifications_enabled=False))
    await db_session.commit()

    sent_count = await notification_service.generate_daily_reminders(db_session)

    active_items, active_total, _ = await notification_service.list_notifications(
        db_session, active.id
    )
    opted_out_items, opted_out_total, _ = await notification_service.list_notifications(
        db_session, opted_out.id
    )

    assert sent_count >= 1
    assert active_total == 1
    assert "streak" in active_items[0].body
    assert opted_out_total == 0
    assert opted_out_items == []
