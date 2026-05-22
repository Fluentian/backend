"""Content router — courses, units, and lessons."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_pagination, require_role
from app.models.content import Language
from app.models.user import AppRole
from app.schemas.common import PaginatedResponse
from app.schemas.content import (
    BlockResponse,
    CourseResponse,
    CreateBlockRequest,
    CreateCourseRequest,
    CreateLessonRequest,
    CreateQuestionRequest,
    CreateUnitRequest,
    LanguageResponse,
    LessonDetailResponse,
    LessonResponse,
    QuestionResponse,
    UnitResponse,
)
from app.services import content_service
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/languages", response_model=list[LanguageResponse])
async def list_languages(db: AsyncSession = Depends(get_db)):
    """List all available languages."""
    result = await db.execute(select(Language))
    return result.scalars().all()


@router.get("/courses", response_model=PaginatedResponse[CourseResponse])
async def list_courses(level: str | None = None, db: AsyncSession = Depends(get_db), pagination: dict = Depends(get_pagination)):
    """List published courses."""
    items, total = await content_service.list_courses(db, level, pagination["offset"], pagination["limit"])
    return PaginatedResponse(
        items=[CourseResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(course_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get course details with units."""
    return await content_service.get_course(db, course_id)


@router.get("/courses/{course_id}/units", response_model=list[UnitResponse])
async def list_units(course_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all units for a course."""
    return await content_service.get_course_units(db, course_id)


@router.get("/lessons/{lesson_id}", response_model=LessonDetailResponse)
async def get_lesson(lesson_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get full lesson detail."""
    return await content_service.get_lesson(db, lesson_id)


@router.get("/lessons/{lesson_id}/questions", response_model=list)
async def list_questions(lesson_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all questions for a lesson."""
    return await content_service.get_lesson_questions(db, lesson_id)


@router.get("/lessons", response_model=PaginatedResponse[LessonResponse])
async def list_lessons(course_id: UUID | None = None, unit_id: UUID | None = None, db: AsyncSession = Depends(get_db), pagination: dict = Depends(get_pagination)):
    """List all lessons (Admin only/Development)."""
    items, total = await content_service.list_lessons(db, course_id, unit_id, pagination["offset"], pagination["limit"])
    return PaginatedResponse(
        items=[LessonResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.patch("/lessons/{lesson_id}", response_model=LessonResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def update_lesson(lesson_id: UUID, req: dict, db: AsyncSession = Depends(get_db)):
    """Update a lesson's basic metadata (Admin only)."""
    return await content_service.update_lesson(db, lesson_id, **req)


# ── Admin Routes ──────────────────────────────────────


@router.post("/courses", response_model=CourseResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def create_course(req: CreateCourseRequest, db: AsyncSession = Depends(get_db)):
    """Create a new course (Admin only)."""
    return await content_service.create_course(db, **req.model_dump())


@router.post("/courses/{course_id}/units", response_model=UnitResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def create_unit(course_id: UUID, req: CreateUnitRequest, db: AsyncSession = Depends(get_db)):
    """Create a new unit (Admin only)."""
    return await content_service.create_unit(db, course_id, **req.model_dump())


@router.post("/units/{unit_id}/lessons", response_model=LessonResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def create_lesson(unit_id: UUID, req: CreateLessonRequest, db: AsyncSession = Depends(get_db)):
    """Create a new lesson (Admin only)."""
    return await content_service.create_lesson(db, unit_id, **req.model_dump())


@router.post("/lessons/{lesson_id}/blocks", response_model=BlockResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def add_block(lesson_id: UUID, req: CreateBlockRequest, db: AsyncSession = Depends(get_db)):
    """Add a new block to a lesson (Admin only)."""
    return await content_service.create_block(db, lesson_id, **req.model_dump())


@router.post("/lessons/{lesson_id}/questions", response_model=QuestionResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def add_question(lesson_id: UUID, req: CreateQuestionRequest, db: AsyncSession = Depends(get_db)):
    """Add a new question to a lesson (Admin only)."""
    return await content_service.create_question(db, lesson_id, **req.model_dump())


@router.patch("/blocks/{block_id}", response_model=BlockResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def update_block(block_id: UUID, req: dict, db: AsyncSession = Depends(get_db)):
    """Update a block (Admin only)."""
    return await content_service.update_block(db, block_id, **req)


@router.delete("/blocks/{block_id}", dependencies=[Depends(require_role(AppRole.admin))])
async def delete_block(block_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a block (Admin only)."""
    await content_service.delete_block(db, block_id)
    return {"status": "ok"}


@router.patch("/questions/{question_id}", response_model=QuestionResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def update_question(question_id: UUID, req: dict, db: AsyncSession = Depends(get_db)):
    """Update a question (Admin only)."""
    return await content_service.update_question(db, question_id, **req)


@router.delete("/questions/{question_id}", dependencies=[Depends(require_role(AppRole.admin))])
async def delete_question(question_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a question (Admin only)."""
    await content_service.delete_question(db, question_id)
    return {"status": "ok"}
