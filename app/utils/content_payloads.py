"""Normalize lesson block and question JSON payloads across Admin, import, seed, and mobile."""

from __future__ import annotations

from typing import Any

from app.models.content import Question

# Block kinds the mobile app and Admin both understand (aliases map into these).
BLOCK_KIND_ALIASES: dict[str, str] = {
    "text": "rich_text",
    "explanation": "rich_text",
    "audio": "audio_clip",
}

MCQ_KINDS = frozenset({"mcq_single", "mcq_multi"})
OPEN_ANSWER_KINDS = frozenset(
    {
        "fill_blank",
        "translation",
        "short_text",
        "dictation",
        "listening_comprehension",
    }
)


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def normalize_block(block_kind: str, block_payload: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
    """Return canonical block_kind and payload with mirrored legacy fields."""
    payload = dict(block_payload or {})
    kind = BLOCK_KIND_ALIASES.get(block_kind, block_kind)

    if kind == "rich_text":
        text = payload.get("content") or payload.get("text") or ""
        payload["content"] = text
        payload["text"] = text
    elif kind == "vocabulary":
        payload["word"] = str(payload.get("word") or "")
        payload["meaning"] = str(payload.get("meaning") or "")
        if payload.get("audio_url"):
            payload["audio_url"] = str(payload["audio_url"])
    elif kind == "grammar_note":
        payload["rule"] = str(payload.get("rule") or payload.get("text") or "")
        payload["example"] = str(payload.get("example") or "")
    elif kind == "sentence_pair":
        target = payload.get("target") or payload.get("french") or payload.get("source") or ""
        base = payload.get("base") or payload.get("translation") or payload.get("english") or ""
        payload["target"] = str(target)
        payload["base"] = str(base)
    elif kind == "ai_hint":
        payload["hint"] = str(payload.get("hint") or payload.get("text") or "")
    elif kind == "audio_clip":
        url = payload.get("url") or payload.get("audio_url") or ""
        payload["url"] = str(url)
        payload["audio_url"] = str(url)
        payload["caption"] = str(payload.get("caption") or "")

    return kind, payload


def normalize_question(
    question_kind: str,
    prompt_payload: dict[str, Any] | None,
    grading_payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return canonical prompt and grading dicts with mirrored legacy keys."""
    prompt = dict(prompt_payload or {})
    grading = dict(grading_payload or {})

    qtext = (
        prompt.get("question")
        or prompt.get("text")
        or prompt.get("prompt")
        or ""
    )
    if qtext:
        qtext = str(qtext)
        prompt["question"] = qtext
        prompt["text"] = qtext

    options = _str_list(prompt.get("options"))
    if not options:
        options = _str_list(prompt.get("mcqOptions"))
    if options:
        prompt["options"] = options
        prompt["mcqOptions"] = options

    correct = grading.get("correct_answer") or prompt.get("mcqCorrectAnswer")
    if correct is None and grading.get("answer") is not None:
        correct = grading.get("answer")
    if correct is None and "correct_index" in grading and options:
        idx = grading["correct_index"]
        if isinstance(idx, int) and 0 <= idx < len(options):
            correct = options[idx]
    if correct is not None:
        correct = str(correct).strip()
        grading["correct_answer"] = correct
        prompt["mcqCorrectAnswer"] = correct

    accepted = _str_list(grading.get("accepted_answers"))
    if not accepted and correct:
        if question_kind in OPEN_ANSWER_KINDS or question_kind.startswith("mcq"):
            accepted = [correct]
    if accepted:
        grading["accepted_answers"] = accepted
        if not grading.get("correct_answer"):
            grading["correct_answer"] = accepted[0]

    if grading.get("explanation") is not None:
        grading["explanation"] = str(grading["explanation"])

    return prompt, grading


def normalize_question_model(question: Question) -> None:
    """Mutate ORM question payloads in place (used before API responses)."""
    prompt, grading = normalize_question(
        question.question_kind.value
        if hasattr(question.question_kind, "value")
        else str(question.question_kind),
        question.prompt_payload,
        question.grading_payload,
    )
    question.prompt_payload = prompt
    question.grading_payload = grading


def normalize_block_model(block: Any) -> None:
    """Mutate ORM block in place."""
    kind, payload = normalize_block(block.block_kind, block.block_payload)
    block.block_kind = kind
    block.block_payload = payload


def _answer_matches(user_answer: Any, accepted: list[str]) -> bool:
    if user_answer is None:
        return False
    normalized = str(user_answer).strip().casefold()
    if not normalized:
        return False
    return any(normalized == a.strip().casefold() for a in accepted if a)


def _clean_text(value: Any) -> str:
    return " ".join(
        str(value)
        .replace(".", "")
        .replace(",", "")
        .replace("!", "")
        .replace("?", "")
        .strip()
        .casefold()
        .split()
    )


def _parse_match_answer(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(k).strip(): str(v).strip() for k, v in value.items()}
    if not isinstance(value, str):
        return {}

    matches: dict[str, str] = {}
    for line in value.splitlines():
        if "->" not in line:
            continue
        left, right = line.split("->", 1)
        if left.strip() and right.strip():
            matches[left.strip()] = right.strip()
    return matches


def grade_answer(question: Question, user_answer: Any) -> bool:
    """Grade a single answer against stored question payloads."""
    kind = (
        question.question_kind.value
        if hasattr(question.question_kind, "value")
        else str(question.question_kind)
    )
    prompt, grading = normalize_question(
        kind, question.prompt_payload, question.grading_payload
    )

    if kind in MCQ_KINDS:
        options = _str_list(prompt.get("options"))
        correct = grading.get("correct_answer")
        if kind == "mcq_multi":
            correct_indices = grading.get("correct_indices")
            if isinstance(correct_indices, list) and options:
                expected = {options[i] for i in correct_indices if isinstance(i, int) and 0 <= i < len(options)}
                if isinstance(user_answer, list):
                    given = {str(x).strip() for x in user_answer}
                else:
                    given = {str(user_answer).strip()} if user_answer else set()
                return given == expected
        if correct is not None:
            return _answer_matches(user_answer, [str(correct)])
        return False

    if kind == "reorder":
        correct_order = grading.get("correct_order")
        if isinstance(correct_order, list):
            expected = " ".join(str(part).strip() for part in correct_order if str(part).strip())
            return _clean_text(user_answer) == _clean_text(expected)
        if grading.get("correct_answer"):
            return _clean_text(user_answer) == _clean_text(grading["correct_answer"])
        return False

    if kind == "match_pairs":
        expected: dict[str, str] = {}
        pairs = prompt.get("pairs")
        if isinstance(pairs, list):
            for pair in pairs:
                if isinstance(pair, dict):
                    left = pair.get("left") or pair.get("fr") or pair.get("target")
                    right = pair.get("right") or pair.get("en") or pair.get("base")
                    if left and right:
                        expected[str(left).strip()] = str(right).strip()
        matches = grading.get("matches")
        if isinstance(matches, dict):
            expected.update({str(k).strip(): str(v).strip() for k, v in matches.items()})
        submitted = _parse_match_answer(user_answer)
        return bool(expected) and submitted == expected

    if kind == "speech_record":
        if isinstance(user_answer, (int, float)):
            return float(user_answer) >= float(grading.get("min_score", 80))
        if isinstance(user_answer, str):
            digits = "".join(ch for ch in user_answer if ch.isdigit() or ch == ".")
            if digits:
                return float(digits) >= float(grading.get("min_score", 80))
        return bool(grading.get("allow_manual_pass", False))

    accepted = _str_list(grading.get("accepted_answers"))
    if not accepted and grading.get("correct_answer"):
        accepted = [str(grading["correct_answer"])]
    if accepted:
        return _answer_matches(user_answer, accepted)

    return False
