"""Progress router — completions, stats, and enrollment."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, get_pagination, require_role
from app.models.user import AppRole, User
from app.schemas.common import PaginatedResponse
from app.schemas.progress import (
    CompleteLessonRequest,
    CompleteLessonResponse,
    EnrollmentResponse,
    LessonProgressResponse,
    UnitProgressResponse,
    UserStatsResponse,
)
from app.services import progress_service, user_service
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/lessons/{lesson_id}/complete", response_model=CompleteLessonResponse)
async def complete_lesson(
    lesson_id: UUID,
    req: CompleteLessonRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit lesson results."""
    return await progress_service.complete_lesson(
        db, user, lesson_id, score=req.score, answers=req.answers, time_seconds=req.time_seconds
    )


@router.get("/me/lessons", response_model=PaginatedResponse[LessonProgressResponse])
async def get_my_lessons(
    completed: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
    pagination: dict = Depends(get_pagination),
):
    """Get current user's lesson progress."""
    items, total = await progress_service.get_user_lesson_progress(
        db, user.id, completed, pagination["offset"], pagination["limit"]
    )
    return PaginatedResponse(
        items=[LessonProgressResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/me/units", response_model=PaginatedResponse[UnitProgressResponse])
async def get_my_units(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
    pagination: dict = Depends(get_pagination),
):
    """Get current user's unit progress."""
    items, total = await progress_service.get_user_unit_progress(
        db, user.id, pagination["offset"], pagination["limit"]
    )
    return PaginatedResponse(
        items=[UnitProgressResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get aggregate stats."""
    return await progress_service.get_user_stats(db, user)


@router.get("/users/{user_id}/lessons", response_model=PaginatedResponse[LessonProgressResponse])
async def get_user_lessons(
    user_id: UUID,
    completed: bool | None = None,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(AppRole.admin)),
    pagination: dict = Depends(get_pagination),
):
    """Get a student's lesson progress for admin review."""
    del admin_user
    items, total = await progress_service.get_user_lesson_progress(
        db, user_id, completed, pagination["offset"], pagination["limit"]
    )
    return PaginatedResponse(
        items=[LessonProgressResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/users/{user_id}/units", response_model=PaginatedResponse[UnitProgressResponse])
async def get_user_units(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(AppRole.admin)),
    pagination: dict = Depends(get_pagination),
):
    """Get a student's unit progress for admin review."""
    del admin_user
    items, total = await progress_service.get_user_unit_progress(
        db, user_id, pagination["offset"], pagination["limit"]
    )
    return PaginatedResponse(
        items=[UnitProgressResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/users/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(AppRole.admin)),
):
    """Get aggregate student stats for admin review."""
    del admin_user
    student = await user_service.get_user_by_id(db, user_id)
    return await progress_service.get_user_stats(db, student)


@router.post("/enroll/{course_id}", response_model=EnrollmentResponse)
async def enroll(
    course_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Enroll in a course."""
    return await progress_service.enroll_in_course(db, user.id, course_id)
