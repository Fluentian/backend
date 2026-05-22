"""Social router — rooms, messages, and calls."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_active_user, get_pagination
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.social import (
    CallResponse,
    ChatMessageResponse,
    CreateCallRequest,
    CreateChatMessageRequest,
    CreateRoomRequest,
    RoomResponse,
)
from app.services import social_service
from app.utils.helpers import compute_pages

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/rooms", response_model=PaginatedResponse[RoomResponse])
async def list_rooms(target_language_id: UUID | None = None, db: AsyncSession = Depends(get_db), pagination: dict = Depends(get_pagination)):
    """List public rooms."""
    items, total = await social_service.list_rooms(db, target_language_id, pagination["offset"], pagination["limit"])
    return PaginatedResponse(
        items=[RoomResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.post("/rooms", response_model=RoomResponse)
async def create_room(req: CreateRoomRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Create a new room."""
    return await social_service.create_room(db, user.id, **req.model_dump())


@router.get("/rooms/{room_id}/messages", response_model=PaginatedResponse[ChatMessageResponse])
async def list_messages(room_id: UUID, db: AsyncSession = Depends(get_db), pagination: dict = Depends(get_pagination)):
    """List room messages."""
    items, total = await social_service.list_messages(db, room_id, pagination["offset"], pagination["limit"])
    return PaginatedResponse(
        items=[ChatMessageResponse.model_validate(i) for i in items],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=compute_pages(total, pagination["size"]),
    )


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse)
async def send_message(room_id: UUID, req: CreateChatMessageRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Send a message to a room."""
    return await social_service.create_message(db, user.id, room_id, **req.model_dump())


@router.post("/rooms/{room_id}/calls", response_model=CallResponse)
async def create_call(room_id: UUID, req: CreateCallRequest, user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    """Start a call."""
    call = await social_service.create_call(db, user.id, room_id, **req.model_dump())
    return {
        "call_session_id": call.id,
        "room_token": "mock-token",
        "provider_room_name": f"room-{room_id}"
    }
