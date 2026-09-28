"""Pydantic v2 schemas for PulseCase subsystem."""

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Enum Types
# ============================================================================

CaseType = Literal[
    "ACADEMIC_SUPPORT",
    "ATTENDANCE_INTERVENTION",
    "EARLY_WARNING_TRIAGE",
    "WELLBEING_REFERRAL",
]

CaseStatus = Literal[
    "OPEN",
    "IN_PROGRESS",
    "WAITING_FOR_STUDENT",
    "FOLLOW_UP_SCHEDULED",
    "RESOLVED",
    "CLOSED",
]

CasePriority = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "URGENT",
]

CaseTriggerSource = Literal[
    "PULSERISK_SPI",
    "PULSEWATCH_SHIFT",
    "FACULTY_REFERRAL",
    "STUDENT_REQUEST",
    "MANUAL_ADVISOR",
]

ResolutionOutcome = Literal[
    "IMPROVED_ENGAGEMENT",
    "ACADEMIC_PLAN_ESTABLISHED",
    "REFERRED_TO_EXTERNAL_RESOURCE",
    "STUDENT_UNRESPONSIVE",
    "NO_FURTHER_ACTION",
]

NoteType = Literal[
    "ADVISING_NOTE",
    "STUDENT_INTERACTION",
    "COUNSELOR_CONFIDENTIAL",
    "ACTION_PLAN",
    "SYSTEM_EVENT",
]

ConfidentialityLevel = Literal[
    "STANDARD",
    "RESTRICTED_ADVISING",
    "COUNSELOR_CONFIDENTIAL",
]

InterventionType = Literal[
    "ONE_ON_ONE_ADVISING",
    "PEER_TUTORING_REFERRAL",
    "ACADEMIC_SKILLS_WORKSHOP",
    "ATTENDANCE_CONTRACT",
    "WELLBEING_SUPPORT",
    "COURSE_LOAD_ADJUSTMENT",
]

InterventionStatus = Literal[
    "PLANNED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
]

FollowUpType = Literal[
    "CHECK_IN_MEETING",
    "ACADEMIC_PROGRESS_REVIEW",
    "ATTENDANCE_CHECK",
    "WELLBEING_FOLLOW_UP",
]

FollowUpStatus = Literal[
    "SCHEDULED",
    "COMPLETED",
    "MISSED",
    "RESCHEDULED",
    "CANCELLED",
]


# ============================================================================
# Request Schemas
# ============================================================================

class CaseCreateRequest(BaseModel):
    """Direct case opening by Advisor or Admin."""

    student_id: str
    case_type: CaseType
    priority: CasePriority = "MEDIUM"
    trigger_source: CaseTriggerSource = "MANUAL_ADVISOR"
    reason: str = Field(..., min_length=5)
    evidence_references: Optional[Dict[str, Any]] = None
    assigned_staff_id: Optional[str] = None


class FacultyReferralCreateRequest(BaseModel):
    """Faculty advising referral submission."""

    student_id: str
    reason: str = Field(..., min_length=5)
    course_id: Optional[str] = None
    priority: CasePriority = "MEDIUM"


class CaseAssignRequest(BaseModel):
    """Assign or reassign staff handler."""

    assigned_staff_id: str


class CaseStatusUpdateRequest(BaseModel):
    """Transition case lifecycle status."""

    status: CaseStatus
    notes: Optional[str] = None


class CaseResolveRequest(BaseModel):
    """Resolve case with recorded outcome."""

    resolution_outcome: ResolutionOutcome
    resolution_summary: str = Field(..., min_length=5)


class CaseCloseRequest(BaseModel):
    """Formally close resolved case."""

    closing_notes: Optional[str] = None


class CaseNoteCreateRequest(BaseModel):
    """Record a note on an active case."""

    note_type: NoteType = "ADVISING_NOTE"
    confidentiality_level: ConfidentialityLevel = "STANDARD"
    content: str = Field(..., min_length=1)


