"""Progress router — completions, stats, and enrollment."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user, get_pagination
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.progress import (
    CompleteLessonRequest,
    CompleteLessonResponse,
    EnrollmentResponse,
    LessonProgressResponse,
    UnitProgressResponse,
    UserStatsResponse,
)
from app.services import progress_service
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/lessons/{lesson_id}/complete", response_model=CompleteLessonResponse)
async def complete_lesson(lesson_id: UUID, req: CompleteLessonRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Submit lesson results."""
    return await progress_service.complete_lesson(db, user, lesson_id, **req.model_dump())


@router.get("/me/lessons", response_model=PaginatedResponse[LessonProgressResponse])
async def get_my_lessons(completed: bool | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user), pagination: dict = Depends(get_pagination)):
    """Get current user's lesson progress."""
    items, total = await progress_service.get_user_lesson_progress(db, user.id, completed, pagination["offset"], pagination["limit"])
    return PaginatedResponse(
        items=[LessonProgressResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/me/units", response_model=PaginatedResponse[UnitProgressResponse])
async def get_my_units(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user), pagination: dict = Depends(get_pagination)):
    """Get current user's unit progress."""
    items, total = await progress_service.get_user_unit_progress(db, user.id, pagination["offset"], pagination["limit"])
    return PaginatedResponse(
        items=[UnitProgressResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Get aggregate stats."""
    return await progress_service.get_user_stats(db, user)


@router.post("/enroll/{course_id}", response_model=EnrollmentResponse)
async def enroll(course_id: UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Enroll in a course."""
    return await progress_service.enroll_in_course(db, user.id, course_id)
