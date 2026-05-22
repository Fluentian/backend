"""AI domain models: AiConversation, AiConversationMessage, AiExplanation."""

from datetime import datetime
import uuid
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class AiConversation(UUIDMixin, Base):
    """A conversation session between a user and the AI tutor."""

    __tablename__ = "ai_conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    messages: Mapped[list["AiConversationMessage"]] = relationship(
        "AiConversationMessage", back_populates="conversation", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<AiConversation id={self.id} user={self.user_id} title={self.title!r}>"


class AiConversationMessage(UUIDMixin, Base):
    """A single message in an AI conversation."""

    __tablename__ = "ai_conversation_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_user_message: Mapped[bool] = mapped_column(Boolean, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    pronunciation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    conversation: Mapped["AiConversation"] = relationship(
        "AiConversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        role = "user" if self.is_user_message else "assistant"
        return f"<AiConversationMessage id={self.id} role={role}>"


class AiExplanation(UUIDMixin, Base):
    """AI-generated explanation for a lesson concept or question."""

    __tablename__ = "ai_explanations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True
    )
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AiExplanation id={self.id} user={self.user_id}>"
