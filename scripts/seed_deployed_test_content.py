#!/usr/bin/env python3
"""Seed three real French A1 units for deployed app testing.

Run from the backend directory after setting DATABASE_URL to the deployed
Postgres URL:

    python scripts/seed_deployed_test_content.py

The script replaces only the FR_BEGINNER_A1_REAL course. It leaves users,
roles, progress, and other courses untouched.
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import func, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.models.content import Lesson, PathUnit, Question  # noqa: E402
from scripts.seed_real_content import COURSE_CODE, seed_real_content  # noqa: E402


async def main() -> None:
    if "localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL:
        print("Refusing to run against a local DATABASE_URL.")
        print("Set DATABASE_URL to the deployed database URL, then run again.")
        raise SystemExit(1)

    async with AsyncSessionLocal() as db:
        course = await seed_real_content(db)
        await db.commit()

        unit_count = (
            await db.execute(
                select(func.count()).select_from(PathUnit).where(PathUnit.course_id == course.id)
            )
        ).scalar_one()
        lesson_count = (
            await db.execute(
                select(func.count()).select_from(Lesson).where(Lesson.course_id == course.id)
            )
        ).scalar_one()
        question_count = (
            await db.execute(
                select(func.count())
                .select_from(Question)
                .join(Lesson)
                .where(Lesson.course_id == course.id)
            )
        ).scalar_one()

    print(f"Seeded {COURSE_CODE}")
    print(f"Course ID: {course.id}")
    print(f"Units: {unit_count}")
    print(f"Lessons: {lesson_count}")
    print(f"Questions: {question_count}")
    print("Question types covered: mcq_single, mcq_multi, fill_blank, reorder,")
    print("match_pairs, short_text, translation, speech_record,")
    print("listening_comprehension, dictation")


if __name__ == "__main__":
    asyncio.run(main())
