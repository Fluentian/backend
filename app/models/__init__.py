"""Fluentian ORM models — import all models so they register with Base.metadata."""

from app.models.base import Base  # noqa: F401
from app.models.user import (  # noqa: F401
    AppRole,
    Notification,
    OpportunityBoard,
    ProficiencyLevel,
    User,
    UserProfile,
    UserSettings,
)
from app.models.content import (  # noqa: F401
    Course,
    CourseEnrollment,
    Language,
    Lesson,
    LessonBlock,
    LessonKind,
    MediaAsset,
    PathUnit,
    Question,
    QuestionKind,
    TtsVoice,
    UnitKind,
)
from app.models.progress import UserLessonProgress, UserUnitProgress  # noqa: F401

__all__ = [
    "Base",
    "AppRole",
    "ProficiencyLevel",
    "User",
    "UserProfile",
    "UserSettings",
    "Notification",
    "OpportunityBoard",
    "Language",
    "MediaAsset",
    "TtsVoice",
    "Course",
    "CourseEnrollment",
    "PathUnit",
    "Lesson",
    "LessonBlock",
    "Question",
    "LessonKind",
    "UnitKind",
    "QuestionKind",
    "UserLessonProgress",
    "UserUnitProgress",
]
