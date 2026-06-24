"""Shared FastAPI dependencies: auth, pagination, DB session."""

import logging
from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import MAX_PAGE_SIZE
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.database import get_db
from app.models.user import AppRole, User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Decode JWT and load the user if present, else return None."""
    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        token_type = payload.get("type")

        if not user_id_str or token_type != "access":
            return None

        user_id = UUID(user_id_str)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT and load the user from the database."""
    payload = decode_token(token)
    user_id_str = payload.get("sub")
    token_type = payload.get("type")

    if not user_id_str or token_type != "access":
        raise UnauthorizedError("Invalid access token")

    try:
        user_id = UUID(user_id_str)
    except ValueError as e:
        raise UnauthorizedError("Invalid token subject") from e

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise NotFoundError("User not found")
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Ensures the current user is active."""
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")
    return user


def require_role(role: AppRole) -> Callable:
    """Factory that returns a dependency checking the user's role with hierarchy."""

    # Define role hierarchy (higher value = more power)
    role_power = {
        AppRole.super_admin: 100,
        AppRole.admin: 80,
        AppRole.teacher: 60,
        AppRole.moderator: 40,
        AppRole.student: 20,
    }

    async def _check_role(
        user: User = Depends(get_current_active_user),
    ) -> User:
        user_power = role_power.get(user.role, 0)
        required_power = role_power.get(role, 0)

        if user_power < required_power:
            raise ForbiddenError(
                f"Insufficient permissions. Role '{role.value}' or higher required"
            )
        return user

    return _check_role


async def get_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
) -> dict:
    """Compute offset/limit from page/size query params."""
    clamped_size = min(size, MAX_PAGE_SIZE)
    return {
        "page": page,
        "size": clamped_size,
        "offset": (page - 1) * clamped_size,
        "limit": clamped_size,
    }
