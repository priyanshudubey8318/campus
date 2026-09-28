"""PulseRecord database models for CampusPulse.

Implements:
- Leave requests, approval workflows, attachments, and history.
- Formal grievances, evidence metadata, investigation notes, adjudication, and appeals.
Strictly decoupled from analytics tables and intervention cases.
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LeaveRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional leave request entity submitted by an enrolled student."""

    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="chk_leave_dates",
        ),
        CheckConstraint(
            "days_count > 0",
            name="chk_leave_days_count",
        ),
        CheckConstraint(
            "leave_type IN ('MEDICAL', 'ACADEMIC_DUTY', 'PERSONAL', 'EMERGENCY', 'BEREAVEMENT')",
            name="chk_leave_type",
        ),
        CheckConstraint(
            "status IN ('SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CANCELLED')",
            name="chk_leave_status",
        ),
        Index("ix_leave_requests_inst_student", "institution_id", "student_id"),
        Index("ix_leave_requests_inst_status", "institution_id", "status"),
        Index("ix_leave_requests_student_dates", "student_id", "start_date", "end_date"),
        Index("ix_leave_requests_query_contract", "student_id", "status", "start_date", "end_date"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)

    reviewed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id])
    student = relationship("StudentProfile", foreign_keys=[student_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by_user_id])
    attachments: Mapped[List["LeaveAttachment"]] = relationship(
        "LeaveAttachment", back_populates="leave_request", cascade="all, delete-orphan"
    )


class LeaveAttachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cryptographic metadata and storage key for leave verification documents."""

    __tablename__ = "leave_attachments"
    __table_args__ = (
        CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 10485760",
            name="chk_leave_attachment_size",
        ),
        CheckConstraint(
            "mime_type IN ('application/pdf', 'image/jpeg', 'image/png')",
            name="chk_leave_attachment_mime",
        ),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    leave_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leave_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploader_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    leave_request: Mapped["LeaveRequest"] = relationship("LeaveRequest", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[uploader_user_id])


class Complaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Formal institutional grievance record submitted by student or authorized reporter."""

    __tablename__ = "complaints"
    __table_args__ = (
        UniqueConstraint("institution_id", "complaint_code", name="uq_complaints_inst_code"),
        CheckConstraint(
            "complainant_role IN ('STUDENT', 'EXTERNAL_REPORTER', 'FACULTY', 'OTHER')",
            name="chk_complaints_complainant_role",
        ),
        CheckConstraint(
            "category IN ('ACADEMIC_INTEGRITY', 'FACILITY_HARASSMENT', 'DISCRIMINATION', 'GRADING_DISPUTE', 'SAFETY_CONCERN', 'OTHER')",
            name="chk_complaints_category",
        ),
        CheckConstraint(
            "target_type IN ('STUDENT', 'FACULTY', 'DEPARTMENT', 'FACILITY', 'OTHER')",
            name="chk_complaints_target_type",
        ),
        CheckConstraint(
            "status IN ('SUBMITTED', 'UNDER_REVIEW', 'NEEDS_INFORMATION', 'VERIFIED', 'DISMISSED', 'OTHER_AUTHORIZED_OUTCOME', 'APPEALED', 'RESOLVED', 'CLOSED')",
            name="chk_complaints_status",
        ),
        CheckConstraint(
            "(status NOT IN ('VERIFIED', 'DISMISSED', 'OTHER_AUTHORIZED_OUTCOME', 'APPEALED', 'RESOLVED', 'CLOSED') AND adjudication_outcome IS NULL) "
            "OR (status IN ('VERIFIED', 'DISMISSED', 'OTHER_AUTHORIZED_OUTCOME', 'APPEALED', 'RESOLVED', 'CLOSED') AND adjudication_outcome IS NOT NULL)",
            name="chk_complaint_outcome_correlation",
        ),
        Index("ix_complaints_inst_status", "institution_id", "status"),
        Index("ix_complaints_complainant", "complainant_user_id", "status"),
        Index("ix_complaints_target_student", "target_student_id", "status"),
        Index("ix_complaints_reviewer", "assigned_reviewer_id", "status"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    complaint_code: Mapped[str] = mapped_column(String(50), nullable=False)
    complainant_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    complainant_role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_student_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    target_department_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)

    assigned_reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    adjudication_outcome: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    adjudication_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    info_request_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    info_response_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    closed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    institution = relationship("Institution", foreign_keys=[institution_id])
    complainant = relationship("User", foreign_keys=[complainant_user_id])
    target_student = relationship("StudentProfile", foreign_keys=[target_student_id])
    target_department = relationship("Department", foreign_keys=[target_department_id])
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    closed_by = relationship("User", foreign_keys=[closed_by_user_id])
    evidence: Mapped[List["ComplaintEvidence"]] = relationship(
        "ComplaintEvidence", back_populates="complaint", cascade="all, delete-orphan"
    )
    appeals: Mapped[List["ComplaintAppeal"]] = relationship(
        "ComplaintAppeal", back_populates="complaint", cascade="all, delete-orphan"
    )


class ComplaintEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cryptographic evidence metadata supporting a formal institutional grievance."""

    __tablename__ = "complaint_evidence"
    __table_args__ = (
        CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 20971520",
            name="chk_complaint_evidence_size",
        ),
        CheckConstraint(
            "mime_type IN ('application/pdf', 'image/jpeg', 'image/png', 'text/plain')",
            name="chk_complaint_evidence_mime",
        ),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    complaint_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploader_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    uploader_role: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sealed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="evidence")
    uploader = relationship("User", foreign_keys=[uploader_user_id])


class ComplaintAppeal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Formal appellate record contesting a completed grievance adjudication."""

    __tablename__ = "complaint_appeals"
    __table_args__ = (
        UniqueConstraint("complaint_id", "appeal_number", name="uq_complaint_appeals_seq"),
        CheckConstraint(
            "status IN ('SUBMITTED', 'UNDER_REVIEW', 'UPHELD', 'OVERTURNED', 'MODIFIED', 'DISMISSED')",
            name="chk_complaint_appeals_status",
        ),
        Index("ix_complaint_appeals_appellant", "appellant_user_id"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    complaint_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    appellant_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    appeal_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)

    reviewer_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disposition_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="appeals")
    appellant = relationship("User", foreign_keys=[appellant_user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_user_id])