class CaseInterventionCreateRequest(BaseModel):
    """Add planned intervention action item."""

    intervention_type: InterventionType
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=5)
    assigned_to_user_id: Optional[str] = None
    target_completion_date: Optional[date] = None


class CaseInterventionUpdateRequest(BaseModel):
    """Update status of an intervention item."""

    status: InterventionStatus
    outcome_notes: Optional[str] = None


class CaseFollowUpCreateRequest(BaseModel):
    """Schedule follow-up evaluation meeting."""

    scheduled_date: date
    scheduled_time: Optional[str] = None
    follow_up_type: FollowUpType = "CHECK_IN_MEETING"
    assigned_staff_id: Optional[str] = None
    notes: Optional[str] = None


class CaseFollowUpUpdateRequest(BaseModel):
    """Record follow-up session completion or rescheduling."""

    status: FollowUpStatus
    notes: Optional[str] = None


# ============================================================================
# Response Schemas
# ============================================================================

class CaseNoteResponse(BaseModel):
    """Response representation of a case note."""

    id: str
    case_id: str
    author_user_id: str
    author_name: Optional[str] = None
    note_type: str
    confidentiality_level: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseInterventionResponse(BaseModel):
    """Response representation of a case intervention."""

    id: str
    case_id: str
    intervention_type: str
    title: str
    description: str
    assigned_to_user_id: Optional[str] = None
    target_completion_date: Optional[date] = None
    status: str
    completed_at: Optional[datetime] = None
    outcome_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseFollowUpResponse(BaseModel):
    """Response representation of a case follow-up session."""

    id: str
    case_id: str
    scheduled_date: date
    scheduled_time: Optional[str] = None
    follow_up_type: str
    assigned_staff_id: str
    assigned_staff_name: Optional[str] = None
    status: str
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupportCaseResponse(BaseModel):
    """Summary projection of an intervention case."""

    id: str
    institution_id: str
    case_number: str
    student_id: str
    student_name: Optional[str] = None
    student_enrollment_number: Optional[str] = None
    case_type: str
    status: str
    priority: str
    trigger_source: str
    reason: str
    evidence_references: Optional[Dict[str, Any]] = None
    assigned_staff_id: Optional[str] = None
    assigned_advisor_id: Optional[str] = None
    assigned_staff_name: Optional[str] = None
    assigned_staff_role: Optional[str] = None
    referred_by_user_id: Optional[str] = None
    referred_by_name: Optional[str] = None
    resolution_outcome: Optional[str] = None
    resolution_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_by_user_id: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    interventions_count: int = 0
    follow_ups_count: int = 0
    notes_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SupportCaseDetailResponse(SupportCaseResponse):
    """Comprehensive case detail with notes, interventions, and follow-ups."""

    notes: List[CaseNoteResponse] = []
    interventions: List[CaseInterventionResponse] = []
    follow_ups: List[CaseFollowUpResponse] = []


class FacultyReferralReceiptResponse(BaseModel):
    """Sanitized referral tracking receipt for teaching faculty."""

    id: str
    case_number: str
    student_id: str
    student_name: Optional[str] = None
    case_type: str
    status: str
    priority: str
    created_at: datetime
    closed_at: Optional[datetime] = None
    resolution_outcome: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StudentSupportItemResponse(BaseModel):
    """Action plan item visible to enrolled student."""

    id: str
    title: str
    description: str
    intervention_type: str
    target_date: Optional[date] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class StudentUpcomingFollowUpResponse(BaseModel):
    """Follow-up appointment visible to enrolled student."""

    id: str
    scheduled_date: date
    scheduled_time: Optional[str] = None
    follow_up_type: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class StudentSupportSummaryResponse(BaseModel):
    """Student self-service overview of support action items."""

    active_cases_count: int
    assigned_advisor_name: Optional[str] = None
    support_action_items: List[StudentSupportItemResponse] = []
    upcoming_follow_ups: List[StudentUpcomingFollowUpResponse] = []
