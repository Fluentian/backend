#!/usr/bin/env python3
"""
Real content seed script for Fluentian.
Populates Unit 1 (Greetings) and Unit 2 (Numbers & Family) with real French vocabulary and assessments.
"""

import asyncio
import os
import sys

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

async def seed_real_content():
    async with AsyncSessionLocal() as db:
        print("=" * 70)
        print("SEEDING REAL CONTENT FOR FLUENTIAN")
        print("=" * 70)

        # 1. French Language
        result = await db.execute(select(Language).where(Language.iso_code == "fr"))
        french = result.scalar_one_or_none()
        if not french:
            french = Language(iso_code="fr", english_name="French", native_name="Français", is_active=True)
            db.add(french)
            await db.flush()

        # 2. Course
        result = await db.execute(select(Course).where(Course.code == "FR_BEGINNER_A1A2"))
        course = result.scalar_one_or_none()
        if not course:
            course = Course(target_language_id=french.id, code="FR_BEGINNER_A1A2", level_min="A1", level_max="A2", is_published=True)
            db.add(course)
            await db.flush()

        # 3. Units
        unit1 = PathUnit(course_id=course.id, unit_kind=UnitKind.core, unit_no=1, title="Les Salutations (Greetings)")
        unit2 = PathUnit(course_id=course.id, unit_kind=UnitKind.core, unit_no=2, title="La Famille et Les Nombres")
        db.add_all([unit1, unit2])
        await db.flush()

        # --- UNIT 1 LESSONS ---
        l1_1 = Lesson(course_id=course.id, unit_id=unit1.id, lesson_kind=LessonKind.vocabulary, sequence_no=1, title="Basic Greetings", estimated_minutes=5, xp_reward=15, is_published=True)
        l1_2 = Lesson(course_id=course.id, unit_id=unit1.id, lesson_kind=LessonKind.dialogue, sequence_no=2, title="How are you?", estimated_minutes=10, xp_reward=20, is_published=True)
        l1_3 = Lesson(course_id=course.id, unit_id=unit1.id, lesson_kind=LessonKind.speaking, sequence_no=3, title="Introducing Yourself", estimated_minutes=10, xp_reward=25, is_published=True)
        db.add_all([l1_1, l1_2, l1_3])
        await db.flush()

        # U1 L1 Blocks & Questions
        db.add_all([
            LessonBlock(lesson_id=l1_1.id, block_kind="explanation", sequence_no=1, block_payload={"text": "Welcome! Let's learn how to greet people in French. 'Bonjour' is used during the day, and 'Bonsoir' in the evening."}),
            LessonBlock(lesson_id=l1_1.id, block_kind="vocabulary", sequence_no=2, block_payload={"word": "Bonjour", "meaning": "Good morning / Hello"}),
            LessonBlock(lesson_id=l1_1.id, block_kind="vocabulary", sequence_no=3, block_payload={"word": "Bonsoir", "meaning": "Good evening"}),
            LessonBlock(lesson_id=l1_1.id, block_kind="vocabulary", sequence_no=4, block_payload={"word": "Salut", "meaning": "Hi / Bye (informal)"}),
            LessonBlock(lesson_id=l1_1.id, block_kind="vocabulary", sequence_no=5, block_payload={"word": "Au revoir", "meaning": "Goodbye"}),
            
            Question(lesson_id=l1_1.id, question_kind=QuestionKind.mcq_single, sequence_no=1, prompt_payload={"text": "How do you say 'Good morning' in French?", "mcqOptions": ["Bonjour", "Bonsoir", "Salut"]}, grading_payload={"correct_index": 0, "explanation": "Bonjour is used during the day."}),
            Question(lesson_id=l1_1.id, question_kind=QuestionKind.match_pairs, sequence_no=2, prompt_payload={"text": "Match the greetings", "pairs": [{"fr": "Bonjour", "en": "Hello"}, {"fr": "Bonsoir", "en": "Good evening"}, {"fr": "Au revoir", "en": "Goodbye"}]}, grading_payload={"matches": {"Bonjour": "Hello", "Bonsoir": "Good evening", "Au revoir": "Goodbye"}}),
            Question(lesson_id=l1_1.id, question_kind=QuestionKind.dictation, sequence_no=3, prompt_payload={"text": "Listen and type", "audio_url": "", "hint": "It means hello"}, grading_payload={"accepted_answers": ["bonjour", "Bonjour"], "explanation": "Bonjour is standard hello."}),
        ])

        # U1 L2 Blocks & Questions
        db.add_all([
            LessonBlock(lesson_id=l1_2.id, block_kind="explanation", sequence_no=1, block_payload={"text": "To ask how someone is doing, say 'Comment ça va ?' (How is it going?)."}),
            LessonBlock(lesson_id=l1_2.id, block_kind="vocabulary", sequence_no=2, block_payload={"word": "Comment ça va ?", "meaning": "How are you?"}),
            LessonBlock(lesson_id=l1_2.id, block_kind="vocabulary", sequence_no=3, block_payload={"word": "Ça va bien, merci", "meaning": "It's going well, thank you"}),
            LessonBlock(lesson_id=l1_2.id, block_kind="vocabulary", sequence_no=4, block_payload={"word": "Et toi ?", "meaning": "And you?"}),
            
            Question(lesson_id=l1_2.id, question_kind=QuestionKind.fill_blank, sequence_no=1, prompt_payload={"text": "Comment ça ____ ?", "hint": "It means 'goes'"}, grading_payload={"accepted_answers": ["va", "Va"]}),
            Question(lesson_id=l1_2.id, question_kind=QuestionKind.listening_comprehension, sequence_no=2, prompt_payload={"text": "Does this person sound happy or sad?", "audio_url": ""}, grading_payload={"accepted_answers": ["happy", "Happy", "Ça va bien", "bien"], "explanation": "They said 'Ça va très bien!'"}),
        ])

        # U1 L3 Blocks & Questions
        db.add_all([
            LessonBlock(lesson_id=l1_3.id, block_kind="explanation", sequence_no=1, block_payload={"text": "To introduce yourself, say 'Je m'appelle...' (My name is...)."}),
            LessonBlock(lesson_id=l1_3.id, block_kind="vocabulary", sequence_no=2, block_payload={"word": "Je m'appelle...", "meaning": "My name is..."}),
            LessonBlock(lesson_id=l1_3.id, block_kind="vocabulary", sequence_no=3, block_payload={"word": "Je suis d'Éthiopie", "meaning": "I am from Ethiopia"}),
            LessonBlock(lesson_id=l1_3.id, block_kind="vocabulary", sequence_no=4, block_payload={"word": "Enchanté", "meaning": "Nice to meet you"}),
            
            Question(lesson_id=l1_3.id, question_kind=QuestionKind.short_text, sequence_no=1, prompt_payload={"text": "Write 'My name is' in French."}, grading_payload={"accepted_answers": ["je m'appelle", "Je m'appelle"]}),
            Question(lesson_id=l1_3.id, question_kind=QuestionKind.translation, sequence_no=2, prompt_payload={"text": "Translate: 'I am from Ethiopia'"}, grading_payload={"accepted_answers": ["Je suis d'Ethiopie", "je suis d'éthiopie", "Je suis d'Éthiopie"]}),
            Question(lesson_id=l1_3.id, question_kind=QuestionKind.speech_record, sequence_no=3, prompt_payload={"text": "Say 'Enchanté'", "instruction": "Pronounce the nasal 'an' and 'é'."}, grading_payload={"evaluation_criteria": ["Pronunciation", "Fluency"]}),
        ])

        # --- UNIT 2 LESSONS ---
        l2_1 = Lesson(course_id=course.id, unit_id=unit2.id, lesson_kind=LessonKind.vocabulary, sequence_no=1, title="Numbers 1-10", estimated_minutes=5, xp_reward=15, is_published=True)
        l2_2 = Lesson(course_id=course.id, unit_id=unit2.id, lesson_kind=LessonKind.vocabulary, sequence_no=2, title="Family Members", estimated_minutes=10, xp_reward=20, is_published=True)
        l2_3 = Lesson(course_id=course.id, unit_id=unit2.id, lesson_kind=LessonKind.exam_drill, sequence_no=3, title="Unit 1 & 2 Checkpoint", estimated_minutes=15, xp_reward=50, is_published=True)
        db.add_all([l2_1, l2_2, l2_3])
        await db.flush()

        # U2 L1 Blocks & Questions
        db.add_all([
            LessonBlock(lesson_id=l2_1.id, block_kind="explanation", sequence_no=1, block_payload={"text": "Let's count from 1 to 5!"}),
            LessonBlock(lesson_id=l2_1.id, block_kind="vocabulary", sequence_no=2, block_payload={"word": "Un, Deux, Trois", "meaning": "One, Two, Three"}),
            LessonBlock(lesson_id=l2_1.id, block_kind="vocabulary", sequence_no=3, block_payload={"word": "Quatre, Cinq", "meaning": "Four, Five"}),
            
            Question(lesson_id=l2_1.id, question_kind=QuestionKind.mcq_single, sequence_no=1, prompt_payload={"text": "Which is the number Five?", "mcqOptions": ["Deux", "Cinq", "Trois"]}, grading_payload={"correct_index": 1}),
            Question(lesson_id=l2_1.id, question_kind=QuestionKind.reorder, sequence_no=2, prompt_payload={"text": "Order the numbers 1 to 4", "words": ["Deux", "Quatre", "Un", "Trois"]}, grading_payload={"correct_order": ["Un", "Deux", "Trois", "Quatre"]}),
        ])

        # U2 L2 Blocks & Questions
        db.add_all([
            LessonBlock(lesson_id=l2_2.id, block_kind="explanation", sequence_no=1, block_payload={"text": "Family vocabulary. Remember 'le' is masculine and 'la' is feminine."}),
            LessonBlock(lesson_id=l2_2.id, block_kind="vocabulary", sequence_no=2, block_payload={"word": "Le père", "meaning": "The father"}),
            LessonBlock(lesson_id=l2_2.id, block_kind="vocabulary", sequence_no=3, block_payload={"word": "La mère", "meaning": "The mother"}),
            LessonBlock(lesson_id=l2_2.id, block_kind="vocabulary", sequence_no=4, block_payload={"word": "Le frère", "meaning": "The brother"}),
            LessonBlock(lesson_id=l2_2.id, block_kind="vocabulary", sequence_no=5, block_payload={"word": "La sœur", "meaning": "The sister"}),
            
            Question(lesson_id=l2_2.id, question_kind=QuestionKind.match_pairs, sequence_no=1, prompt_payload={"text": "Match the family members", "pairs": [{"fr": "Le frère", "en": "Brother"}, {"fr": "La mère", "en": "Mother"}, {"fr": "La sœur", "en": "Sister"}]}, grading_payload={"matches": {"Le frère": "Brother", "La mère": "Mother", "La sœur": "Sister"}}),
            Question(lesson_id=l2_2.id, question_kind=QuestionKind.fill_blank, sequence_no=2, prompt_payload={"text": "Mon _____ s'appelle Dawit (Brother)", "hint": "brother"}, grading_payload={"accepted_answers": ["frère", "frere"]}),
        ])

        # U2 L3 Blocks & Questions (Checkpoint)
        db.add_all([
            Question(lesson_id=l2_3.id, question_kind=QuestionKind.translation, sequence_no=1, prompt_payload={"text": "Translate: 'Hello, my name is...'"}, grading_payload={"accepted_answers": ["Bonjour, je m'appelle..."]}),
            Question(lesson_id=l2_3.id, question_kind=QuestionKind.mcq_single, sequence_no=2, prompt_payload={"text": "Which word means 'Good evening'?", "mcqOptions": ["Bonjour", "Salut", "Bonsoir"]}, grading_payload={"correct_index": 2}),
            Question(lesson_id=l2_3.id, question_kind=QuestionKind.short_text, sequence_no=3, prompt_payload={"text": "Write the number 3 in French."}, grading_payload={"accepted_answers": ["trois", "Trois"]}),
        ])

        await db.commit()
        print("Successfully seeded real curriculum!")

if __name__ == "__main__":
    asyncio.run(seed_real_content())
