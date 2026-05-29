"""Social service — rooms, messages, and calls."""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.social import CallSession, Message, Room

logger = logging.getLogger(__name__)


async def list_rooms(
    db: AsyncSession, target_language_id: UUID | None = None, offset: int = 0, limit: int = 20
) -> tuple[list[Room], int]:
    """List public rooms."""
    query = select(Room)
    count_query = select(func.count()).select_from(Room)
    if target_language_id:
        query = query.where(Room.target_language_id == target_language_id)
        count_query = count_query.where(Room.target_language_id == target_language_id)
    total = (await db.execute(count_query)).scalar() or 0
    items = list((await db.execute(query.offset(offset).limit(limit))).scalars().all())
    return items, total


async def create_room(db: AsyncSession, user_id: UUID, **kwargs: object) -> Room:
    """Create a new chat room."""
    room = Room(created_by=user_id, **kwargs)  # type: ignore[arg-type]
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def list_messages(
    db: AsyncSession, room_id: UUID, offset: int = 0, limit: int = 30
) -> tuple[list[Message], int]:
    """List messages in a room (newest first)."""
    query = select(Message).where(Message.room_id == room_id).order_by(Message.created_at.desc())
    count_query = select(func.count()).select_from(Message).where(Message.room_id == room_id)
    total = (await db.execute(count_query)).scalar() or 0
    items = list((await db.execute(query.offset(offset).limit(limit))).scalars().all())
    return items, total


async def create_message(
    db: AsyncSession, user_id: UUID, room_id: UUID, **kwargs: object
) -> Message:
    """Create a new message."""
    msg = Message(sender_user_id=user_id, room_id=room_id, **kwargs)  # type: ignore[arg-type]
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def create_call(
    db: AsyncSession, user_id: UUID, room_id: UUID, **kwargs: object
) -> CallSession:
    """Create a call session."""
    call = CallSession(started_by=user_id, room_id=room_id, **kwargs)  # type: ignore[arg-type]
    db.add(call)
    await db.commit()
    await db.refresh(call)
    return call


async def end_call(db: AsyncSession, call_id: UUID) -> CallSession:
    """End a call session."""
    result = await db.execute(select(CallSession).where(CallSession.id == call_id))
    call = result.scalar_one_or_none()
    if not call:
        raise NotFoundError("Call session not found")
    call.status = "ended"
    await db.commit()
    await db.refresh(call)
    return call
