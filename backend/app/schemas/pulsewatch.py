"""Pydantic schemas for the PulseWatch behavioral monitoring subsystem."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


DataQualityStatus = Literal["NO_DATA", "INSUFFICIENT_DATA", "VALID_DATA"]
BehaviorSeverity = Literal["NORMAL", "MILD_CHANGE", "MODERATE_CHANGE", "SIGNIFICANT_CHANGE"]
SignalType = Literal[
    "ATTENDANCE_CHANGE",
    "SUBMISSION_LATENESS",
    "MISSED_ASSIGNMENT",
    "ASSESSMENT_PERFORMANCE",
]
BehaviorEventType = Literal[
    "ACADEMIC_ENGAGEMENT_CHANGE",
    "ATTENDANCE_DROP",
    "COURSEWORK_IRREGULARITY",
    "ASSESSMENT_DECLINE",
    "MULTI_SIGNAL_CHANGE",
]


class SignalEvidenceSchema(BaseModel):
    """Granular evidence metric supporting an engagement signal."""

    signal_type: str
    severity: str
    metric_name: str
    current_value: Optional[Decimal] = None
    baseline_value: Optional[Decimal] = None
    delta_value: Optional[Decimal] = None
    evidence_payload: Optional[Dict[str, Any]] = None


class CohortContextSchema(BaseModel):
    """Secondary cohort-level context. Never replaces or overrides the personal baseline."""

    program_code: Optional[str] = None
    batch_name: Optional[str] = None
    section_name: Optional[str] = None
    cohort_attendance_rate: Optional[Decimal] = None
    cohort_submission_rate: Optional[Decimal] = None
    cohort_assessment_average: Optional[Decimal] = None
    context_note: str = (
        "Cohort metrics provide population context only and do not modify the personal baseline or event severity."
    )


class AcademicContextSchema(BaseModel):
    """Available academic environment context for the observation window."""

    term_name: Optional[str] = None
    upcoming_assessments_count: int = 0
    assignment_deadline_clustering: bool = False
    untracked_contexts: List[str] = [
        "LEAVE_RECORDS_DEFERRED",
        "COMPLAINTS_DEFERRED",
        "SUPPORT_CASES_DEFERRED",
    ]


class ExplainabilitySchema(BaseModel):
    """Transparent, deterministic explanation for the observed status."""

    what_changed: str
    compared_with: str
    observation_period: str
    data_sufficiency: str
    disclaimer: str = (
        "This indicator reflects recorded academic engagement compared to your personal baseline. "
        "CampusPulse does not infer personal, medical, or psychological causes."
    )


class PulseWatchSummaryResponse(BaseModel):
    """Live computed academic behavioral engagement summary for a student."""

    student_id: str
    observation_window_days: int
    window_start_date: date
    window_end_date: date
    baseline_start_date: date
    baseline_end_date: date
    data_quality: str
    overall_status: str
    summary_text: str
    signals: List[SignalEvidenceSchema] = []
    cohort_context: CohortContextSchema
    academic_context: AcademicContextSchema
    explainability: ExplainabilitySchema
    algorithm_version: str = "pulsewatch-v1.0"
    calculated_at: datetime


class BehaviorEventResponse(BaseModel):
    """Historical persisted behavioral event record with associated evidence."""

    id: str
    student_id: str
    event_type: str
    severity: str
    observation_window_days: int
    window_start_date: date
    window_end_date: date
    summary_text: str
    status: str
    algorithm_version: str
    detected_at: datetime
    evidence: List[SignalEvidenceSchema] = []


class StudentBehaviorBaselineResponse(BaseModel):
    """Persisted behavioral baseline record for a specific academic metric."""

    metric_type: str
    baseline_value: Optional[Decimal] = None
    observation_count: int
    data_quality: str
    window_days: int
    algorithm_version: str
    calculated_at: datetime
