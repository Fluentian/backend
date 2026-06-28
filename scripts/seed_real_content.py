#!/usr/bin/env python3
"""Seed a real, display-ready French A1 curriculum for Fluentian."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.content import (  # noqa: E402
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

COURSE_CODE = "FR_BEGINNER_A1_REAL"


def rich(content: str) -> dict[str, Any]:
    return {"kind": "rich_text", "payload": {"content": content, "text": content}}


def vocab(word: str, meaning: str) -> dict[str, Any]:
    return {
        "kind": "vocabulary",
        "payload": {
            "word": word,
            "meaning": meaning,
            "tts_enabled": True,
            "tts_language": "fr-FR",
            "tts_text": word,
        },
    } 


def sentence(target: str, base: str) -> dict[str, Any]:
    return {
        "kind": "sentence_pair",
        "payload": {
            "target": target,
            "base": base,
            "tts_enabled": True,
            "tts_language": "fr-FR",
            "tts_text": target,
        },
    }


def grammar(rule: str, example: str) -> dict[str, Any]:
    return {"kind": "grammar_note", "payload": {"rule": rule, "example": example}}


def mcq(question: str, options: list[str], correct: str) -> dict[str, Any]:
    return {
        "kind": QuestionKind.mcq_single,
        "prompt": {"question": question, "text": question, "options": options, "mcqOptions": options},
        "grading": {"correct_answer": correct, "accepted_answers": [correct]},
    }


def mcq_multi(question: str, options: list[str], correct: list[str]) -> dict[str, Any]:
    return {
        "kind": QuestionKind.mcq_multi,
        "prompt": {"question": question, "text": question, "options": options, "mcqOptions": options},
        "grading": {"correct_answers": correct},
    }


def fill_blank(question: str, correct: str, accepted: list[str]) -> dict[str, Any]:
    return {
        "kind": QuestionKind.fill_blank,
        "prompt": {"question": question, "text": question},
        "grading": {"correct_answer": correct, "accepted_answers": accepted},
    }


def short_text(question: str, correct: str, accepted: list[str]) -> dict[str, Any]:
    return {
        "kind": QuestionKind.short_text,
        "prompt": {"question": question, "text": question},
        "grading": {"correct_answer": correct, "accepted_answers": accepted},
    }


def translation(question: str, correct: str, accepted: list[str]) -> dict[str, Any]:
    words = correct.replace(".", "").replace(",", "").split()
    return {
        "kind": QuestionKind.translation,
        "prompt": {"question": question, "text": question, "word_bank": words, "options": words},
        "grading": {"correct_answer": correct, "accepted_answers": accepted},
    }


def dictation(question: str, phrase: str, accepted: list[str]) -> dict[str, Any]:
    return {
        "kind": QuestionKind.dictation,
        "prompt": {
            "question": question,
            "text": question,
            "tts_enabled": True,
            "tts_language": "fr-FR",
            "tts_text": phrase,
            "dictation_text": phrase,
        },
        "grading": {"correct_answer": phrase, "accepted_answers": accepted},
    }


def listening(question: str, options: list[str], correct: str, phrase: str) -> dict[str, Any]:
    return {
        "kind": QuestionKind.listening_comprehension,
        "prompt": {
            "question": question,
            "text": question,
            "options": options,
            "mcqOptions": options,
            "tts_enabled": True,
            "tts_language": "fr-FR",
            "tts_text": phrase,
            "listening_text": phrase,
        },
        "grading": {"correct_answer": correct, "accepted_answers": [correct]},
    }


def reorder(question: str, correct_order: list[str]) -> dict[str, Any]:
    correct = " ".join(correct_order)
    return {
        "kind": QuestionKind.reorder,
        "prompt": {"question": question, "text": question, "word_bank": correct_order, "options": correct_order},
        "grading": {"correct_order": correct_order, "correct_answer": correct},
    }


def match(question: str, pairs: list[tuple[str, str]]) -> dict[str, Any]:
    pair_dicts = [{"left": left, "right": right} for left, right in pairs]
    return {
        "kind": QuestionKind.match_pairs,
        "prompt": {"question": question, "text": question, "pairs": pair_dicts},
        "grading": {"matches": {left: right for left, right in pairs}},
    }


def speech(question: str, phrase: str) -> dict[str, Any]:
    return {
        "kind": QuestionKind.speech_record,
        "prompt": {
            "question": question,
            "text": phrase,
            "tts_enabled": True,
            "tts_language": "fr-FR",
            "tts_text": phrase,
        },
        "grading": {"correct_answer": phrase, "min_score": 80},
    }


CURRICULUM: list[dict[str, Any]] = [
    {
        "unit_no": 1,
        "title": "Survival Greetings",
        "lessons": [
            {
                "kind": LessonKind.vocabulary,
                "title": "Hello, Goodbye, and Polite Words",
                "minutes": 7,
                "xp": 20,
                "blocks": [
                    rich("French greetings change with the moment and the relationship. Use Bonjour during the day, Bonsoir in the evening, and Salut with friends."),
                    vocab("Bonjour", "Hello / Good morning"),
                    vocab("Bonsoir", "Good evening"),
                    vocab("Salut", "Hi / Bye"),
                    vocab("Au revoir", "Goodbye"),
                    vocab("Merci", "Thank you"),
                    sentence("Bonjour, madame.", "Hello, ma'am."),
                    grammar("Use Bonjour with strangers, teachers, and shop staff. Salut is informal.", "Bonjour, monsieur. / Salut, Lina."),
                ],
                "questions": [
                    mcq("How do you say 'good evening' in French?", ["Bonjour", "Bonsoir", "Merci"], "Bonsoir"),
                    match("Match each greeting to its meaning.", [("Bonjour", "Hello"), ("Au revoir", "Goodbye"), ("Merci", "Thank you")]),
                    dictation("Listen and type the word for hello.", "Bonjour", ["bonjour"]),
                ],
            },
            {
                "kind": LessonKind.dialogue,
                "title": "Asking How Someone Is",
                "minutes": 8,
                "xp": 25,
                "blocks": [
                    rich("The common friendly question Comment ca va ? means How is it going? The simplest answer is Ca va bien, merci."),
                    vocab("Comment ca va ?", "How are you? / How is it going?"),
                    vocab("Ca va bien", "I am well"),
                    vocab("Pas mal", "Not bad"),
                    vocab("Et toi ?", "And you?"),
                    sentence("Salut, comment ca va ?", "Hi, how are you?"),
                    sentence("Ca va bien, merci. Et toi ?", "I am well, thank you. And you?"),
                ],
                "questions": [
                    fill_blank("Comment ca ____ ?", "va", ["va"]),
                    mcq("What is the best answer to Comment ca va ?", ["Au revoir", "Ca va bien, merci", "Je m'appelle"], "Ca va bien, merci"),
                    reorder("Put the reply in order.", ["Ca", "va", "bien", "merci"]),
                ],
            },
            {
                "kind": LessonKind.speaking,
                "title": "Introduce Yourself",
                "minutes": 10,
                "xp": 30,
                "blocks": [
                    rich("To introduce yourself, say Je m'appelle plus your name. To say where you are from, use Je viens de plus the place."),
                    vocab("Je m'appelle...", "My name is..."),
                    vocab("Je viens de Nairobi.", "I come from Nairobi."),
                    vocab("Enchante", "Nice to meet you"),
                    grammar("Je means I. The verb m'appelle is used only when giving your name.", "Je m'appelle Amina."),
                    sentence("Bonjour, je m'appelle Amina.", "Hello, my name is Amina."),
                ],
                "questions": [
                    short_text("Write 'My name is' in French.", "Je m'appelle", ["je m'appelle", "je m appelle"]),
                    translation("Translate: I come from Nairobi.", "Je viens de Nairobi", ["Je viens de Nairobi.", "je viens de nairobi"]),
                    speech("Say: Enchante", "Enchante"),
                ],
            },
        ],
    },
    {
        "unit_no": 2,
        "title": "People, Numbers, and Family",
        "lessons": [
            {
                "kind": LessonKind.vocabulary,
                "title": "Numbers 1 to 10",
                "minutes": 8,
                "xp": 20,
                "blocks": [
                    rich("French numbers from one to ten are essential for phone numbers, prices, ages, and classroom instructions."),
                    vocab("un", "one"),
                    vocab("deux", "two"),
                    vocab("trois", "three"),
                    vocab("quatre", "four"),
                    vocab("cinq", "five"),
                    vocab("six", "six"),
                    vocab("sept", "seven"),
                    vocab("huit", "eight"),
                    vocab("neuf", "nine"),
                    vocab("dix", "ten"),
                ],
                "questions": [
                    mcq("Which word means five?", ["deux", "cinq", "huit"], "cinq"),
                    reorder("Order the numbers from one to four.", ["un", "deux", "trois", "quatre"]),
                    fill_blank("Deux plus un font ____.", "trois", ["trois", "3"]),
                ],
            },
            {
                "kind": LessonKind.vocabulary,
                "title": "Family Members",
                "minutes": 9,
                "xp": 25,
                "blocks": [
                    rich("Family nouns often use le for masculine words and la for feminine words."),
                    vocab("le pere", "the father"),
                    vocab("la mere", "the mother"),
                    vocab("le frere", "the brother"),
                    vocab("la soeur", "the sister"),
                    vocab("les parents", "the parents"),
                    sentence("Ma mere s'appelle Grace.", "My mother is called Grace."),
                    sentence("J'ai deux freres.", "I have two brothers."),
                ],
                "questions": [
                    match("Match the family words.", [("le pere", "father"), ("la mere", "mother"), ("la soeur", "sister")]),
                    fill_blank("Mon ____ s'appelle David. (brother)", "frere", ["frere"]),
                    mcq_multi("Which two words are family members?", ["merci", "la mere", "le frere", "bonjour"], ["la mere", "le frere"]),
                ],
            },
            {
                "kind": LessonKind.grammar_explainer,
                "title": "My, Your, and Simple Sentences",
                "minutes": 10,
                "xp": 30,
                "blocks": [
                    rich("Possessive words change with the noun. Use mon before masculine nouns and ma before feminine nouns."),
                    grammar("Use mon with le words and ma with la words.", "mon pere / ma mere"),
                    sentence("Mon pere est professeur.", "My father is a teacher."),
                    sentence("Ma soeur a dix ans.", "My sister is ten years old."),
                ],
                "questions": [
                    mcq("Choose the correct phrase for 'my mother'.", ["mon mere", "ma mere", "mes mere"], "ma mere"),
                    translation("Translate: My sister is ten years old.", "Ma soeur a dix ans", ["Ma soeur a dix ans.", "ma soeur a dix ans"]),
                    fill_blank("____ pere est professeur.", "Mon", ["mon", "Mon"]),
                ],
            },
        ],
    },
    {
        "unit_no": 3,
        "title": "Daily Life and Places",
        "lessons": [
            {
                "kind": LessonKind.dialogue,
                "title": "Ordering at a Cafe",
                "minutes": 11,
                "xp": 30,
                "blocks": [
                    rich("In cafes, Je voudrais is a polite way to say I would like."),
                    vocab("Je voudrais", "I would like"),
                    vocab("un cafe", "a coffee"),
                    vocab("un the", "a tea"),
                    vocab("l'addition", "the bill"),
                    sentence("Je voudrais un cafe, s'il vous plait.", "I would like a coffee, please."),
                    sentence("L'addition, s'il vous plait.", "The bill, please."),
                ],
                "questions": [
                    mcq("What does Je voudrais mean?", ["I have", "I would like", "I am"], "I would like"),
                    reorder("Build: I would like a tea.", ["Je", "voudrais", "un", "the"]),
                    dictation("Listen and type: please.", "s'il vous plait", ["s'il vous plait", "sil vous plait"]),
                ],
            },
            {
                "kind": LessonKind.listening,
                "title": "Where Is It?",
                "minutes": 10,
                "xp": 30,
                "blocks": [
                    rich("Use ou est to ask where something is. Common place words help you navigate a city."),
                    vocab("Ou est... ?", "Where is...?"),
                    vocab("la gare", "the train station"),
                    vocab("la banque", "the bank"),
                    vocab("l'ecole", "the school"),
                    vocab("a gauche", "on the left"),
                    vocab("a droite", "on the right"),
                    sentence("Ou est la gare ?", "Where is the train station?"),
                ],
                "questions": [
                    listening("Listen: Ou est la gare ?", ["Where is the train station?", "Where is the school?", "Where is the bank?"], "Where is the train station?", "Ou est la gare ?"),
                    match("Match the places.", [("la gare", "train station"), ("la banque", "bank"), ("l'ecole", "school")]),
                    fill_blank("La banque est a ____.", "droite", ["droite"]),
                ],
            },
            {
                "kind": LessonKind.exam_drill,
                "title": "A1 Checkpoint: First Conversations",
                "minutes": 15,
                "xp": 50,
                "blocks": [
                    rich("This checkpoint reviews greetings, introductions, family, numbers, cafe language, and directions."),
                ],
                "questions": [
                    mcq("Which sentence introduces your name?", ["Je m'appelle Sara.", "Je voudrais un cafe.", "Ou est la gare ?"], "Je m'appelle Sara."),
                    translation("Translate: Good evening, my name is Sara.", "Bonsoir, je m'appelle Sara", ["Bonsoir, je m'appelle Sara.", "bonsoir je m'appelle sara"]),
                    match("Match each phrase.", [("Merci", "Thank you"), ("la gare", "train station"), ("Je voudrais", "I would like")]),
                    fill_blank("J'ai ____ freres. (two)", "deux", ["deux", "2"]),
                    reorder("Build: Where is the bank?", ["Ou", "est", "la", "banque"]),
                ],
            },
        ],
    },
]


async def seed_real_content(db: AsyncSession | None = None) -> Course:
    owns_session = db is None
    session = db or AsyncSessionLocal()
    try:
        result = await session.execute(select(Language).where(Language.iso_code == "fr"))
        french = result.scalar_one_or_none()
        if french is None:
            french = Language(
                iso_code="fr",
                english_name="French",
                native_name="Francais",
                is_active=True,
            )
            session.add(french)
            await session.flush()

        existing = await session.execute(select(Course).where(Course.code == COURSE_CODE))
        old_course = existing.scalar_one_or_none()
        if old_course is not None:
            await session.delete(old_course)
            await session.flush()

        course = Course(
            target_language_id=french.id,
            code=COURSE_CODE,
            level_min="A1",
            level_max="A1",
            is_published=True,
        )
        session.add(course)
        await session.flush()

        for unit_data in CURRICULUM:
            unit = PathUnit(
                course_id=course.id,
                unit_kind=UnitKind.core,
                unit_no=unit_data["unit_no"],
                title=unit_data["title"],
            )
            session.add(unit)
            await session.flush()

            for lesson_index, lesson_data in enumerate(unit_data["lessons"], start=1):
                lesson = Lesson(
                    course_id=course.id,
                    unit_id=unit.id,
                    lesson_kind=lesson_data["kind"],
                    sequence_no=lesson_index,
                    title=lesson_data["title"],
                    estimated_minutes=lesson_data["minutes"],
                    xp_reward=lesson_data["xp"],
                    is_published=True,
                )
                session.add(lesson)
                await session.flush()

                for block_index, block_data in enumerate(lesson_data["blocks"], start=1):
                    session.add(
                        LessonBlock(
                            lesson_id=lesson.id,
                            block_kind=block_data["kind"],
                            sequence_no=block_index,
                            block_payload=block_data["payload"],
                        )
                    )

                for question_index, question_data in enumerate(lesson_data["questions"], start=1):
                    session.add(
                        Question(
                            lesson_id=lesson.id,
                            question_kind=question_data["kind"],
                            sequence_no=question_index,
                            prompt_payload=question_data["prompt"],
                            grading_payload=question_data["grading"],
                        )
                    )

        if owns_session:
            await session.commit()
            await session.refresh(course)
        else:
            await session.flush()
        return course
    finally:
        if owns_session:
            await session.close()


async def main() -> None:
    course = await seed_real_content()
    print(f"Seeded {COURSE_CODE} ({course.id}) with {len(CURRICULUM)} units.")


if __name__ == "__main__":
    asyncio.run(main())
