"""Notification service — management and delivery."""

import logging
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import AppRole, Notification, User, UserSettings

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


async def list_all_notifications(
    db: AsyncSession, is_read: bool | None = None, offset: int = 0, limit: int = 20
) -> tuple[list[Notification], int, int]:
    """List all notifications for admin broadcast history."""
    query = select(Notification).order_by(Notification.created_at.desc())
    count_query = select(func.count()).select_from(Notification)
    unread_query = (
        select(func.count()).select_from(Notification).where(Notification.is_read.is_(False))
    )

    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
        count_query = count_query.where(Notification.is_read == is_read)

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


async def broadcast_notification(db: AsyncSession, title: str, body: str) -> int:
    """Create an in-app notification for every active student who accepts notifications."""
    result = await db.execute(
        select(User.id)
        .outerjoin(UserSettings, UserSettings.user_id == User.id)
        .where(
            User.role == AppRole.student,
            User.is_active.is_(True),
            or_(
                UserSettings.user_id.is_(None),
                UserSettings.notifications_enabled.is_(True),
            ),
        )
    )
    user_ids = list(result.scalars().all())
    for user_id in user_ids:
        db.add(Notification(user_id=user_id, title=title, body=body))
    await db.commit()
    return len(user_ids)


async def generate_daily_reminders(db: AsyncSession) -> int:
    """Generate daily streak reminders for users who haven't completed their daily goal today."""
    from datetime import datetime, timedelta, UTC
    now = datetime.now(UTC)
    today = now.date()

    # Find users who have a streak > 0, but haven't been active today
    # and have learning reminders enabled in settings
    result = await db.execute(
        select(User)
        .outerjoin(UserSettings, UserSettings.user_id == User.id)
        .where(
            User.streak_days > 0,
            User.is_active.is_(True),
            User.last_activity_date < now.replace(hour=0, minute=0, second=0, microsecond=0),
            or_(
                UserSettings.user_id.is_(None),
                (
                    UserSettings.notifications_enabled.is_(True)
                    & UserSettings.learning_reminder_enabled.is_(True)
                ),
            ),
        )
    )
    users = list(result.scalars().all())
    count = 0
    for user in users:
        title = "Keep your streak alive! 🔥"
        body = f"You have a {user.streak_days}-day streak! Practice for {user.daily_goal_minutes} minutes today to keep it going."
        db.add(Notification(user_id=user.id, title=title, body=body))
        count += 1
        
    await db.commit()
    return count
