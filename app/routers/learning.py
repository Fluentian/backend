"""MVP learner workflows: feedback and placement."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, require_role
from app.models.user import AppRole, User
from app.schemas.learning import (
    CreateLessonFeedbackRequest,
    LessonFeedbackResponse,
    PlacementResultResponse,
    PlacementSubmissionRequest,
)
from app.services import learning_service

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post(
    "/lessons/{lesson_id}/feedback",
    response_model=LessonFeedbackResponse,
    status_code=201,
)
async def create_lesson_feedback(
    lesson_id: UUID,
    req: CreateLessonFeedbackRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit simple post-lesson feedback."""
    return await learning_service.create_lesson_feedback(
        db,
        user,
        lesson_id,
        rating=req.rating,
        category=req.category,
        comment=req.comment,
    )


@router.get(
    "/feedback",
    response_model=list[LessonFeedbackResponse],
    dependencies=[Depends(require_role(AppRole.teacher))],
)
async def list_feedback(
    lesson_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List lesson feedback for staff review."""
    return await learning_service.list_lesson_feedback(db, lesson_id)


@router.post("/placement/submit", response_model=PlacementResultResponse, status_code=201)
async def submit_placement(
    req: PlacementSubmissionRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a basic placement test and update user level."""
    return await learning_service.submit_placement(db, user, req.answers, req.detail)
