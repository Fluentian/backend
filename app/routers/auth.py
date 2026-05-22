"""Auth router — registration, login, and token management."""

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserBriefResponse,
)
from app.schemas.common import MessageResponse
from app.services import auth_service

from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    user, access, refresh = await auth_service.register_user(
        db, req.username, req.email, req.password, req.ui_language_id
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": UserBriefResponse.model_validate(user),
    }


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and get tokens."""
    user, access, refresh = await auth_service.login_user(db, req.email, req.password)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": UserBriefResponse.model_validate(user),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh tokens."""
    user, access, refresh = await auth_service.refresh_tokens(db, req.refresh_token)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": UserBriefResponse.model_validate(user),
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(
    user: User = Depends(get_current_user),
    authorization: str | None = Header(None)
):
    """Log out user and revoke token."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    await auth_service.logout_user(user.id, token)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset."""
    code = await auth_service.request_password_reset(db, req.email)
    res = {"message": "Password reset email sent if account exists"}
    if code: res["detail"] = code # For MVP debug
    return res


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password with token."""
    await auth_service.reset_password(db, req.token, req.new_password)
    return {"message": "Password updated successfully"}
