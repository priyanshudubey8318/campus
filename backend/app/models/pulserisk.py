"""PulseRisk database models for CampusPulse Phase 4.

Includes risk policies, student risk snapshots, and granular risk signal contributions.
All entities support immutable historical reproducibility and governed lifecycles.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
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


class RiskPolicy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional configuration policy governing Support Priority Index (SPI) weights and thresholds.
    
    Follows a governed lifecycle: DRAFT -> VALIDATED -> ACTIVE -> RETIRED.
    ACTIVE policies are immutable and strictly unique per institution scope.
    """

    __tablename__ = "risk_policies"
    __table_args__ = (
        CheckConstraint(
            "weight_attendance + weight_coursework + weight_assessment + weight_persistence = 1.000",
            name="chk_risk_policies_weight_sum",
        ),
        CheckConstraint(
            "threshold_moderate < threshold_elevated AND threshold_elevated < threshold_urgent",
            name="chk_risk_policies_threshold_order",
        ),
        UniqueConstraint(
            "institution_id",
            "code",
            "policy_version",
            name="uq_risk_policies_institution_code_version",
        ),
        Index("ix_risk_policies_institution_id", "institution_id"),
        Index("ix_risk_policies_status", "status"),
        Index(
            "uq_risk_policies_active_scope",
            "institution_id",
            unique=True,
            postgresql_where="status = 'ACTIVE'",
            sqlite_where="status = 'ACTIVE'",
        ),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Normalized weights (must sum to 1.000)
    weight_attendance: Mapped[Decimal] = mapped_column(Numeric(5, 3), default=Decimal("0.350"), nullable=False)
    weight_coursework: Mapped[Decimal] = mapped_column(Numeric(5, 3), default=Decimal("0.300"), nullable=False)
    weight_assessment: Mapped[Decimal] = mapped_column(Numeric(5, 3), default=Decimal("0.250"), nullable=False)
    weight_persistence: Mapped[Decimal] = mapped_column(Numeric(5, 3), default=Decimal("0.100"), nullable=False)

    # Threshold boundaries
    threshold_moderate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("25.00"), nullable=False)
    threshold_elevated: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("50.00"), nullable=False)
    threshold_urgent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("75.00"), nullable=False)

    # Persistence temporal half-life in days
    persistence_half_life_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)

    # Lifecycle status: DRAFT, VALIDATED, ACTIVE, RETIRED
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False)

    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    institution = relationship("Institution")
    snapshots: Mapped[List["StudentRiskSnapshot"]] = relationship("StudentRiskSnapshot", back_populates="policy")


class StudentRiskSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable periodic evaluation snapshot of student academic support priority.
    
    Includes student_id, evaluation_date, window_days, algorithm_version, and policy_version
    in its primary identity constraint to guarantee historical reproducibility.
    """

    __tablename__ = "student_risk_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "evaluation_date",
            "window_days",
            "algorithm_version",
            "policy_version",
            name="uq_student_risk_snapshots_identity",
        ),
        Index("ix_student_risk_snapshots_student_id_date", "student_id", "evaluation_date"),
        Index("ix_student_risk_snapshots_priority_tier", "priority_tier"),
        Index("ix_student_risk_snapshots_spi", "support_priority_index"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    policy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("risk_policies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    evaluation_date: Mapped[date] = mapped_column(Date, nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)

    # Computed Support Priority Index (0.0 to 100.0)
    support_priority_index: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    # Tier: LOW_PRIORITY, MODERATE_PRIORITY, ELEVATED_PRIORITY, URGENT_PRIORITY
    priority_tier: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"), nullable=False)
    data_quality: Mapped[str] = mapped_column(String(50), nullable=False)
    primary_driver: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Auditable JSON snapshots for zero-data-loss reproducibility
    input_snapshot_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decomposition_json: Mapped[str] = mapped_column(Text, nullable=False)
    summary_text: Mapped[str] = mapped_column(String(500), nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="EVALUATED", nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(20), default="pulserisk-v1.0", nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    student = relationship("StudentProfile")
    policy: Mapped["RiskPolicy"] = relationship("RiskPolicy", back_populates="snapshots")
    contributions: Mapped[List["RiskSignalContribution"]] = relationship(
        "RiskSignalContribution", back_populates="snapshot", cascade="all, delete-orphan"
    )


class RiskSignalContribution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Normalized relational contribution of an academic dimension to an SPI snapshot."""

    __tablename__ = "risk_signal_contributions"
    __table_args__ = (
        Index("ix_risk_signal_contributions_snapshot_dimension", "snapshot_id", "dimension"),
    )

    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_risk_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dimension: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ATTENDANCE, COURSEWORK, ASSESSMENTS, LONGITUDINAL_PERSISTENCE
    metric_label: Mapped[str] = mapped_column(String(100), nullable=False)
    observed_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    baseline_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delta_value: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    factor_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    assigned_weight: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False)
    weighted_contribution: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    data_quality: Mapped[str] = mapped_column(String(50), nullable=False)
    source_signal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    evidence_payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    snapshot: Mapped["StudentRiskSnapshot"] = relationship("StudentRiskSnapshot", back_populates="contributions")
