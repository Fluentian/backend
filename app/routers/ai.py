"""AI router — conversations and explanations."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user, get_pagination
from app.models.ai import AiConversation
from app.models.user import User
from app.schemas.ai import (
    AiChatResponse,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationSummary,
    CreateConversationRequest,
    ExplainRequest,
    ExplanationResponse,
    SendMessageRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.ai_service import ai_service
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(req: CreateConversationRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Start a new AI conversation."""
    conv = AiConversation(user_id=user.id, title=req.title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/conversations", response_model=PaginatedResponse[ConversationResponse])
async def list_conversations(user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), pagination: dict = Depends(get_pagination)):
    """List user's AI conversations."""
    query = select(AiConversation).where(AiConversation.user_id == user.id).order_by(AiConversation.started_at.desc())
    total = (await db.execute(select(func.count()).select_from(AiConversation).where(AiConversation.user_id == user.id))).scalar() or 0
    items = list((await db.execute(query.offset(pagination["offset"]).limit(pagination["limit"]))).scalars().all())
    return PaginatedResponse(
        items=[ConversationResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: UUID, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Get conversation with messages."""
    result = await db.execute(select(AiConversation).where(AiConversation.id == conversation_id, AiConversation.user_id == user.id))
    conv = result.scalar_one_or_none()
    if not conv: raise HTTPException(404, "Conversation not found")
    return conv


@router.post("/conversations/{conversation_id}/messages", response_model=AiChatResponse)
async def send_message(conversation_id: UUID, req: SendMessageRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Send a message to the AI and get a response."""
    result = await db.execute(select(AiConversation).where(AiConversation.id == conversation_id, AiConversation.user_id == user.id))
    conv = result.scalar_one_or_none()
    if not conv: raise HTTPException(404, "Conversation not found")
    
    return await ai_service.get_conversation_response(
        db, user.id, conversation_id, req.content, conv.messages, user.current_level, "English" # Default base lang
    )


@router.post("/explain", response_model=ExplanationResponse)
async def explain(req: ExplainRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Get an AI explanation for a concept."""
    text = await ai_service.generate_explanation(req.source_type, req.user_input, "English", user.current_level.value)
    return {"explanation_text": text, "created_at": datetime.now(timezone.utc), "id": UUID(int=0)} # Mock id for now

# Add imports for func, HTTPException, datetime, timezone
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, timezone
