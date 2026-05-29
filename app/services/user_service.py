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


async def update_user_onboarding(db: AsyncSession, user: User, **kwargs: object) -> User:
    """Update user, profile, and settings in a single transaction during onboarding/profile PUT."""
    data = kwargs.copy()

    # 1. Map daily_goal_xp to daily_goal_minutes if provided
    if "daily_goal_xp" in data and data["daily_goal_xp"] is not None:
        xp = data["daily_goal_xp"]
        if not isinstance(xp, int):
            try:
                xp = int(xp)
            except (ValueError, TypeError):
                xp = 20
        # Casual (10 XP -> 5 min), Regular (20 XP -> 10 min), Serious (50 XP -> 20 min), Intense (100 XP -> 40 min)
        if xp <= 10:
            data["daily_goal_minutes"] = 5
        elif xp <= 20:
            data["daily_goal_minutes"] = 10
        elif xp <= 50:
            data["daily_goal_minutes"] = 20
        else:
            data["daily_goal_minutes"] = 40

    # 2. Map current_level (case-insensitive CEFR codes)
    if "current_level" in data and data["current_level"] is not None:
        level_str = str(data["current_level"]).lower().replace("/", "")
        # Map "c1c2" or unrecognized values
        if level_str in ["a0", "a1", "a2", "b1", "b2", "c1", "c2"]:
            data["current_level"] = level_str
        elif "c1" in level_str or "c2" in level_str:
            data["current_level"] = "c1"
        else:
            data["current_level"] = "a0"

    # 3. Update User model fields
    user_fields = [
        "username",
        "current_level",
        "daily_goal_minutes",
        "ui_language_id",
        "base_language_id",
        "target_language_id",
    ]
    for field in user_fields:
        if field in data and data[field] is not None:
            setattr(user, field, data[field])

    # 4. Update UserProfile fields
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    profile_fields = ["display_name", "avatar_url", "bio", "learning_goal", "preferred_voice_id"]
    for field in profile_fields:
        if field in data and data[field] is not None:
            setattr(profile, field, data[field])

    # 5. Update UserSettings fields
    settings = user.settings
    if settings is None:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    settings_fields = [
        "notifications_enabled",
        "offline_mode_enabled",
        "autoplay_audio",
        "sound_enabled",
    ]
    for field in settings_fields:
        if field in data and data[field] is not None:
            setattr(settings, field, data[field])

    await db.commit()
    await db.refresh(user)
    return user
