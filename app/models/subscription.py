"""Subscription domain model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class SubscriptionTier(str, enum.Enum):
    """Subscription plan tiers."""

    free = "free"
    plus = "plus"
    pro = "pro"


class Subscription(UUIDMixin, Base):
    """User subscription record."""

    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier, name="subscription_tier", create_constraint=True),
        default=SubscriptionTier.free,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} user={self.user_id} tier={self.tier.value}>"
