"""Admin user service — creating and managing users with role-based access."""

import logging
import secrets
import string
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password
from app.models.user import AppRole, User, UserProfile, UserSettings
from app.utils.email import send_admin_credentials_email

logger = logging.getLogger(__name__)


def _generate_strong_password(length: int = 8) -> str:
    """Generate a strong 8-digit password with uppercase, lowercase, digits, and symbols."""
    characters = (
        string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%"
    )
    password = "".join(secrets.choice(characters) for _ in range(length))
    return password


async def _check_role_permission(admin_user: User, target_role: AppRole) -> None:
    """Check if admin has permission to create/manage users with target_role."""
    # Super admin can manage all roles
    if admin_user.role == AppRole.super_admin:
        return

    # Admin can only manage: teacher, moderator, student
    allowed_roles = {AppRole.teacher, AppRole.moderator, AppRole.student}
    if admin_user.role == AppRole.admin and target_role in allowed_roles:
        return

    raise ForbiddenError(
        f"You don't have permission to manage {target_role.value} users"
    )


async def create_user(
    db: AsyncSession,
    admin_user: User,
    email: str,
    username: str,
    role: AppRole,
    first_name: str | None = None,
    last_name: str | None = None,
) -> tuple[User, str]:
    """
    Create a new user with admin authorization.
    Returns: (user, generated_password)
    """
    # Check authorization
    await _check_role_permission(admin_user, role)

    # Check uniqueness
    existing = await db.execute(
        select(User).where((User.email == email) | (User.username == username))
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("A user with this email or username already exists")

    # Generate strong password
    password = _generate_strong_password(8)
    password_hash = hash_password(password)

    # Create user with email pre-verified for admin-created accounts
    async with db.begin_nested():
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            email_verified=True,  # Admin-created users have verified emails
            is_active=True,
        )
        db.add(user)
        await db.flush()

        # Create profile and settings
        display_name = (
            f"{first_name} {last_name}".strip() if first_name or last_name else username
        )
        profile = UserProfile(user_id=user.id, display_name=display_name)
        settings_obj = UserSettings(user_id=user.id)

        db.add_all([profile, settings_obj])

    await db.commit()
    await db.refresh(user)

    # Send credentials email
    email_sent = await send_admin_credentials_email(
        email=email,
        username=username,
        password=password,
        role=role.value,
        recipient_name=display_name,
    )
    if not email_sent:
        logger.warning(
            f"Failed to send credentials email to {email}, but user was created"
        )

    logger.info(f"User {user.id} created by admin {admin_user.id}")

    return user, password


async def list_users(
    db: AsyncSession,
    admin_user: User,
    role_filter: AppRole | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[User], int]:
    """
    List users with optional filtering.
    Admins can only see users they have permission to manage.
    """
    query = select(User)

    # Role-based filtering
    if admin_user.role == AppRole.admin:
        # Admins can only see: teacher, moderator, student
        allowed_roles = [AppRole.teacher, AppRole.moderator, AppRole.student]
        query = query.where(User.role.in_(allowed_roles))

    # Apply optional filters
    if role_filter is not None:
        await _check_role_permission(admin_user, role_filter)
        query = query.where(User.role == role_filter)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(User).select_from(query.froms[0])
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    return users, total


async def update_user_role(
    db: AsyncSession,
    admin_user: User,
    user_id: UUID,
    new_role: AppRole,
) -> User:
    """
    Update a user's role with admin authorization.
    """
    # Check authorization for target role
    await _check_role_permission(admin_user, new_role)

    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    # Check authorization for current role
    await _check_role_permission(admin_user, user.role)

    user.role = new_role
    await db.commit()
    await db.refresh(user)

    logger.info(
        f"User {user_id} role updated to {new_role.value} by admin {admin_user.id}"
    )

    return user


async def deactivate_user(
    db: AsyncSession,
    admin_user: User,
    user_id: UUID,
) -> User:
    """
    Deactivate a user (soft delete).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    # Check authorization
    await _check_role_permission(admin_user, user.role)

    # Cannot deactivate super_admin if you're not super_admin
    if user.role == AppRole.super_admin and admin_user.role != AppRole.super_admin:
        raise ForbiddenError("Only super admins can deactivate other super admins")

    user.is_active = False
    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user_id} deactivated by admin {admin_user.id}")

    return user


async def reactivate_user(
    db: AsyncSession,
    admin_user: User,
    user_id: UUID,
) -> User:
    """
    Reactivate a deactivated user.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    # Check authorization
    await _check_role_permission(admin_user, user.role)
    

    user.is_active = True
    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user_id} reactivated by admin {admin_user.id}")

    return user


async def reset_user_password(
    db: AsyncSession,
    admin_user: User,
    user_id: UUID,
) -> tuple[User, str]:
    """
    Generate a new password for a user and send it via email.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")

    # Check authorization
    await _check_role_permission(admin_user, user.role)

    # Generate new password
    new_password = _generate_strong_password(8)
    user.password_hash = hash_password(new_password)

    await db.commit()
    await db.refresh(user)

    # Send new credentials email
    display_name = user.profile.display_name if user.profile else user.username
    email_sent = await send_admin_credentials_email(
        email=user.email,
        username=user.username,
        password=new_password,
        role=user.role.value,
        recipient_name=display_name,
    )
    if not email_sent:
        logger.warning(f"Failed to send password reset email to {user.email}")

    logger.info(f"User {user_id} password reset by admin {admin_user.id}")

    return user, new_password


# Import func at the end to avoid circular imports
from sqlalchemy import func
