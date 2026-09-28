"""Audit log model for security tracking and migration verification."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Foundational audit log entity tracking administrative and system actions."""

    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, actor_id={self.actor_id})>"
