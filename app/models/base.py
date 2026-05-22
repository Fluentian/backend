"""SQLAlchemy declarative base and shared mixins for all ORM models."""

from datetime import datetime
import uuid
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all Fluentian ORM models."""

    pass


class UUIDMixin:
    """Adds a UUID primary key column to any model."""

    id: Mapped[uuid.UUID] = mapped_column(  # type: ignore[assignment]
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
