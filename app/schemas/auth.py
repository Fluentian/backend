"""Auth request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.constants import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


class LoginRequest(BaseModel):
    """Email + password login."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """New user registration."""

    username: str
    email: EmailStr
    password: str
    ui_language_id: UUID | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Enforce minimum password strength."""
        if len(v) < MIN_PASSWORD_LENGTH:
            msg = f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            raise ValueError(msg)
        if len(v) > MAX_PASSWORD_LENGTH:
            msg = f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
            raise ValueError(msg)
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Enforce username rules."""
        if len(v) < 3:
            msg = "Username must be at least 3 characters"
            raise ValueError(msg)
        if len(v) > 50:
            msg = "Username must be at most 50 characters"
            raise ValueError(msg)
        if not v.isalnum() and "_" not in v:
            msg = "Username may only contain letters, digits, and underscores"
            raise ValueError(msg)
        return v


class UserBriefResponse(BaseModel):
    """Minimal user info embedded in token response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    role: str
    current_level: str
    xp_total: int
    streak_days: int
    hearts: int
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT token pair returned on login / register / refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserBriefResponse


class RefreshRequest(BaseModel):
    """Refresh token rotation request."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Password reset with token."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Enforce minimum password strength."""
        if len(v) < MIN_PASSWORD_LENGTH:
            msg = f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            raise ValueError(msg)
        return v
