"""Subscription router."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.subscription import Subscription, SubscriptionTier
from app.models.user import User
from app.schemas.subscription import SubscriptionResponse, UpgradeRequest

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Get current active subscription."""
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.starts_at.desc()))
    sub = result.scalars().first()
    if not sub: raise HTTPException(404, "No subscription found")
    return sub


@router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade(req: UpgradeRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Upgrade subscription tier."""
    sub = Subscription(user_id=user.id, tier=SubscriptionTier(req.tier), status="active")
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub

from fastapi import HTTPException
