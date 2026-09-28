"""Pydantic schemas for Phase 6 PulseRecord subsystem.

Covers:
- Leave requests, review, cancellation, attachments.
- Complaints, review notes, info requests, adjudication, appeals, evidence.
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# =============================================================================
# 1. Leave Schemas
# =============================================================================

class LeaveTypeEnum(str, Enum):
    MEDICAL = "MEDICAL"
    ACADEMIC_DUTY = "ACADEMIC_DUTY"
    PERSONAL = "PERSONAL"
    EMERGENCY = "EMERGENCY"
    BEREAVEMENT = "BEREAVEMENT"


class LeaveStatusEnum(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveRequestCreate(BaseModel):
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=5, max_length=2000)


class LeaveReviewRequest(BaseModel):
    status: Literal[LeaveStatusEnum.APPROVED, LeaveStatusEnum.REJECTED]
    reviewer_notes: Optional[str] = Field(None, max_length=2000)


class LeaveCancelRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=3, max_length=500)


class LeaveAttachmentResponse(BaseModel):
    id: str
    leave_request_id: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveRequestResponse(BaseModel):
    id: str
    institution_id: str
    student_id: str
    student_name: Optional[str] = None
    enrollment_number: Optional[str] = None
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    days_count: int
    reason: str
    status: LeaveStatusEnum
    reviewed_by_user_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaveRequestDetailResponse(LeaveRequestResponse):
    attachments: List[LeaveAttachmentResponse] = []


# =============================================================================
# 2. Complaint Schemas
# =============================================================================

class ComplaintCategoryEnum(str, Enum):
    ACADEMIC_INTEGRITY = "ACADEMIC_INTEGRITY"
    FACILITY_HARASSMENT = "FACILITY_HARASSMENT"
    DISCRIMINATION = "DISCRIMINATION"
    GRADING_DISPUTE = "GRADING_DISPUTE"
    SAFETY_CONCERN = "SAFETY_CONCERN"
    OTHER = "OTHER"


class ComplaintTargetTypeEnum(str, Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    DEPARTMENT = "DEPARTMENT"
    FACILITY = "FACILITY"
    OTHER = "OTHER"


class ComplaintStatusEnum(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    VERIFIED = "VERIFIED"
    DISMISSED = "DISMISSED"
    OTHER_AUTHORIZED_OUTCOME = "OTHER_AUTHORIZED_OUTCOME"
    APPEALED = "APPEALED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ComplaintCreate(BaseModel):
    category: ComplaintCategoryEnum
    target_type: ComplaintTargetTypeEnum
    target_student_id: Optional[str] = None
    target_department_id: Optional[str] = None
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=5000)
    is_anonymous: bool = False


class ComplaintAssignRequest(BaseModel):
    reviewer_user_id: str


class ComplaintRequestInfo(BaseModel):
    details: str = Field(..., min_length=5, max_length=2000)


class ComplaintProvideInfo(BaseModel):
    response: str = Field(..., min_length=5, max_length=2000)


class ComplaintAdjudicateRequest(BaseModel):
    status: Literal[
        ComplaintStatusEnum.VERIFIED,
        ComplaintStatusEnum.DISMISSED,
        ComplaintStatusEnum.OTHER_AUTHORIZED_OUTCOME,
    ]
    adjudication_outcome: str = Field(..., min_length=3, max_length=50)
    adjudication_summary: str = Field(..., min_length=5, max_length=5000)
    internal_reviewer_notes: Optional[str] = Field(None, max_length=5000)


class ComplaintAppealCreate(BaseModel):
    reason: str = Field(..., min_length=10, max_length=5000)


class ComplaintAppealResolve(BaseModel):
    status: Literal["UPHELD", "OVERTURNED", "MODIFIED", "DISMISSED"]
    disposition_summary: str = Field(..., min_length=5, max_length=5000)
    reviewer_notes: Optional[str] = Field(None, max_length=5000)


class ComplaintEvidenceResponse(BaseModel):
    id: str
    complaint_id: str
    uploader_user_id: Optional[str] = None
    uploader_role: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    description: Optional[str] = None
    is_confidential: bool
    is_sealed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComplaintAppealResponse(BaseModel):
    id: str
    complaint_id: str
    appellant_user_id: Optional[str] = None
    appeal_number: int
    reason: str
    status: str
    reviewer_user_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    disposition_summary: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintResponse(BaseModel):
    id: str
    institution_id: str
    complaint_code: str
    complainant_user_id: Optional[str] = None
    complainant_role: Optional[str] = None
    is_anonymous: bool
    category: ComplaintCategoryEnum
    target_type: ComplaintTargetTypeEnum
    target_student_id: Optional[str] = None
    target_department_id: Optional[str] = None
    title: str
    description: str
    status: ComplaintStatusEnum
    assigned_reviewer_id: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    adjudication_outcome: Optional[str] = None
    adjudication_summary: Optional[str] = None
    internal_reviewer_notes: Optional[str] = None
    info_request_details: Optional[str] = None
    info_response_details: Optional[str] = None
    evidence_count: int = 0
    appeal_count: int = 0
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintDetailResponse(ComplaintResponse):
    evidence: List[ComplaintEvidenceResponse] = []
    appeals: List[ComplaintAppealResponse] = []
