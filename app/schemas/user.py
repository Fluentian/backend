"""User, profile, and settings schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── User ────────────────────────────────────────────────


class UserResponse(BaseModel):
    """Full user response (private — returned for /me)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    role: str
    current_level: str
    xp_total: int
    streak_days: int
    hearts: int
    daily_goal_minutes: int
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime | None = None
    profile: "ProfileResponse | None" = None
    settings: "SettingsResponse | None" = None


class PublicUserResponse(BaseModel):
    """Public user profile (visible to other users)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    current_level: str
    streak_days: int


class UpdateUserRequest(BaseModel):
    """Partial update for user fields."""

    username: str | None = None
    daily_goal_minutes: int | None = None


class OnboardingUpdateRequest(BaseModel):
    """Update during onboarding / profile PUT."""

    # User fields
    username: str | None = None
    current_level: str | None = None
    daily_goal_minutes: int | None = None
    daily_goal_xp: int | None = None
    ui_language_id: UUID | None = None
    base_language_id: UUID | None = None
    target_language_id: UUID | None = None

    # Profile fields
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    learning_goal: str | None = None
    preferred_voice_id: UUID | None = None

    # Settings fields
    notifications_enabled: bool | None = None
    offline_mode_enabled: bool | None = None
    autoplay_audio: bool | None = None
    sound_enabled: bool | None = None


# ── Profile ─────────────────────────────────────────────


class ProfileResponse(BaseModel):
    """User profile response."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    learning_goal: str | None = None
    preferred_voice_id: UUID | None = None
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    """Partial update for profile fields."""

    display_name: str | None = None
    bio: str | None = None
    learning_goal: str | None = None
    preferred_voice_id: UUID | None = None


# ── Settings ────────────────────────────────────────────


class SettingsResponse(BaseModel):
    """User settings response."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    notifications_enabled: bool
    offline_mode_enabled: bool
    autoplay_audio: bool
    sound_enabled: bool
    updated_at: datetime | None = None


class UpdateSettingsRequest(BaseModel):
    """Partial update for settings fields."""

    notifications_enabled: bool | None = None
    offline_mode_enabled: bool | None = None
    autoplay_audio: bool | None = None
    sound_enabled: bool | None = None


# ── Hearts ──────────────────────────────────────────────


class HeartsResponse(BaseModel):
    """Current heart count and next refill."""

    hearts: int
    next_refill_at: datetime | None = None


# ── Avatar ──────────────────────────────────────────────


class AvatarResponse(BaseModel):
    """Avatar upload result."""


# ── Notifications ───────────────────────────────────────
class NotificationResponse(BaseModel):
    """Notification response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    body: str
    is_read: bool
    created_at: datetime


class CreateNotificationRequest(BaseModel):
    """Create a direct or broadcast notification."""

    user_id: UUID | str
    title: str
    body: str


# ── Opportunities ───────────────────────────────────────


class OpportunityResponse(BaseModel):
    """Opportunity listing response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    type: str
    deadline: datetime | None = None
    is_active: bool
    created_at: datetime


class CreateOpportunityRequest(BaseModel):
    """Create a new opportunity Listing."""

    title: str
    description: str
    type: str
    deadline: datetime | None = None
    is_active: bool = True


class OpportunityApplicationResponse(BaseModel):
    """Opportunity application response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    opportunity_id: UUID
    user_id: UUID
    full_name: str
    email: str
    phone: str | None = None
    education: str | None = None
    experience: str | None = None
    skills: str | None = None
    motivation: str
    status: str
    resume_url: str | None = None
    created_at: datetime
    # We'll include the user in a detailed response later if needed
    user: "PublicUserResponse | None" = None


class ApplyOpportunityRequest(BaseModel):
    """User request to apply for an opportunity."""

    full_name: str
    email: str
    phone: str | None = None
    education: str | None = None
    experience: str | None = None
    skills: str | None = None
    motivation: str
    resume_url: str | None = None
