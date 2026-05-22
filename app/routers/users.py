"""User router — profiles, settings, and hearts."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    AvatarResponse,
    HeartsResponse,
    ProfileResponse,
    PublicUserResponse,
    SettingsResponse,
    UpdateProfileRequest,
    UpdateSettingsRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_active_user)):
    """Get current user data."""
    return user


@router.patch("/me", response_model=UserResponse)
async def update_me(req: UpdateUserRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Update current user."""
    return await user_service.update_user(db, user, **req.model_dump(exclude_unset=True))


@router.patch("/me/profile", response_model=ProfileResponse)
async def update_my_profile(req: UpdateProfileRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Update user profile."""
    return await user_service.update_profile(db, user.id, **req.model_dump(exclude_unset=True))


@router.patch("/me/settings", response_model=SettingsResponse)
async def update_my_settings(req: UpdateSettingsRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Update user settings."""
    return await user_service.update_settings(db, user.id, **req.model_dump(exclude_unset=True))
 

@router.get("/me/hearts", response_model=HeartsResponse)
async def get_my_hearts(user: User = Depends(get_current_active_user)):
    """Get current heart count."""
    # TODO: Calculate next_refill_at
    return {"hearts": user.hearts, "next_refill_at": None}


@router.post("/me/avatar", response_model=AvatarResponse)
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Upload avatar image."""
    # TODO: Implement actual S3 upload
    mock_url = f"https://s3.amazonaws.com/fluentian/avatars/{user.id}.jpg"
    url = await user_service.update_avatar(db, user.id, mock_url)
    return {"avatar_url": url}


@router.get("/{user_id}", response_model=PublicUserResponse)
async def get_user_public(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a public user profile."""
    user = await user_service.get_user_by_id(db, user_id)
    return PublicUserResponse.model_validate(user)
