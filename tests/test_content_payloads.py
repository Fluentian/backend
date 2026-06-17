"""Tests for cross-client content payload normalization."""

from app.utils.content_payloads import (
    grade_answer,
    normalize_block,
    normalize_question,
)


def test_normalize_seed_style_mcq():
    prompt, grading = normalize_question(
        "mcq_single",
        {
            "text": "What is hello?",
            "mcqOptions": ["Bonsoir", "Bonjour"],
            "mcqCorrectAnswer": "Bonjour",
        },
        {"correct_index": 1},
    )
    assert prompt["question"] == "What is hello?"
    assert prompt["options"] == ["Bonsoir", "Bonjour"]
    assert grading["correct_answer"] == "Bonjour"


def test_normalize_admin_style_mcq():
    prompt, grading = normalize_question(
        "mcq_single",
        {"question": "Pick one", "options": ["a", "b"]},
        {"correct_answer": "b"},
    )
    assert prompt["text"] == "Pick one"
    assert grading["correct_answer"] == "b"


def test_normalize_explanation_block():
    kind, payload = normalize_block("explanation", {"text": "Hello class"})
    assert kind == "rich_text"
    assert payload["content"] == "Hello class"
    assert payload["text"] == "Hello class"


def test_grade_open_answer():
    from types import SimpleNamespace

    question = SimpleNamespace(
        question_kind="translation",
        prompt_payload={"question": "Translate: Hi"},
        grading_payload={"accepted_answers": ["Bonjour", "Salut"]},
    )
    assert grade_answer(question, "bonjour") is True
    assert grade_answer(question, "wrong") is False


def test_grade_reorder_answer():
    from types import SimpleNamespace

    question = SimpleNamespace(
        question_kind="reorder",
        prompt_payload={"question": "Build the sentence"},
        grading_payload={"correct_order": ["Je", "voudrais", "un", "the"]},
    )
    assert grade_answer(question, "Je voudrais un the") is True
    assert grade_answer(question, "Je un voudrais the") is False


def test_grade_match_pairs_answer():
    from types import SimpleNamespace

    question = SimpleNamespace(
        question_kind="match_pairs",
        prompt_payload={
            "question": "Match",
            "pairs": [
                {"left": "Bonjour", "right": "Hello"},
                {"left": "Merci", "right": "Thank you"},
            ],
        },
        grading_payload={},
    )
    assert grade_answer(question, "Bonjour -> Hello\nMerci -> Thank you") is True
    assert grade_answer(question, "Bonjour -> Thank you\nMerci -> Hello") is False
