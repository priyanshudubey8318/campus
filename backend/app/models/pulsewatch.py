"""PulseWatch behavioral monitoring database models for CampusPulse.

Includes student behavior baselines, detected behavior events, and granular
supporting signal evidence.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentBehaviorBaseline(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persistent historical behavioral baseline for an individual student.
    
    Computed over historical windows ending strictly before the current observation window.
    Preserves algorithm versioning to enable retrospective analysis.
    """

    __tablename__ = "student_behavior_baselines"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "metric_type",
            "window_days",
            "algorithm_version",
            name="uq_student_baselines_metric_window_algo",
        ),
        Index("ix_student_baselines_student_id_metric", "student_id", "metric_type"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ATTENDANCE_RATE, SUBMISSION_RATE, ON_TIME_RATE, ASSESSMENT_AVERAGE
    baseline_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_quality: Mapped[str] = mapped_column(
        String(50), default="NO_DATA", nullable=False
    )  # NO_DATA, INSUFFICIENT_DATA, VALID_DATA
    window_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="pulsewatch-v1.0", nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    student = relationship("StudentProfile")


class BehaviorEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Auditable academic engagement change event detected for a student.
    
    Identified deterministically by student, window dates, and algorithm version.
    """

    __tablename__ = "behavior_events"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "observation_window_days",
            "window_start_date",
            "window_end_date",
            "algorithm_version",
            name="uq_behavior_events_student_window_algo",
        ),
        Index("ix_behavior_events_student_id_detected_at", "student_id", "detected_at"),
        Index("ix_behavior_events_student_id_severity", "student_id", "severity"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ACADEMIC_ENGAGEMENT_CHANGE, ATTENDANCE_DROP, COURSEWORK_IRREGULARITY, ASSESSMENT_DECLINE, MULTI_SIGNAL_CHANGE
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # NORMAL, MILD_CHANGE, MODERATE_CHANGE, SIGNIFICANT_CHANGE
    observation_window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    window_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    window_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary_text: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="DETECTED", nullable=False
    )  # DETECTED, ACKNOWLEDGED, RESOLVED, ARCHIVED
    algorithm_version: Mapped[str] = mapped_column(String(20), default="pulsewatch-v1.0", nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    student = relationship("StudentProfile")
    evidence_records: Mapped[List["BehaviorSignalEvidence"]] = relationship(
        "BehaviorSignalEvidence", back_populates="event", cascade="all, delete-orphan"
    )


class BehaviorSignalEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular supporting evidence metric attached to a detected behavior event."""

    __tablename__ = "behavior_signal_evidence"

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("behavior_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    signal_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ATTENDANCE_CHANGE, SUBMISSION_LATENESS, MISSED_ASSIGNMENT, ASSESSMENT_PERFORMANCE
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # NORMAL, MILD_CHANGE, MODERATE_CHANGE, SIGNIFICANT_CHANGE
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    baseline_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    delta_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    evidence_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    event: Mapped["BehaviorEvent"] = relationship("BehaviorEvent", back_populates="evidence_records")
