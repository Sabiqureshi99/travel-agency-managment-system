"""
core/base_model.py
==================
Base SQLAlchemy declarative model with full audit trail support.

Every table that inherits from ``Base`` automatically gets:
    - ``id``          — UUID primary key (stored as string for SQLite compat.)
    - ``created_at``  — timestamp of record creation
    - ``updated_at``  — auto-updated timestamp on every change
    - ``created_by``  — user ID who created the record
    - ``updated_by``  — user ID who last modified the record
    - ``is_deleted``  — soft-delete flag (use ``is_active`` property)
    - ``deleted_at``  — timestamp of soft deletion
    - ``deleted_by``  — user ID who performed the deletion
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """Generate a new UUID4 string for use as a primary key."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """SQLAlchemy declarative base — all models inherit from this."""
    pass


class TimestampMixin:
    """
    Mixin that adds created_at / updated_at audit timestamps.

    ``created_at`` is set once on INSERT.
    ``updated_at`` is refreshed automatically on every UPDATE.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated.",
    )


class SoftDeleteMixin:
    """
    Mixin that adds soft-delete support.

    Instead of physically deleting rows, set ``is_deleted = True`` and
    record who deleted it and when.
    """
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Soft-delete flag. True means the record is logically deleted.",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft-deleted.",
    )
    deleted_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="UUID of the user who soft-deleted this record.",
    )

    @property
    def is_active(self) -> bool:
        """Convenience property — True if the record has NOT been deleted."""
        return not self.is_deleted


class AuditMixin(TimestampMixin, SoftDeleteMixin):
    """
    Combines timestamp and soft-delete mixins plus user-tracking columns.

    Provides the full audit trail expected by TAMS:
        created_at, created_by, updated_at, updated_by,
        is_deleted, deleted_at, deleted_by
    """
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="UUID of the user who created this record.",
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        default=None,
        doc="UUID of the user who last updated this record.",
    )


class BaseModel(Base, AuditMixin):
    """
    Abstract base model for all TAMS database tables.

    Adds a UUID primary key on top of the AuditMixin columns.
    All concrete models should inherit from this class.

    Example::

        class Customer(BaseModel):
            __tablename__ = "customers"
            full_name: Mapped[str] = mapped_column(String(200))
    """
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        doc="UUID primary key.",
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the model instance to a plain dictionary.

        Only includes column values (not relationships).
        """
        result: dict[str, Any] = {}
        for col in self.__table__.columns:  # type: ignore[attr-defined]
            value = getattr(self, col.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[col.name] = value
        return result

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        pk = getattr(self, "id", "?")
        return f"<{cls_name} id={pk}>"
