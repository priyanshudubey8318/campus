"""AI interaction audit log model for Phase 5 PulseAssist subsystem.

Captures queries, model metrics, citation references, and performance telemetry
for administrative oversight without exposing PII.
"""

from datetime import datetime, timezone
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class AIInteractionLog(Base, UUIDPrimaryKeyMixin):
    """Audit log capturing AI queries, responses, cited chunk IDs, and latency."""

    __tablename__ = "ai_interaction_logs"
    __table_args__ = (
        Index("ix_ai_logs_inst_user", "institution_id", "user_id"),
        Index("ix_ai_logs_student", "student_context_id"),
        Index("ix_ai_logs_created", "created_at"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="RESTRICT", name="fk_ai_logs_institution"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="RESTRICT", name="fk_ai_logs_user"),
        nullable=False,
    )
    student_context_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("student_profiles.id", ondelete="SET NULL", name="fk_ai_logs_student"),
        nullable=True,
    )
    interaction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunks_cited_ids: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    verified_data_included: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=sa.text("false"),
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.func.now(),
        nullable=False,
    )

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id])
    user = relationship("User", foreign_keys=[user_id])
    student = relationship("StudentProfile", foreign_keys=[student_context_id])
