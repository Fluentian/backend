"""Notification router."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.database import get_db
from app.dependencies import get_current_active_user, get_pagination, require_role

# Re-define schema reference to avoid conflict with model name
from app.models.user import AppRole, User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import CreateNotificationRequest, NotificationResponse
from app.services import notification_service
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _can_view_broadcast_history(user: User) -> bool:
    role_power = {
        AppRole.super_admin: 100,
        AppRole.admin: 80,
        AppRole.teacher: 60,
        AppRole.moderator: 40,
        AppRole.student: 20,
    }
    return role_power.get(user.role, 0) >= role_power[AppRole.moderator]


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    response: Response,
    is_read: bool | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: dict = Depends(get_pagination),
):
    """List user notifications."""
    if _can_view_broadcast_history(user):
        items, total, unread = await notification_service.list_all_notifications(
            db, is_read, pagination["offset"], pagination["limit"]
        )
    else:
        items, total, unread = await notification_service.list_notifications(
            db, user.id, is_read, pagination["offset"], pagination["limit"]
        )
    response.headers["X-Unread-Count"] = str(unread)
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    req: CreateNotificationRequest,
    admin_user: User = Depends(require_role(AppRole.moderator)),
    db: AsyncSession = Depends(get_db),
):
    """Create a direct notification or broadcast one to all students."""
    del admin_user
    if str(req.user_id).lower() == "global":
        sent_count = await notification_service.broadcast_notification(db, req.title, req.body)
        return {
            "message": "Broadcast notification sent",
            "detail": f"{sent_count} students notified",
        }
    try:
        target_user_id = UUID(str(req.user_id))
    except ValueError as exc:
        raise ValidationError("user_id must be a UUID or global") from exc
    await notification_service.create_notification(db, target_user_id, req.title, req.body)
    return {"message": "Notification sent"}


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
