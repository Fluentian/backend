"""User service — profile, settings, avatar management."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import AppRole, User, UserProfile, UserSettings

logger = logging.getLogger(__name__)


async def list_users(
    db: AsyncSession,
    role: AppRole | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[User], int]:
    """List users with optional role filter."""
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = list(result.scalars().all())

    return users, total


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    """Fetch a user by ID or raise 404."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")
    return user


async def update_user(db: AsyncSession, user: User, **kwargs: object) -> User:
    """Update user fields."""
    for key, value in kwargs.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


async def update_profile(db: AsyncSession, user_id: UUID, **kwargs: object) -> UserProfile:
    """Update user profile fields."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("Profile not found")

    for key, value in kwargs.items():
        if value is not None and hasattr(profile, key):
            setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_settings(db: AsyncSession, user_id: UUID, **kwargs: object) -> UserSettings:
    """Update user settings fields."""
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    user_settings = result.scalar_one_or_none()
    if user_settings is None:
        raise NotFoundError("Settings not found")

    for key, value in kwargs.items():
        if value is not None and hasattr(user_settings, key):
            setattr(user_settings, key, value)
    await db.commit()
    await db.refresh(user_settings)
    return user_settings


async def update_avatar(db: AsyncSession, user_id: UUID, avatar_url: str) -> str:
    """Update the user's avatar URL."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError("Profile not found")

    profile.avatar_url = avatar_url
    await db.commit()
    return avatar_url
