"""Notification router."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user, get_pagination

# Re-define schema reference to avoid conflict with model name
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services import notification_service
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=PaginatedResponse)
async def list_notifications(
    response: Response,
    is_read: bool | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(get_pagination),
):
    """List user notifications."""
    items, total, unread = await notification_service.list_notifications(
        db, user.id, is_read, pagination["offset"], pagination["limit"]
    )
    response.headers["X-Unread-Count"] = str(unread)
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.patch("/{notification_id}/read", response_model=MessageResponse)
async def mark_read(
    notification_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark notification as read."""
    await notification_service.mark_read(db, user.id, notification_id)
    return {"message": "Notification marked as read"}


@router.patch("/read-all", response_model=MessageResponse)
async def mark_all_read(
    user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read."""
    await notification_service.mark_all_read(db, user.id)
    return {"message": "All notifications marked as read"}
