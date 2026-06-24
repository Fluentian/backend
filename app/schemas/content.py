"""Content domain schemas: courses, units, lessons, blocks, questions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Language ────────────────────────────────────────────


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    iso_code: str
    english_name: str
    native_name: str
    is_active: bool
    created_at: datetime


# ── Course ──────────────────────────────────────────────


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_language_id: UUID
    code: str
    level_min: str
    level_max: str
    is_published: bool
    created_at: datetime
    units: list["UnitResponse"] = []


class CreateCourseRequest(BaseModel):
    target_language_id: UUID
    code: str
    level_min: str
    level_max: str
    is_published: bool = False


# ── Unit ────────────────────────────────────────────────


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    unit_kind: str
    unit_no: int
    title: str
    created_at: datetime
    lessons: list["LessonResponse"] = []


class CreateUnitRequest(BaseModel):
    unit_kind: str
    unit_no: int
    title: str


# ── Lesson ──────────────────────────────────────────────


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    unit_id: UUID
    lesson_kind: str
    sequence_no: int
    title: str
    estimated_minutes: int
    xp_reward: int
    is_published: bool


class LessonDetailResponse(LessonResponse):
    blocks: list["BlockResponse"] = []
    questions: list["QuestionResponse"] = []


class CreateLessonRequest(BaseModel):
    lesson_kind: str
    sequence_no: int
    title: str
    estimated_minutes: int = 5
    xp_reward: int = 10
    is_published: bool = False


# ── Block ───────────────────────────────────────────────


class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lesson_id: UUID
    block_kind: str
    sequence_no: int
    block_payload: dict[str, Any]
    created_at: datetime


class CreateBlockRequest(BaseModel):
    block_kind: str
    sequence_no: int
    block_payload: dict[str, Any] = {}


# ── Question ────────────────────────────────────────────


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lesson_id: UUID
    question_kind: str
    sequence_no: int
    difficulty: int
    prompt_payload: dict[str, Any]
    grading_payload: dict[str, Any]
    created_at: datetime


class CreateQuestionRequest(BaseModel):
    question_kind: str
    sequence_no: int
    difficulty: int = 1
    prompt_payload: dict[str, Any] = {}
    grading_payload: dict[str, Any] = {}


# Culture stories


class CultureStoryMedia(BaseModel):
    type: str
    url: str
    caption: str = ""


class CultureSentence(BaseModel):
    original: str
    translated: str


class CultureStoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    location: str
    category: str
    sequence_no: int
    is_published: bool
    media: list[CultureStoryMedia]
    paragraphs: list[list[CultureSentence]]
    created_at: datetime
    updated_at: datetime


class CreateCultureStoryRequest(BaseModel):
    title: str
    location: str
    category: str
    sequence_no: int = 0
    is_published: bool = False
    media: list[CultureStoryMedia] = []
    paragraphs: list[list[CultureSentence]] = []


class UpdateCultureStoryRequest(BaseModel):
    title: str | None = None
    location: str | None = None
    category: str | None = None
    sequence_no: int | None = None
    is_published: bool | None = None
    media: list[CultureStoryMedia] | None = None
    paragraphs: list[list[CultureSentence]] | None = None
