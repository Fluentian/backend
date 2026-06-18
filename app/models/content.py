"""Content domain models: Language, MediaAsset, TtsVoice, Course, CourseEnrollment,
PathUnit, Lesson, LessonBlock, Question."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

# ── Enums ───────────────────────────────────────────────


class LessonKind(str, enum.Enum):
    """Types of lesson content."""

    grammar_explainer = "grammar_explainer"
    dialogue = "dialogue"
    vocabulary = "vocabulary"
    pronunciation = "pronunciation"
    listening = "listening"
    reading = "reading"
    writing = "writing"
    speaking = "speaking"
    cultural_bridge = "cultural_bridge"
    exam_drill = "exam_drill"
    roleplay_simulation = "roleplay_simulation"


class UnitKind(str, enum.Enum):
    """Types of path units."""

    core = "core"
    practice = "practice"
    story = "story"
    checkpoint = "checkpoint"


class QuestionKind(str, enum.Enum):
    """Types of assessment questions."""

    mcq_single = "mcq_single"
    mcq_multi = "mcq_multi"
    fill_blank = "fill_blank"
    reorder = "reorder"
    match_pairs = "match_pairs"
    short_text = "short_text"
    translation = "translation"
    speech_record = "speech_record"
    listening_comprehension = "listening_comprehension"
    dictation = "dictation"


class CultureStoryMediaType(str, enum.Enum):
    """Supported media types for culture exploration stories."""

    image = "image"
    video = "video"


# ── Models ──────────────────────────────────────────────


class Language(UUIDMixin, TimestampMixin, Base):
    """Supported languages in the platform."""

    __tablename__ = "languages"

    iso_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    english_name: Mapped[str] = mapped_column(String(100), nullable=False)
    native_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Language id={self.id} code={self.iso_code!r}>"


class MediaAsset(UUIDMixin, Base):
    """Uploaded media files stored in S3-compatible storage."""

    __tablename__ = "media_assets"

    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MediaAsset id={self.id} key={self.storage_key!r}>"


class TtsVoice(UUIDMixin, Base):
    """Text-to-speech voice configuration."""

    __tablename__ = "tts_voices"

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    voice_key: Mapped[str] = mapped_column(String(100), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False
    )
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<TtsVoice id={self.id} provider={self.provider!r} key={self.voice_key!r}>"


class Course(UUIDMixin, Base):
    """A structured learning course."""

    __tablename__ = "courses"

    target_language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    level_min: Mapped[str] = mapped_column(String(5), nullable=False)
    level_max: Mapped[str] = mapped_column(String(5), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    units: Mapped[list["PathUnit"]] = relationship(
        "PathUnit", back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson", back_populates="course", lazy="noload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id} code={self.code!r}>"


class CourseEnrollment(UUIDMixin, Base):
    """Tracks which users are enrolled in which courses."""

    __tablename__ = "course_enrollments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<CourseEnrollment id={self.id} user={self.user_id} course={self.course_id}>"


class PathUnit(UUIDMixin, TimestampMixin, Base):
    """A unit within a course's learning path."""

    __tablename__ = "path_units"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    unit_kind: Mapped[UnitKind] = mapped_column(
        Enum(UnitKind, name="unit_kind", create_constraint=True), nullable=False
    )
    unit_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="units")
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson", back_populates="unit", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PathUnit id={self.id} unit_no={self.unit_no} title={self.title!r}>"


class Lesson(UUIDMixin, TimestampMixin, Base):
    """A single lesson within a unit."""

    __tablename__ = "lessons"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("path_units.id", ondelete="CASCADE"), nullable=False
    )
    lesson_kind: Mapped[LessonKind] = mapped_column(
        Enum(LessonKind, name="lesson_kind", create_constraint=True), nullable=False
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    unit: Mapped["PathUnit"] = relationship("PathUnit", back_populates="lessons")
    blocks: Mapped[list["LessonBlock"]] = relationship(
        "LessonBlock", back_populates="lesson", lazy="selectin", cascade="all, delete-orphan"
    )
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="lesson", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Lesson id={self.id} seq={self.sequence_no} title={self.title!r}>"


class LessonBlock(UUIDMixin, TimestampMixin, Base):
    """A content block within a lesson (text, audio, image, etc.)."""

    __tablename__ = "lesson_blocks"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    block_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    block_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[assignment]

    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="blocks")

    def __repr__(self) -> str:
        return f"<LessonBlock id={self.id} kind={self.block_kind!r} seq={self.sequence_no}>"


class Question(UUIDMixin, TimestampMixin, Base):
    """An assessment question within a lesson."""

    __tablename__ = "questions"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    question_kind: Mapped[QuestionKind] = mapped_column(
        Enum(QuestionKind, name="question_kind", create_constraint=True), nullable=False
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[assignment]
    grading_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # type: ignore[assignment]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question id={self.id} kind={self.question_kind.value} seq={self.sequence_no}>"


class CultureStory(UUIDMixin, TimestampMixin, Base):
    """A culture exploration story with media and translatable French text."""

    __tablename__ = "culture_stories"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    media: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)  # type: ignore[assignment]
    paragraphs: Mapped[list[list[dict]]] = mapped_column(
        JSONB, nullable=False, default=list
    )  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<CultureStory id={self.id} title={self.title!r}>"
