"""Admin request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class CreateUserRequest(BaseModel):
    """Create a new user (admin only)."""

    email: EmailStr
    username: str
    role: str  # AppRole enum value
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is a valid AppRole."""
        valid_roles = ["super_admin", "admin", "teacher", "moderator", "student"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
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


class UpdateUserRoleRequest(BaseModel):
    """Update a user's role."""

    role: str  # AppRole enum value

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is a valid AppRole."""
        valid_roles = ["super_admin", "admin", "teacher", "moderator", "student"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        return v


class UserAdminResponse(BaseModel):
    """User details for admin panel."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    profile: "UserProfileResponse | None" = None

    @field_validator("role", mode="before")
    @classmethod
    def serialize_role(cls, v) -> str:
        """Convert role enum to string."""
        if hasattr(v, "value"):
            return v.value
        return str(v)


class UserProfileResponse(BaseModel):
    """User profile for admin response."""

    model_config = ConfigDict(from_attributes=True)

    display_name: str | None = None
    avatar_url: str | None = None


class UsersListResponse(BaseModel):
    """Paginated users list response."""

    data: list[UserAdminResponse]
    pagination: "PaginationInfo"


class PaginationInfo(BaseModel):
    """Pagination details."""

    page: int
    size: int
    total: int
    pages: int
