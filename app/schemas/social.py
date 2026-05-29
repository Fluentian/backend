"""Social domain schemas: rooms, messages, calls."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Room ────────────────────────────────────────────────


class CreateRoomRequest(BaseModel):
    title: str
    room_kind: str
    target_language_id: UUID | None = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_kind: str
    title: str
    target_language_id: UUID | None = None
    created_by: UUID
    created_at: datetime


# ── Chat Message ────────────────────────────────────────


class CreateChatMessageRequest(BaseModel):
    body: str
    message_kind: str = "text"


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    sender_user_id: UUID
    message_kind: str
    body: str
    created_at: datetime


# ── Call ────────────────────────────────────────────────


class CreateCallRequest(BaseModel):
    call_kind: str = "audio"


class CallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    call_session_id: UUID
    room_token: str
    provider_room_name: str
