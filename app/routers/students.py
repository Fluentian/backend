"""Students router — Admin management of students."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_pagination, require_role
from app.models.user import AppRole
from app.schemas.common import PaginatedResponse
from app.schemas.user import UpdateUserRequest, UserResponse
from app.services import user_service
from app.utils.helpers import compute_pages

router = APIRouter(
    prefix="/students", tags=["students"], dependencies=[Depends(require_role(AppRole.admin))]
)


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_students(
    db: AsyncSession = Depends(get_db), pagination: dict = Depends(get_pagination)
):
    """List all students (Admin only)."""
    # For MVP, we'll just filter by role student if possible, or return all users for now
    # Let's assume we want all users with role 'student'
    items, total = await user_service.list_users(
        db, role=AppRole.student, offset=pagination["offset"], limit=pagination["limit"]
    )
    return PaginatedResponse(
        items=[UserResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/{student_id}", response_model=UserResponse)
async def get_student(student_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get student details (Admin only)."""
    return await user_service.get_user_by_id(db, student_id)


@router.patch("/{student_id}", response_model=UserResponse)
async def update_student(
    student_id: UUID, req: UpdateUserRequest, db: AsyncSession = Depends(get_db)
):
    """Update student (Admin only)."""
    user = await user_service.get_user_by_id(db, student_id)
    return await user_service.update_user(db, user, **req.model_dump(exclude_unset=True))
