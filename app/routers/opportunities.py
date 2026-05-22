"""Opportunities router."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_pagination
from app.models.user import OpportunityBoard
from app.schemas.common import PaginatedResponse
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


from app.schemas.user import CreateOpportunityRequest, OpportunityResponse, OpportunityApplicationResponse, ApplyOpportunityRequest
from app.dependencies import require_role, get_current_user
from app.models.user import AppRole, OpportunityApplication, User
from sqlalchemy.orm import joinedload


@router.get("/", response_model=PaginatedResponse[OpportunityResponse])
async def list_opportunities(type: str | None = None, db: AsyncSession = Depends(get_db), pagination: dict = Depends(get_pagination)):
    """List active opportunities."""
    query = select(OpportunityBoard).where(OpportunityBoard.is_active.is_(True))
    if type: query = query.where(OpportunityBoard.type == type)
    
    total = (await db.execute(select(func.count()).select_from(OpportunityBoard).where(OpportunityBoard.is_active.is_(True)))).scalar() or 0
    items = list((await db.execute(query.offset(pagination["offset"]).limit(pagination["limit"]))).scalars().all())
    
    return PaginatedResponse(
        items=[OpportunityResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.post("/", response_model=OpportunityResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def create_opportunity(req: CreateOpportunityRequest, db: AsyncSession = Depends(get_db)):
    """Create a new opportunity (Admin only)."""
    item = OpportunityBoard(**req.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get single opportunity."""
    result = await db.execute(select(OpportunityBoard).where(OpportunityBoard.id == opportunity_id))
    item = result.scalar_one_or_none()
    if not item: raise HTTPException(404, "Not found")
    return item


@router.post("/{opportunity_id}/apply", response_model=OpportunityApplicationResponse)
async def apply_for_opportunity(
    opportunity_id: UUID, 
    req: ApplyOpportunityRequest, 
    user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Apply for an opportunity (Student)."""
    # Check if already applied
    existing = await db.execute(
        select(OpportunityApplication).where(
            OpportunityApplication.opportunity_id == opportunity_id,
            OpportunityApplication.user_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Already applied for this opportunity")
    
    application = OpportunityApplication(
        opportunity_id=opportunity_id,
        user_id=user.id,
        **req.model_dump()
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/{opportunity_id}/applications", response_model=list[OpportunityApplicationResponse], dependencies=[Depends(require_role(AppRole.admin))])
async def list_applications(opportunity_id: UUID, db: AsyncSession = Depends(get_db)):
    """List all applications for an opportunity (Admin only)."""
    result = await db.execute(
        select(OpportunityApplication)
        .options(joinedload(OpportunityApplication.user))
        .where(OpportunityApplication.opportunity_id == opportunity_id)
    )
    return list(result.scalars().all())


@router.patch("/applications/{application_id}/status", response_model=OpportunityApplicationResponse, dependencies=[Depends(require_role(AppRole.admin))])
async def update_application_status(application_id: UUID, status: str, db: AsyncSession = Depends(get_db)):
    """Update application status (Admin only)."""
    result = await db.execute(select(OpportunityApplication).where(OpportunityApplication.id == application_id))
    application = result.scalar_one_or_none()
    if not application: raise HTTPException(404, "Application not found")
    
    application.status = status
    await db.commit()
    await db.refresh(application)
    return application
