"""PulseCase database models for CampusPulse.

Implements:
- Support cases, lifecycle transitions, and human interventions.
- Confidential case notes with strict counselor isolation.
- Planned action-item interventions and scheduled follow-ups.
- Strictly decoupled from analytics engines and PulseAssist RAG.
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SupportCase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional student support and advising intervention case."""

    __tablename__ = "support_cases"
    __table_args__ = (
        UniqueConstraint("case_number", name="uq_support_cases_case_number"),
        CheckConstraint(
            "case_type IN ('ACADEMIC_SUPPORT', 'ATTENDANCE_INTERVENTION', 'EARLY_WARNING_TRIAGE', 'WELLBEING_REFERRAL')",
            name="chk_case_type",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'WAITING_FOR_STUDENT', 'FOLLOW_UP_SCHEDULED', 'RESOLVED', 'CLOSED')",
            name="chk_case_status",
        ),
        CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')",
            name="chk_case_priority",
        ),
        CheckConstraint(
            "trigger_source IN ('PULSERISK_SPI', 'PULSEWATCH_SHIFT', 'FACULTY_REFERRAL', 'STUDENT_REQUEST', 'MANUAL_ADVISOR')",
            name="chk_case_trigger_source",
        ),
        CheckConstraint(
            "assigned_staff_role IS NULL OR assigned_staff_role IN ('ADVISOR', 'COUNSELOR')",
            name="chk_case_assigned_role",
        ),
        CheckConstraint(
            "(status = 'RESOLVED' AND resolution_outcome IS NOT NULL AND resolved_at IS NOT NULL) OR (status != 'RESOLVED')",
            name="chk_case_resolution_integrity",
        ),
        CheckConstraint(
            "resolution_outcome IS NULL OR resolution_outcome IN ('IMPROVED_ENGAGEMENT', 'ACADEMIC_PLAN_ESTABLISHED', 'REFERRED_TO_EXTERNAL_RESOURCE', 'STUDENT_UNRESPONSIVE', 'NO_FURTHER_ACTION')",
            name="chk_case_resolution_outcome_enum",
        ),
        CheckConstraint(
            "(status = 'CLOSED' AND closed_at IS NOT NULL AND closed_by_user_id IS NOT NULL) OR (status != 'CLOSED')",
            name="chk_case_closed_integrity",
        ),
        CheckConstraint(
            "(case_type != 'WELLBEING_REFERRAL') OR (assigned_staff_role IS NULL OR assigned_staff_role = 'COUNSELOR')",
            name="chk_case_wellbeing_role",
        ),
        Index("ix_support_cases_inst_student", "institution_id", "student_id"),
        Index("ix_support_cases_inst_status", "institution_id", "status"),
        Index("ix_support_cases_assigned_staff", "institution_id", "assigned_staff_id", "status"),
        Index("ix_support_cases_referred_by", "institution_id", "referred_by_user_id"),
        Index("ix_support_cases_created", "institution_id", "created_at"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_number: Mapped[str] = mapped_column(String(50), nullable=False)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_references: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    assigned_staff_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    assigned_staff_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    referred_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )

    resolution_outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    closed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id])
    student = relationship("StudentProfile", foreign_keys=[student_id])
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
    referred_by = relationship("User", foreign_keys=[referred_by_user_id])
    closed_by = relationship("User", foreign_keys=[closed_by_user_id])

    notes: Mapped[List["CaseNote"]] = relationship(
        "CaseNote", back_populates="case", cascade="all, delete-orphan", order_by="CaseNote.created_at.asc()"
    )
    interventions: Mapped[List["CaseIntervention"]] = relationship(
        "CaseIntervention", back_populates="case", cascade="all, delete-orphan", order_by="CaseIntervention.created_at.asc()"
    )
    follow_ups: Mapped[List["CaseFollowUp"]] = relationship(
        "CaseFollowUp", back_populates="case", cascade="all, delete-orphan", order_by="CaseFollowUp.scheduled_date.asc()"
    )

    @property
    def assigned_advisor_id(self) -> Optional[str]:
        """Alias property for assigned_staff_id adhering to Master Spec Section 18 naming."""
        return self.assigned_staff_id


class CaseNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Timestamped note recorded on an intervention case."""

    __tablename__ = "case_notes"
    __table_args__ = (
        CheckConstraint(
            "note_type IN ('ADVISING_NOTE', 'STUDENT_INTERACTION', 'COUNSELOR_CONFIDENTIAL', 'ACTION_PLAN', 'SYSTEM_EVENT')",
            name="chk_case_note_type",
        ),
        CheckConstraint(
            "confidentiality_level IN ('STANDARD', 'RESTRICTED_ADVISING', 'COUNSELOR_CONFIDENTIAL')",
            name="chk_case_note_confidentiality",
        ),
        Index("ix_case_notes_case", "case_id", "created_at"),
        Index("ix_case_notes_confidentiality", "case_id", "confidentiality_level"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    note_type: Mapped[str] = mapped_column(String(50), default="ADVISING_NOTE", nullable=False)
    confidentiality_level: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    case = relationship("SupportCase", back_populates="notes")
    author = relationship("User", foreign_keys=[author_user_id])


class CaseIntervention(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Action plan item, student commitment, or referral intervention."""

    __tablename__ = "case_interventions"
    __table_args__ = (
        CheckConstraint(
            "intervention_type IN ('ONE_ON_ONE_ADVISING', 'PEER_TUTORING_REFERRAL', 'ACADEMIC_SKILLS_WORKSHOP', 'ATTENDANCE_CONTRACT', 'WELLBEING_SUPPORT', 'COURSE_LOAD_ADJUSTMENT')",
            name="chk_case_intervention_type",
        ),
        CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="chk_case_intervention_status",
        ),
        CheckConstraint(
            "(status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status != 'COMPLETED')",
            name="chk_case_intervention_completed",
        ),
        Index("ix_case_interventions_case", "case_id", "status"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    intervention_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    assigned_to_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    target_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PLANNED", nullable=False)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    case = relationship("SupportCase", back_populates="interventions")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])


class CaseFollowUp(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Scheduled review, check-in meeting, or follow-up session."""

    __tablename__ = "case_follow_ups"
    __table_args__ = (
        CheckConstraint(
            "follow_up_type IN ('CHECK_IN_MEETING', 'ACADEMIC_PROGRESS_REVIEW', 'ATTENDANCE_CHECK', 'WELLBEING_FOLLOW_UP')",
            name="chk_case_follow_up_type",
        ),
        CheckConstraint(
            "status IN ('SCHEDULED', 'COMPLETED', 'MISSED', 'RESCHEDULED', 'CANCELLED')",
            name="chk_case_follow_up_status",
        ),
        CheckConstraint(
            "(status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status != 'COMPLETED')",
            name="chk_case_follow_up_completed",
        ),
        Index("ix_case_follow_ups_case", "case_id", "scheduled_date"),
        Index("ix_case_follow_ups_staff_date", "assigned_staff_id", "scheduled_date"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("support_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    follow_up_type: Mapped[str] = mapped_column(String(50), default="CHECK_IN_MEETING", nullable=False)

    assigned_staff_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED", nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    case = relationship("SupportCase", back_populates="follow_ups")
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
