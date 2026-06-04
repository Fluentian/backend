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
    LessonBlock,
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

                # Add lesson blocks based on lesson kind
                print(f"  Creating blocks for: {lesson_title}")
                if lesson_kind == LessonKind.dialogue:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "In this lesson, you'll learn basic French greetings used in everyday conversations. Pay attention to the formal vs informal use."
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Bonjour",
                                "meaning": "Hello / Good day",
                                "audio_url": "https://example.com/audio/bonjour.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            3,
                            {
                                "word": "Bonsoir",
                                "meaning": "Good evening",
                                "audio_url": "https://example.com/audio/bonsoir.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            4,
                            {
                                "word": "Bonne nuit",
                                "meaning": "Good night",
                                "audio_url": "https://example.com/audio/bonnenuit.mp3",
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.vocabulary:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Learn essential vocabulary for introducing yourself in French."
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Je m'appelle",
                                "meaning": "My name is",
                                "audio_url": "https://example.com/audio/jemappelle.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            3,
                            {
                                "word": "Enchanté(e)",
                                "meaning": "Nice to meet you",
                                "audio_url": "https://example.com/audio/enchante.mp3",
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.grammar_explainer:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Understanding responses to 'How are you?' in French. Common polite responses include 'Ça va bien, merci' and 'Très bien, et toi?'"
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Ça va?",
                                "meaning": "How are you? (informal)",
                                "audio_url": "https://example.com/audio/cavat.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            3,
                            {
                                "word": "Ça va bien",
                                "meaning": "I'm doing well",
                                "audio_url": "https://example.com/audio/cavabien.mp3",
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.pronunciation:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Master French pronunciation with these key greetings. French pronunciation emphasizes clear syllables and silent letters."
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Bonjour [bon-zhoor]",
                                "meaning": "The j is pronounced like 'zh' in 'measure'",
                                "audio_url": "https://example.com/audio/bonjour_slow.mp3",
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.listening:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "In this listening exercise, you'll hear introductions in French. Try to identify greetings and names."
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.reading:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Read this short dialogue between two French speakers meeting for the first time."
                            },
                        ),
                        (
                            "explanation",
                            2,
                            {
                                "text": "Marie: Bonjour! Je m'appelle Marie.\nJean: Enchanté! Moi, je m'appelle Jean. Ça va?"
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.writing:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Practice writing a simple greeting email in French using the vocabulary you've learned."
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.speaking:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Record yourself speaking these French greetings. Focus on clear pronunciation and natural rhythm."
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.cultural_bridge:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "In France, greetings are important for politeness. Use 'Bonjour' when entering shops and 'Bonsoir' after 6 PM. Always greet before asking questions!"
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.roleplay_simulation:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "You'll now practice a realistic conversation. Pretend you're meeting a French person at a café."
                            },
                        ),
                    ]
                elif lesson_kind == LessonKind.exam_drill:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "This exam-style section tests all aspects of greetings: listening, reading, writing, and speaking."
                            },
                        ),
                    ]
                else:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {"text": f"Lesson content for {lesson_title}"},
                        )
                    ]

                for block_kind, block_seq, block_payload in blocks:
                    result = await db.execute(
                        select(LessonBlock).where(
                            (LessonBlock.lesson_id == lesson.id)
                            & (LessonBlock.sequence_no == block_seq)
                        )
                    )
                    existing_block = result.scalar_one_or_none()
                    if not existing_block:
                        block = LessonBlock(
                            lesson_id=lesson.id,
                            block_kind=block_kind,
                            sequence_no=block_seq,
                            block_payload=block_payload,
                        )
                        db.add(block)

                # Create diverse questions for this lesson - ALL QUESTION KINDS
                print(f"  Creating questions for: {lesson_title}")
                questions_data = [
                    (
                        1,
                        QuestionKind.mcq_single,
                        {
                            "text": "What is the correct greeting in the morning?",
                            "mcqOptions": [
                                "Bonsoir",
                                "Bonjour",
                                "Bonne nuit",
                                "Au revoir",
                            ],
                            "mcqCorrectAnswer": "Bonjour",
                        },
                        {
                            "correct_index": 1,
                            "explanation": "Bonjour is used as a greeting during the day.",
                        },
                    ),
                    (
                        2,
                        QuestionKind.mcq_multi,
                        {
                            "text": "Which of these are valid greetings? (Select all)",
                            "mcqOptions": ["Bonjour", "Salut", "Bonsoir", "Merci"],
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
                            "hint": "Any French name works as an example",
                        },
                        {
                            "accepted_answers": [
                                "Marie",
                                "Jean",
                                "Sophie",
                                "Pierre",
                                "André",
                                "Claire",
                            ]
                        },
                    ),
                    (
                        4,
                        QuestionKind.reorder,
                        {
                            "text": "Arrange in correct order",
                            "words": ["Hello", "are", "you", "how"],
                            "hint": "Standard English greeting order",
                        },
                        {
                            "correct_order": ["Hello", "how", "are", "you"],
                            "explanation": "The correct order forms 'Hello, how are you?'",
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
                                "Enchanté!",
                                "Bonjour!",
                            ]
                        },
                    ),
                    (
                        7,
                        QuestionKind.translation,
                        {"text": "Translate to French: 'How are you?'"},
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
                            "text": "Listen and select what greeting you hear",
                            "audio_url": "https://example.com/audio/greeting_1.mp3",
                        },
                        {
                            "accepted_answers": ["Bonjour", "bonjour"],
                            "explanation": "The speaker says 'Bonjour'",
                        },
                    ),
                    (
                        9,
                        QuestionKind.dictation,
                        {
                            "text": "Listen and type what you hear",
                            "audio_url": "https://example.com/audio/dictation_1.mp3",
                            "hint": "A common French greeting",
                        },
                        {
                            "accepted_answers": ["Bonjour", "bonjour"],
                            "explanation": "You should write 'Bonjour'",
                        },
                    ),
                    (
                        10,
                        QuestionKind.speech_record,
                        {
                            "text": "Record yourself saying: 'Bonjour, je m'appelle [your name]'",
                            "instruction": "Speak clearly and at natural pace",
                        },
                        {
                            "evaluation_criteria": [
                                "Pronunciation clarity",
                                "Accent accuracy",
                                "Fluency and confidence",
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

                # Add lesson blocks based on lesson kind
                print(f"  Creating blocks for: {lesson_title}")
                if "Numbers" in lesson_title:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Master French numbers 1-10. These are essential for telling time, prices, and quantities."
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Un",
                                "meaning": "One",
                                "audio_url": "https://example.com/audio/un.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            3,
                            {
                                "word": "Deux",
                                "meaning": "Two",
                                "audio_url": "https://example.com/audio/deux.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            4,
                            {
                                "word": "Trois",
                                "meaning": "Three",
                                "audio_url": "https://example.com/audio/trois.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            5,
                            {
                                "word": "Dix",
                                "meaning": "Ten",
                                "audio_url": "https://example.com/audio/dix.mp3",
                            },
                        ),
                    ]
                elif "Colors" in lesson_title:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Learn French color vocabulary. Colors are essential adjectives in French."
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Rouge",
                                "meaning": "Red",
                                "audio_url": "https://example.com/audio/rouge.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            3,
                            {
                                "word": "Bleu",
                                "meaning": "Blue",
                                "audio_url": "https://example.com/audio/bleu.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            4,
                            {
                                "word": "Vert",
                                "meaning": "Green",
                                "audio_url": "https://example.com/audio/vert.mp3",
                            },
                        ),
                    ]
                elif "Days" in lesson_title:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Days of the week are fundamental for scheduling and time expressions in French."
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Lundi",
                                "meaning": "Monday",
                                "audio_url": "https://example.com/audio/lundi.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            3,
                            {
                                "word": "Jeudi",
                                "meaning": "Thursday",
                                "audio_url": "https://example.com/audio/jeudi.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            4,
                            {
                                "word": "Samedi",
                                "meaning": "Saturday",
                                "audio_url": "https://example.com/audio/samedi.mp3",
                            },
                        ),
                    ]
                elif "Time" in lesson_title:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Time expressions in French. Learn how to tell time and discuss schedules."
                            },
                        ),
                        (
                            "vocabulary",
                            2,
                            {
                                "word": "Heure",
                                "meaning": "Hour/Time",
                                "audio_url": "https://example.com/audio/heure.mp3",
                            },
                        ),
                        (
                            "vocabulary",
                            3,
                            {
                                "word": "Minute",
                                "meaning": "Minute",
                                "audio_url": "https://example.com/audio/minute.mp3",
                            },
                        ),
                    ]
                elif "Reading" in lesson_title:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Read this story about numbers in French context."
                            },
                        ),
                        (
                            "explanation",
                            2,
                            {
                                "text": "Il y a un chat noir et trois souris. Les souris sont petites."
                            },
                        ),
                    ]
                elif "Listening" in lesson_title:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Listen to color descriptions and try to identify which color is mentioned."
                            },
                        ),
                    ]
                elif "Speaking" in lesson_title:
                    blocks = [
                        (
                            "explanation",
                            1,
                            {
                                "text": "Practice speaking: describe colors you see around you in French."
                            },
                        ),
                    ]
                else:
                    blocks = [
                        ("explanation", 1, {"text": f"Content for {lesson_title}"})
                    ]

                for block_kind, block_seq, block_payload in blocks:
                    result = await db.execute(
                        select(LessonBlock).where(
                            (LessonBlock.lesson_id == lesson.id)
                            & (LessonBlock.sequence_no == block_seq)
                        )
                    )
                    existing_block = result.scalar_one_or_none()
                    if not existing_block:
                        block = LessonBlock(
                            lesson_id=lesson.id,
                            block_kind=block_kind,
                            sequence_no=block_seq,
                            block_payload=block_payload,
                        )
                        db.add(block)

                # Create questions
                print(f"  Creating questions for: {lesson_title}")
                questions_data = [
                    (
                        1,
                        QuestionKind.mcq_single,
                        {
                            "text": "What is 5 in French?",
                            "mcqOptions": ["trois", "cinq", "sept", "neuf"],
                            "mcqCorrectAnswer": "cinq",
                        },
                        {"correct_index": 1, "explanation": "Cinq means five."},
                    ),
                    (
                        2,
                        QuestionKind.mcq_multi,
                        {
                            "text": "Which are numbers? (Select all)",
                            "mcqOptions": ["un", "rouge", "deux", "bleu", "trois"],
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
                                {"num": "5", "fr": "cinq"},
                            ],
                        },
                        {
                            "matches": {
                                "1": "un",
                                "2": "deux",
                                "3": "trois",
                                "5": "cinq",
                            }
                        },
                    ),
                    (
                        5,
                        QuestionKind.reorder,
                        {
                            "text": "Arrange days in order",
                            "words": ["Jeudi", "Lundi", "Mercredi"],
                            "hint": "Week order",
                        },
                        {
                            "correct_order": ["Lundi", "Mercredi", "Jeudi"],
                            "explanation": "Days in chronological order",
                        },
                    ),
                    (
                        6,
                        QuestionKind.translation,
                        {"text": "Translate to French: 'Monday'"},
                        {"accepted_answers": ["Lundi", "lundi"]},
                    ),
                    (
                        7,
                        QuestionKind.short_text,
                        {"text": "Name 3 colors in French"},
                        {
                            "accepted_answers": [
                                "rouge, bleu, vert",
                                "red, blue, green",
                                "Rouge, bleu, vert",
                            ]
                        },
                    ),
                    (
                        8,
                        QuestionKind.listening_comprehension,
                        {
                            "text": "What number do you hear?",
                            "audio_url": "https://example.com/audio/number_5.mp3",
                        },
                        {"accepted_answers": ["cinq", "5", "Cinq"]},
                    ),
                    (
                        9,
                        QuestionKind.dictation,
                        {
                            "text": "Listen and type what you hear",
                            "audio_url": "https://example.com/audio/lundi_dictation.mp3",
                        },
                        {"accepted_answers": ["Lundi", "lundi"]},
                    ),
                    (
                        10,
                        QuestionKind.speech_record,
                        {
                            "text": "Say the numbers 1-5 in French",
                            "instruction": "Speak clearly and slowly",
                        },
                        {
                            "evaluation_criteria": [
                                "Number accuracy",
                                "Pronunciation clarity",
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
        print("  • Language: French (Français)")
        print("  • Courses: 2 (Beginner A1-A2, Intermediate B1-B2)")
        print(f"  • Units: {len(beginner_units) + len(intermediate_units)}")
        print("\n  Lesson Kinds (11 types) with Content Blocks:")
        print("    ✓ dialogue, vocabulary, grammar_explainer, pronunciation")
        print("    ✓ listening, reading, writing, speaking")
        print("    ✓ cultural_bridge, roleplay_simulation, exam_drill")
        print("\n  Content Blocks Created:")
        print("    • explanation: Lesson context and instructions")
        print("    • vocabulary: Key words with audio pronunciation")
        print("    • 18 lessons in Beginner Units 1-2 (Unit 1: 11, Unit 2: 7)")
        print("\n  Question Types (10 types) per Lesson:")
        print("    ✓ mcq_single: Single choice with options")
        print("    ✓ mcq_multi: Multiple choice (select all)")
        print("    ✓ fill_blank: Fill in missing words with hints")
        print("    ✓ reorder: Arrange words in correct sequence")
        print("    ✓ match_pairs: Match French to English")
        print("    ✓ short_text: Free text response")
        print("    ✓ translation: Translate sentences")
        print("    ✓ listening_comprehension: Audio-based questions")
        print("    ✓ dictation: Type what you hear")
        print("    ✓ speech_record: Record and evaluate speech")
        print("\n  Total Content Items:")
        print("    • 18 Lessons with full blocks")
        print("    • 180+ Questions (10 types per lesson)")
        print("    • 40+ Content blocks (explanation, vocabulary, etc)")
        print("\n  Frontend Integration Ready:")
        print("    • Blocks serve lesson content (blocks in lesson_detail_screen)")
        print("    • Questions have proper MCQ fields (mcqOptions, mcqCorrectAnswer)")
        print("    • Audio URLs included for pronunciation/listening")
        print("    • Grading payloads configured for auto-evaluation")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(seed_content())