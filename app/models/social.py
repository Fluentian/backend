"""Social domain models: Room, Message, CallSession."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class RoomKind(str, enum.Enum):
    """Types of chat rooms."""

    dm = "dm"
    group = "group"
    level_based = "level_based"


class MessageKind(str, enum.Enum):
    """Types of messages."""

    text = "text"
    image = "image"
    audio = "audio"
    system = "system"


class CallKind(str, enum.Enum):
    """Types of calls."""

    audio = "audio"
    video = "video"


class Room(UUIDMixin, Base):
    """A chat room for social interactions."""

    __tablename__ = "rooms"

    room_kind: Mapped[RoomKind] = mapped_column(
        Enum(RoomKind, name="room_kind", create_constraint=True), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_language_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="room", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Room id={self.id} kind={self.room_kind.value} title={self.title!r}>"


class Message(UUIDMixin, Base):
    """A message within a chat room."""

    __tablename__ = "messages"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    message_kind: Mapped[MessageKind] = mapped_column(
        Enum(MessageKind, name="message_kind", create_constraint=True), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} room={self.room_id} kind={self.message_kind.value}>"


class CallSession(UUIDMixin, Base):
    """A voice/video call session within a room."""

    __tablename__ = "call_sessions"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    started_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    call_kind: Mapped[CallKind] = mapped_column(
        Enum(CallKind, name="call_kind", create_constraint=True), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CallSession id={self.id} room={self.room_id} status={self.status!r}>"
