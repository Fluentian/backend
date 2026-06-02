"""Admin router — user management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_pagination, require_role
from app.models.user import AppRole, User
from app.schemas.admin import (
    CreateUserRequest,
    UpdateUserRoleRequest,
    UserAdminResponse,
    UsersListResponse,
)
from app.schemas.common import MessageResponse
from app.services import admin_user_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_admin_user(user: User = Depends(require_role(AppRole.admin))) -> User:
    """Dependency: ensures user is admin or super_admin."""
    return user


@router.post(
    "/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    req: CreateUserRequest,
    admin_user: User = Depends(_get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (requires admin or super_admin role)."""
    user, password = await admin_user_service.create_user(
        db=db,
        admin_user=admin_user,
        email=req.email,
        username=req.username,
        role=AppRole(req.role),
        first_name=req.first_name,
        last_name=req.last_name,
    )
    return UserAdminResponse.model_validate(user)


@router.get("/users", response_model=UsersListResponse)
async def list_users(
    admin_user: User = Depends(_get_admin_user),
    db: AsyncSession = Depends(get_db),
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    pagination: dict = Depends(get_pagination),
):
    """List users with optional filters (requires admin or super_admin role)."""
    role_filter = AppRole(role) if role else None
    users, total = await admin_user_service.list_users(
        db=db,
        admin_user=admin_user,
        role_filter=role_filter,
        is_active=is_active,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )

    return UsersListResponse(
        data=[UserAdminResponse.model_validate(u) for u in users],
        pagination={
            "page": pagination["page"],
            "size": pagination["size"],
            "total": total,
            "pages": (total + pagination["size"] - 1) // pagination["size"],
        },
    )


@router.patch("/users/{user_id}/role", response_model=UserAdminResponse)
async def update_user_role(
    user_id: UUID,
    req: UpdateUserRoleRequest,
    admin_user: User = Depends(_get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role (requires admin or super_admin role)."""
    user = await admin_user_service.update_user_role(
        db=db,
        admin_user=admin_user,
        user_id=user_id,
        new_role=AppRole(req.role),
    )
    return UserAdminResponse.model_validate(user)


@router.post("/users/{user_id}/deactivate", response_model=UserAdminResponse)
async def deactivate_user(
    user_id: UUID,
    admin_user: User = Depends(_get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a user account."""
    user = await admin_user_service.deactivate_user(
        db=db,
        admin_user=admin_user,
        user_id=user_id,
    )
    return UserAdminResponse.model_validate(user)


@router.post("/users/{user_id}/reactivate", response_model=UserAdminResponse)
async def reactivate_user(
    user_id: UUID,
    admin_user: User = Depends(_get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Reactivate a user account."""
    user = await admin_user_service.reactivate_user(
        db=db,
        admin_user=admin_user,
        user_id=user_id,
    )
    return UserAdminResponse.model_validate(user)


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
async def reset_user_password(
    user_id: UUID,
    admin_user: User = Depends(_get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new password for a user and send via email."""
    user, password = await admin_user_service.reset_user_password(
        db=db,
        admin_user=admin_user,
        user_id=user_id,
    )
    return {
        "message": "Password reset successfully. New credentials sent to user's email.",
    }
