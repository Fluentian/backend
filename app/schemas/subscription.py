"""Subscription schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    tier: str
    status: str
    starts_at: datetime
    ends_at: datetime | None = None


class UpgradeRequest(BaseModel):
    tier: str
    provider: str
    provider_subscription_id: str
