#!/usr/bin/env python3
"""
Clear script for removing seeded content (lessons, questions, blocks).

This script removes sample content that was added by seed_content.py.
It keeps the course structure (Language, Course, PathUnit) intact.
Run from the backend directory with: python scripts/clear_seed_content.py
"""

import asyncio
import os
import sys

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.content import (
    Course,
    Language,
    Lesson,
    LessonBlock,
    PathUnit,
    Question,
)


async def clear_seed_content():
    """Remove seeded lessons, blocks, and questions."""
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("CLEARING SEEDED CONTENT: Removing Lessons, Blocks, and Questions")
        print("=" * 70)

        # 1. Find French language and Beginner course
        print("\n--- Locating Content to Remove ---")
        result = await db.execute(select(Language).where(Language.iso_code == "fr"))
        french = result.scalar_one_or_none()

        if not french:
            print("French language not found. Nothing to clear.")
            return

        print(f"French language found (id: {french.id})")

        result = await db.execute(
            select(Course).where(Course.code == "FR_BEGINNER_A1A2")
        )
        beginner_course = result.scalar_one_or_none()

        if not beginner_course:
            print("Beginner course not found. Nothing to clear.")
            return

        print(f"Beginner course found (id: {beginner_course.id})")

        # 2. Find Units 1 and 2 in the Beginner course
        print("\n--- Finding Units to Clear ---")
        result = await db.execute(
            select(PathUnit).where(
                (PathUnit.course_id == beginner_course.id)
                & (PathUnit.unit_no.in_([1, 2]))
            )
        )
        units = result.scalars().all()
        print(f"Found {len(units)} units to clear: Unit 1 and Unit 2")

        unit_ids = [unit.id for unit in units]

        # 3. Find and delete Questions in lessons of these units
        print("\n--- Removing Questions ---")
        result = await db.execute(
            select(Question).where(
                Question.lesson_id.in_(
                    select(Lesson.id).where(Lesson.unit_id.in_(unit_ids))
                )
            )
        )
        questions = result.scalars().all()
        question_count = len(questions)

        if question_count > 0:
            for question in questions:
                await db.delete(question)
            print(f"Deleted {question_count} questions")
        else:
            print("No questions found to delete")

        # 4. Find and delete LessonBlocks in lessons of these units
        print("\n--- Removing Lesson Blocks ---")
        result = await db.execute(
            select(LessonBlock).where(
                LessonBlock.lesson_id.in_(
                    select(Lesson.id).where(Lesson.unit_id.in_(unit_ids))
                )
            )
        )
        blocks = result.scalars().all()
        block_count = len(blocks)

        if block_count > 0:
            for block in blocks:
                await db.delete(block)
            print(f"Deleted {block_count} lesson blocks")
        else:
            print("No lesson blocks found to delete")

        # 5. Find and delete Lessons in these units
        print("\n--- Removing Lessons ---")
        result = await db.execute(select(Lesson).where(Lesson.unit_id.in_(unit_ids)))
        lessons = result.scalars().all()
        lesson_count = len(lessons)

        if lesson_count > 0:
            for lesson in lessons:
                await db.delete(lesson)
            print(f"Deleted {lesson_count} lessons")
        else:
            print("No lessons found to delete")

        # 6. Commit changes
        await db.commit()

        print("\n" + "=" * 70)
        print("✓ Content clearing completed successfully!")
        print("=" * 70)
        print("\nSummary of Removed Items:")
        print(f"  • Questions removed: {question_count}")
        print(f"  • Lesson blocks removed: {block_count}")
        print(f"  • Lessons removed: {lesson_count}")
        print("\nRemaining Structure (Not Deleted):")
        print("  • Language: French ✓")
        print("  • Courses: FR_BEGINNER_A1A2, FR_INTERMEDIATE_B1B2 ✓")
        print("  • Units: All structure preserved ✓")
        print("\nYou can now run 'python scripts/seed_content.py' for a fresh seed.")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(clear_seed_content())
