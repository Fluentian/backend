"""Notification service — management and delivery."""

import logging
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import Notification

logger = logging.getLogger(__name__)


async def list_notifications(
    db: AsyncSession, user_id: UUID, is_read: bool | None = None, offset: int = 0, limit: int = 20
) -> tuple[list[Notification], int, int]:
    """List notifications for a user."""
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    count_query = (
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    unread_query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
    )

    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    total = (await db.execute(count_query)).scalar() or 0
    unread = (await db.execute(unread_query)).scalar() or 0
    items = list((await db.execute(query.offset(offset).limit(limit))).scalars().all())
    return items, total, unread


async def mark_read(db: AsyncSession, user_id: UUID, notification_id: UUID) -> Notification:
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise NotFoundError("Notification not found")
    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return notif


async def mark_all_read(db: AsyncSession, user_id: UUID) -> None:
    """Mark all user notifications as read."""
    await db.execute(
        update(Notification).where(Notification.user_id == user_id).values(is_read=True)
    )
    await db.commit()


async def create_notification(
    db: AsyncSession, user_id: UUID, title: str, body: str
) -> Notification:
    """Create a new notification."""
    notif = Notification(user_id=user_id, title=title, body=body)
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif
