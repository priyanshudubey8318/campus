"""Pydantic schemas for the PulseRisk Support Prioritization Subsystem."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


RiskPolicyStatus = Literal["DRAFT", "VALIDATED", "ACTIVE", "RETIRED"]
PriorityTier = Literal["LOW_PRIORITY", "MODERATE_PRIORITY", "ELEVATED_PRIORITY", "URGENT_PRIORITY"]
RiskDimension = Literal["ATTENDANCE", "COURSEWORK", "ASSESSMENTS", "LONGITUDINAL_PERSISTENCE"]


class RiskPolicyBase(BaseModel):
    """Base schema for an institutional risk policy."""

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    weight_attendance: Decimal = Field(default=Decimal("0.350"), ge=0, le=1)
    weight_coursework: Decimal = Field(default=Decimal("0.300"), ge=0, le=1)
    weight_assessment: Decimal = Field(default=Decimal("0.250"), ge=0, le=1)
    weight_persistence: Decimal = Field(default=Decimal("0.100"), ge=0, le=1)
    threshold_moderate: Decimal = Field(default=Decimal("25.00"), ge=0, le=100)
    threshold_elevated: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)
    threshold_urgent: Decimal = Field(default=Decimal("75.00"), ge=0, le=100)
    persistence_half_life_days: int = Field(default=14, ge=1, le=90)
    policy_version: str = Field(default="v1.0", max_length=20)


class RiskPolicyCreate(RiskPolicyBase):
    """Schema for creating a new DRAFT risk policy."""

    institution_id: str


class RiskPolicyUpdate(BaseModel):
    """Schema for updating a DRAFT risk policy."""

    name: Optional[str] = None
    description: Optional[str] = None
    weight_attendance: Optional[Decimal] = None
    weight_coursework: Optional[Decimal] = None
    weight_assessment: Optional[Decimal] = None
    weight_persistence: Optional[Decimal] = None
    threshold_moderate: Optional[Decimal] = None
    threshold_elevated: Optional[Decimal] = None
    threshold_urgent: Optional[Decimal] = None
    persistence_half_life_days: Optional[int] = None


class RiskPolicyResponse(RiskPolicyBase):
    """Schema for returning risk policy details."""

    id: str
    institution_id: str
    status: RiskPolicyStatus
    activated_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RiskSignalContributionSchema(BaseModel):
    """Decomposed contribution metric for an academic dimension."""

    dimension: str
    metric_label: str
    observed_value: Optional[str] = None
    baseline_value: Optional[str] = None
    delta_value: Optional[str] = None
    factor_score: Decimal
    assigned_weight: Decimal
    weighted_contribution: Decimal
    data_quality: str
    source_signal: Optional[str] = None
    context_details: Optional[Dict[str, Any]] = None


class SafetyFloorTriggerSchema(BaseModel):
    """Details of a critical safety floor triggered during evaluation."""

    trigger_name: str
    mandated_tier: str
    mandated_floor: Decimal
    reason: str


class ExplainabilitySummarySchema(BaseModel):
    """Human-readable explainability narrative and primary driver."""

    summary: str
    primary_driver: Optional[str] = None
    institutional_notice: str = (
        "Support Priority Index represents deterministic friction indicators and does not infer "
        "personal, disciplinary, or medical circumstances."
    )


class PulseRiskSummaryResponse(BaseModel):
    """Decomposed, auditable Support Priority Index response for a student."""

    student_id: str
    evaluation_date: date
    observation_window_days: int
    support_priority_index: Decimal
    priority_tier: str
    confidence_score: Decimal
    data_quality: str
    primary_driver: Optional[str] = None
    algorithm_version: str = "pulserisk-v1.0"
    policy_version: str
    policy_name: str
    calculated_at: datetime
    contributions: List[RiskSignalContributionSchema] = []
    safety_floors_triggered: List[SafetyFloorTriggerSchema] = []
    explainability: ExplainabilitySummarySchema


class StudentRiskSnapshotResponse(BaseModel):
    """Persisted snapshot record response."""

    id: str
    student_id: str
    policy_id: str
    evaluation_date: date
    window_days: int
    support_priority_index: Decimal
    priority_tier: str
    confidence_score: Decimal
    data_quality: str
    primary_driver: Optional[str] = None
    summary_text: str
    status: str
    algorithm_version: str
    policy_version: str
    calculated_at: datetime
    contributions: List[RiskSignalContributionSchema] = []

    class Config:
        from_attributes = True


class CohortPriorityItemResponse(BaseModel):
    """Item row for the advisor triage roster."""

    student_id: str
    student_name: str
    roll_number: str
    program_code: Optional[str] = None
    section_name: Optional[str] = None
    support_priority_index: Decimal
    priority_tier: str
    primary_driver: Optional[str] = None
    confidence_score: Decimal
    data_quality: str
    evaluation_date: date
    calculated_at: datetime


class CohortPrioritiesPageResponse(BaseModel):
    """Paginated advisor support priority roster response."""

    items: List[CohortPriorityItemResponse]
    total: int
    page: int
    limit: int
    pages: int
