"""Database models package."""

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from .audit_log import AuditLog
from .role import Role, Permission, UserRole, RolePermission
from .user import User
from .refresh_token import RefreshToken
from .academic import (
    Institution,
    Department,
    Program,
    Batch,
    Section,
    AcademicTerm,
    Course,
    StudentProfile,
    FacultyProfile,
    Enrollment,
    FacultyCourseAssignment,
    AttendanceRecord,
    Assignment,
    AssignmentSubmission,
    Assessment,
    AssessmentResult,
)
from .pulsewatch import (
    StudentBehaviorBaseline,
    BehaviorEvent,
    BehaviorSignalEvidence,
)
from .pulserisk import (
    RiskPolicy,
    StudentRiskSnapshot,
    RiskSignalContribution,
)
from .knowledge import (
    KnowledgeDocument,
    DocumentVersionSchedule,
    KnowledgeChunk,
    VectorType,
)
from .ai_log import AIInteractionLog
from .pulserecord import (
    LeaveRequest,
    LeaveAttachment,
    Complaint,
    ComplaintEvidence,
    ComplaintAppeal,
)
from .pulsecase import (
    SupportCase,
    CaseNote,
    CaseIntervention,
    CaseFollowUp,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "AuditLog",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "RefreshToken",
    "Institution",
    "Department",
    "Program",
    "Batch",
    "Section",
    "AcademicTerm",
    "Course",
    "StudentProfile",
    "FacultyProfile",
    "Enrollment",
    "FacultyCourseAssignment",
    "AttendanceRecord",
    "Assignment",
    "AssignmentSubmission",
    "Assessment",
    "AssessmentResult",
    "StudentBehaviorBaseline",
    "BehaviorEvent",
    "BehaviorSignalEvidence",
    "RiskPolicy",
    "StudentRiskSnapshot",
    "RiskSignalContribution",
    "KnowledgeDocument",
    "DocumentVersionSchedule",
    "KnowledgeChunk",
    "VectorType",
    "AIInteractionLog",
    "LeaveRequest",
    "LeaveAttachment",
    "Complaint",
    "ComplaintEvidence",
    "ComplaintAppeal",
    "SupportCase",
    "CaseNote",
    "CaseIntervention",
    "CaseFollowUp",
]

