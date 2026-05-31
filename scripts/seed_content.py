#!/usr/bin/env python3
"""
Seed script for creating courses, units, lessons, and questions.

This script populates the database with sample content for learning.
Run from the backend directory with: python scripts/seed_content.py
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
    LessonKind,
    PathUnit,
    Question,
    QuestionKind,
    UnitKind,
)


async def seed_content():
    """Seed courses, units, lessons, and questions."""
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("SEEDING CONTENT: Courses, Units, Lessons, and Questions")
        print("=" * 70)

        # 1. Ensure French language exists
        print("\n--- Setting up Language ---")
        result = await db.execute(select(Language).where(Language.iso_code == "fr"))
        french = result.scalar_one_or_none()

        if not french:
            print("Creating French language...")
            french = Language(
                iso_code="fr",
                english_name="French",
                native_name="Français",
                is_active=True,
            )
            db.add(french)
            await db.flush()
        else:
            print(f"French language already exists (id: {french.id})")

        # 2. Create Beginner Course (A1-A2)
        print("\n--- Creating Beginner Course (A1-A2) ---")
        result = await db.execute(
            select(Course).where(Course.code == "FR_BEGINNER_A1A2")
        )
        beginner_course = result.scalar_one_or_none()

        if not beginner_course:
            print("Creating Beginner Course...")
            beginner_course = Course(
                target_language_id=french.id,
                code="FR_BEGINNER_A1A2",
                level_min="A1",
                level_max="A2",
                is_published=True,
            )
            db.add(beginner_course)
            await db.flush()
        else:
            print(f"Beginner Course already exists (id: {beginner_course.id})")

        # 3. Create Intermediate Course (B1-B2)
        print("\n--- Creating Intermediate Course (B1-B2) ---")
        result = await db.execute(
            select(Course).where(Course.code == "FR_INTERMEDIATE_B1B2")
        )
        intermediate_course = result.scalar_one_or_none()

        if not intermediate_course:
            print("Creating Intermediate Course...")
            intermediate_course = Course(
                target_language_id=french.id,
                code="FR_INTERMEDIATE_B1B2",
                level_min="B1",
                level_max="B2",
                is_published=True,
            )
            db.add(intermediate_course)
            await db.flush()
        else:
            print(f"Intermediate Course already exists (id: {intermediate_course.id})")

        # 4. Create units for Beginner Course
        print("\n--- Creating Units for Beginner Course ---")
        beginner_units = [
            ("Introduction & Greetings", UnitKind.core, 1),
            ("Basic Vocabulary & Phrases", UnitKind.core, 2),
            ("Present Tense Basics", UnitKind.core, 3),
            ("Daily Conversations", UnitKind.practice, 4),
            ("Unit 1 Checkpoint", UnitKind.checkpoint, 5),
        ]

        created_units = {}
        for unit_title, unit_kind, unit_no in beginner_units:
            result = await db.execute(
                select(PathUnit).where(
                    (PathUnit.course_id == beginner_course.id)
                    & (PathUnit.unit_no == unit_no)
                )
            )
            unit = result.scalar_one_or_none()

            if not unit:
                print(f"Creating Unit {unit_no}: {unit_title}")
                unit = PathUnit(
                    course_id=beginner_course.id,
                    unit_kind=unit_kind,
                    unit_no=unit_no,
                    title=unit_title,
                )
                db.add(unit)
                await db.flush()
            else:
                print(f"Unit {unit_no} already exists")

            created_units[unit_no] = unit

        # 5. Create comprehensive lessons for Unit 1 - ALL LESSON KINDS
        print("\n--- Creating Lessons for Unit 1 (All Lesson Kinds) ---")
        unit1 = created_units[1]
        unit1_lessons = [
            ("Bonjour! - Basic Greetings", LessonKind.dialogue, 1, 8, 15),
            ("Hello, My Name Is...", LessonKind.vocabulary, 2, 10, 20),
            ("How Are You? - Responses", LessonKind.grammar_explainer, 3, 12, 25),
            ("Pronunciation Guide", LessonKind.pronunciation, 4, 15, 30),
            ("Listening: Introduction", LessonKind.listening, 5, 10, 20),
            ("Reading: Meeting People", LessonKind.reading, 6, 12, 25),
            ("Writing: Hello Email", LessonKind.writing, 7, 15, 30),
            ("Speaking Practice", LessonKind.speaking, 8, 20, 40),
            ("Cultural Bridge: French Customs", LessonKind.cultural_bridge, 9, 15, 30),
            ("Practice Conversation", LessonKind.roleplay_simulation, 10, 20, 40),
            ("Exam Drill: Greetings", LessonKind.exam_drill, 11, 15, 35),
        ]

        for lesson_title, lesson_kind, seq_no, est_minutes, xp_reward in unit1_lessons:
            result = await db.execute(
                select(Lesson).where(
                    (Lesson.unit_id == unit1.id) & (Lesson.sequence_no == seq_no)
                )
            )
            lesson = result.scalar_one_or_none()

            if not lesson:
                print(f"Creating Lesson {seq_no}: {lesson_title}")
                lesson = Lesson(
                    course_id=beginner_course.id,
                    unit_id=unit1.id,
                    lesson_kind=lesson_kind,
                    sequence_no=seq_no,
                    title=lesson_title,
                    estimated_minutes=est_minutes,
                    xp_reward=xp_reward,
                    is_published=True,
                )
                db.add(lesson)
                await db.flush()

                # Create diverse questions for this lesson - ALL QUESTION KINDS
                print(f"  Creating questions for: {lesson_title}")
                questions_data = [
                    (
                        1,
                        QuestionKind.mcq_single,
                        {
                            "text": "What is the correct greeting in the morning?",
                            "options": [
                                "Bonsoir",
                                "Bonjour",
                                "Bonne nuit",
                                "Au revoir",
                            ],
                        },
                        {
                            "correct_index": 1,
                            "explanation": "Bonjour is used as a greeting during day.",
                        },
                    ),
                    (
                        2,
                        QuestionKind.mcq_multi,
                        {
                            "text": "Which of these are valid greetings? (Select all)",
                            "options": ["Bonjour", "Salut", "Bonsoir", "Merci"],
                        },
                        {
                            "correct_indices": [0, 1, 2],
                            "explanation": "Bonjour, Salut, and Bonsoir are all greetings.",
                        },
                    ),
                    (
                        3,
                        QuestionKind.fill_blank,
                        {
                            "text": "Je m'appelle ____.",
                            "hint": "Name placeholder",
                        },
                        {"accepted_answers": ["Marie", "Jean", "Sophie", "Pierre"]},
                    ),
                    (
                        4,
                        QuestionKind.reorder,
                        {
                            "text": "Arrange in correct order: you nice Hello are to",
                            "words": ["Hello", "nice", "to", "you", "are"],
                            "correct_order": ["Hello", "you", "are", "nice", "to"],
                        },
                        {
                            "correct_order": ["Hello", "you", "are", "nice", "to"],
                            "explanation": "Correct sentence order.",
                        },
                    ),
                    (
                        5,
                        QuestionKind.match_pairs,
                        {
                            "text": "Match French to English",
                            "pairs": [
                                {"fr": "Bonjour", "en": "Hello"},
                                {"fr": "Merci", "en": "Thanks"},
                                {"fr": "Au revoir", "en": "Goodbye"},
                            ],
                        },
                        {
                            "matches": {
                                "Bonjour": "Hello",
                                "Merci": "Thanks",
                                "Au revoir": "Goodbye",
                            }
                        },
                    ),
                    (
                        6,
                        QuestionKind.short_text,
                        {"text": "Write a short greeting in French (2-3 words)"},
                        {
                            "accepted_answers": [
                                "Bonjour, ça va?",
                                "Salut mon ami",
                                "Hello, how are you",
                            ]
                        },
                    ),
                    (
                        7,
                        QuestionKind.translation,
                        {"text": 'Translate: "How are you?" to French'},
                        {
                            "accepted_answers": [
                                "Comment allez-vous?",
                                "Comment ça va?",
                                "Ça va?",
                            ]
                        },
                    ),
                    (
                        8,
                        QuestionKind.listening_comprehension,
                        {
                            "text": "Listen to the audio and answer: What is the greeting?",
                            "audio_url": "/media/greeting_audio.mp3",
                        },
                        {
                            "accepted_answers": ["Bonjour", "Good morning"],
                            "explanation": "The speaker says 'Bonjour'",
                        },
                    ),
                    (
                        9,
                        QuestionKind.dictation,
                        {
                            "text": "Listen and type what you hear",
                            "audio_url": "/media/dictation_bonjour.mp3",
                            "hint": "French greeting",
                        },
                        {
                            "accepted_answers": ["Bonjour"],
                            "explanation": "Bonjour is a common French greeting.",
                        },
                    ),
                    (
                        10,
                        QuestionKind.speech_record,
                        {
                            "text": "Record yourself saying: Bonjour, je m'appelle...",
                            "instruction": "Speak clearly and naturally",
                        },
                        {
                            "evaluation_criteria": [
                                "Pronunciation clarity",
                                "Accent accuracy",
                                "Fluency",
                            ]
                        },
                    ),
                ]

                for q_seq, q_kind, prompt_payload, grading_payload in questions_data:
                    result = await db.execute(
                        select(Question).where(
                            (Question.lesson_id == lesson.id)
                            & (Question.sequence_no == q_seq)
                        )
                    )
                    question = result.scalar_one_or_none()

                    if not question:
                        question = Question(
                            lesson_id=lesson.id,
                            question_kind=q_kind,
                            sequence_no=q_seq,
                            prompt_payload=prompt_payload,
                            grading_payload=grading_payload,
                        )
                        db.add(question)
            else:
                print(f"Lesson {seq_no} already exists")

        # 6. Create lessons for Unit 2
        print("\n--- Creating Lessons for Unit 2 (Basic Vocabulary & Phrases) ---")
        unit2 = created_units[2]
        unit2_lessons = [
            ("Numbers 1-10", LessonKind.vocabulary, 1, 10, 20),
            ("Colors Around Us", LessonKind.vocabulary, 2, 10, 20),
            ("Days of the Week", LessonKind.grammar_explainer, 3, 8, 15),
            ("Time Expressions", LessonKind.vocabulary, 4, 12, 25),
            ("Reading: Numbers Story", LessonKind.reading, 5, 10, 20),
            ("Listening: Color Quiz", LessonKind.listening, 6, 12, 25),
            ("Speaking: Introduce Colors", LessonKind.speaking, 7, 15, 30),
        ]

        for lesson_title, lesson_kind, seq_no, est_minutes, xp_reward in unit2_lessons:
            result = await db.execute(
                select(Lesson).where(
                    (Lesson.unit_id == unit2.id) & (Lesson.sequence_no == seq_no)
                )
            )
            lesson = result.scalar_one_or_none()

            if not lesson:
                print(f"Creating Lesson {seq_no}: {lesson_title}")
                lesson = Lesson(
                    course_id=beginner_course.id,
                    unit_id=unit2.id,
                    lesson_kind=lesson_kind,
                    sequence_no=seq_no,
                    title=lesson_title,
                    estimated_minutes=est_minutes,
                    xp_reward=xp_reward,
                    is_published=True,
                )
                db.add(lesson)
                await db.flush()

                # Create questions
                print(f"  Creating questions for: {lesson_title}")
                questions_data = [
                    (
                        1,
                        QuestionKind.mcq_single,
                        {
                            "text": "What is 5 in French?",
                            "options": ["trois", "cinq", "sept", "neuf"],
                        },
                        {"correct_index": 1, "explanation": "Cinq means five."},
                    ),
                    (
                        2,
                        QuestionKind.mcq_multi,
                        {
                            "text": "Which are numbers? (Select all)",
                            "options": ["un", "rouge", "deux", "bleu", "trois"],
                        },
                        {
                            "correct_indices": [0, 2, 4],
                            "explanation": "un, deux, trois are numbers.",
                        },
                    ),
                    (
                        3,
                        QuestionKind.fill_blank,
                        {
                            "text": "Lundi est le premier jour de la ____.",
                            "hint": "The word for week",
                        },
                        {"accepted_answers": ["semaine"]},
                    ),
                    (
                        4,
                        QuestionKind.match_pairs,
                        {
                            "text": "Match numbers to French",
                            "pairs": [
                                {"num": "1", "fr": "un"},
                                {"num": "2", "fr": "deux"},
                                {"num": "3", "fr": "trois"},
                            ],
                        },
                        {"matches": {"1": "un", "2": "deux", "3": "trois"}},
                    ),
                    (
                        5,
                        QuestionKind.reorder,
                        {
                            "text": "Order: red blue green",
                            "words": ["red", "blue", "green"],
                            "correct_order": ["red", "blue", "green"],
                        },
                        {
                            "correct_order": ["red", "blue", "green"],
                            "explanation": "Rainbow order",
                        },
                    ),
                    (
                        6,
                        QuestionKind.translation,
                        {"text": "Translate: 'Monday' to French"},
                        {"accepted_answers": ["Lundi"]},
                    ),
                    (
                        7,
                        QuestionKind.short_text,
                        {"text": "Name 3 colors in French"},
                        {
                            "accepted_answers": [
                                "rouge, bleu, vert",
                                "red, blue, green",
                            ]
                        },
                    ),
                    (
                        8,
                        QuestionKind.listening_comprehension,
                        {
                            "text": "What number do you hear?",
                            "audio_url": "/media/number_audio.mp3",
                        },
                        {"accepted_answers": ["cinq", "5"]},
                    ),
                    (
                        9,
                        QuestionKind.dictation,
                        {
                            "text": "Type what you hear",
                            "audio_url": "/media/dictation_lundi.mp3",
                        },
                        {"accepted_answers": ["Lundi"]},
                    ),
                    (
                        10,
                        QuestionKind.speech_record,
                        {
                            "text": "Say the French numbers 1-5",
                            "instruction": "Speak clearly",
                        },
                        {"evaluation_criteria": ["Accuracy", "Pronunciation"]},
                    ),
                ]

                for q_seq, q_kind, prompt_payload, grading_payload in questions_data:
                    result = await db.execute(
                        select(Question).where(
                            (Question.lesson_id == lesson.id)
                            & (Question.sequence_no == q_seq)
                        )
                    )
                    question = result.scalar_one_or_none()

                    if not question:
                        question = Question(
                            lesson_id=lesson.id,
                            question_kind=q_kind,
                            sequence_no=q_seq,
                            prompt_payload=prompt_payload,
                            grading_payload=grading_payload,
                        )
                        db.add(question)
            else:
                print(f"Lesson {seq_no} already exists")

        # 7. Create units for Intermediate Course
        print("\n--- Creating Units for Intermediate Course ---")
        intermediate_units = [
            ("Advanced Grammar", UnitKind.core, 1),
            ("Professional French", UnitKind.core, 2),
            ("Cultural Immersion", UnitKind.story, 3),
            ("Advanced Practice", UnitKind.practice, 4),
        ]

        for unit_title, unit_kind, unit_no in intermediate_units:
            result = await db.execute(
                select(PathUnit).where(
                    (PathUnit.course_id == intermediate_course.id)
                    & (PathUnit.unit_no == unit_no)
                )
            )
            unit = result.scalar_one_or_none()

            if not unit:
                print(f"Creating Unit {unit_no}: {unit_title}")
                unit = PathUnit(
                    course_id=intermediate_course.id,
                    unit_kind=unit_kind,
                    unit_no=unit_no,
                    title=unit_title,
                )
                db.add(unit)
                await db.flush()
            else:
                print(f"Unit {unit_no} already exists")

        # Commit all changes
        await db.commit()

        print("\n" + "=" * 70)
        print("✓ Content seeding completed successfully!")
        print("=" * 70)
        print("\nSummary:")
        print("  • Language: French")
        print("  • Courses: 2 (Beginner A1-A2, Intermediate B1-B2)")
        print(f"  • Units: {len(beginner_units) + len(intermediate_units)}")
        print("\n  Lesson Kinds Included (11 types):")
        print("    - dialogue, vocabulary, grammar_explainer, pronunciation")
        print("    - listening, reading, writing, speaking")
        print("    - cultural_bridge, roleplay_simulation, exam_drill")
        print("\n  Question Types Included (10 types):")
        print("    - mcq_single, mcq_multi, fill_blank, reorder, match_pairs")
        print("    - short_text, translation, listening_comprehension")
        print("    - dictation, speech_record")
        print("\n  • Each lesson includes 3-10 diverse questions")
        print("  • Each question type has 3+ examples")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(seed_content())
