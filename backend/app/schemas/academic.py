"""Pydantic v2 schemas for Academic Domain models, requests, and summaries."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# Base Models
# -----------------------------------------------------------------------------

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Institutional Hierarchy
# -----------------------------------------------------------------------------

class InstitutionResponse(BaseSchema):
    id: str
    name: str
    code: str
    address: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    created_at: datetime


class DepartmentResponse(BaseSchema):
    id: str
    institution_id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime


class ProgramResponse(BaseSchema):
    id: str
    department_id: str
    name: str
    code: str
    degree_level: str
    duration_years: int
    is_active: bool
    created_at: datetime


class BatchResponse(BaseSchema):
    id: str
    program_id: str
    name: str
    start_year: int
    end_year: int
    current_semester: int
    is_active: bool
    created_at: datetime


class SectionResponse(BaseSchema):
    id: str
    batch_id: str
    name: str
    capacity: int
    is_active: bool
    created_at: datetime


class AcademicTermResponse(BaseSchema):
    id: str
    institution_id: str
    name: str
    term_type: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime


class CourseResponse(BaseSchema):
    id: str
    institution_id: str
    department_id: str
    code: str
    title: str
    credits: int
    course_type: str
    syllabus_summary: Optional[str] = None
    is_active: bool
    created_at: datetime


# -----------------------------------------------------------------------------
# Profiles
# -----------------------------------------------------------------------------

class StudentProfileCreate(BaseModel):
    user_id: str
    enrollment_number: str
    program_id: str
    batch_id: str
    section_id: Optional[str] = None
    current_semester: int = 1
    admission_date: Optional[date] = None
    academic_status: str = "ENROLLED"


class StudentProfileResponse(BaseSchema):
    id: str
    user_id: str
    enrollment_number: str
    program_id: str
    batch_id: str
    section_id: Optional[str] = None
    current_semester: int
    admission_date: date
    academic_status: str
    created_at: datetime

    # Optional nested details
    program_name: Optional[str] = None
    batch_name: Optional[str] = None
    section_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None


class FacultyProfileCreate(BaseModel):
    user_id: str
    employee_id: str
    department_id: str
    designation: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    joining_date: Optional[date] = None
    is_active: bool = True


class FacultyProfileResponse(BaseSchema):
    id: str
    user_id: str
    employee_id: str
    department_id: str
    designation: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    joining_date: date
    is_active: bool
    created_at: datetime

    # Optional nested details
    department_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None


# -----------------------------------------------------------------------------
# Enrollments & Teaching Assignments
# -----------------------------------------------------------------------------

class EnrollmentCreate(BaseModel):
    student_id: str
    course_id: str
    term_id: str
    section_id: Optional[str] = None
    enrollment_date: Optional[date] = None
    status: str = "ENROLLED"


class EnrollmentResponse(BaseSchema):
    id: str
    student_id: str
    course_id: str
    term_id: str
    section_id: Optional[str] = None
    enrollment_date: date
    status: str
    created_at: datetime

    # Nested fields
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    course_credits: Optional[int] = None
    term_name: Optional[str] = None


class FacultyCourseAssignmentResponse(BaseSchema):
    id: str
    faculty_id: str
    course_id: str
    term_id: str
    section_id: Optional[str] = None
    role: str
    created_at: datetime

    course_code: Optional[str] = None
    course_title: Optional[str] = None
    term_name: Optional[str] = None
    section_name: Optional[str] = None


# -----------------------------------------------------------------------------
# Attendance
# -----------------------------------------------------------------------------

class AttendanceRecordCreate(BaseModel):
    student_id: str
    course_id: str
    term_id: str
    session_date: date
    session_slot: str
    status: Literal["PRESENT", "ABSENT", "LATE", "EXCUSED"]
    source: Literal["MANUAL", "IMPORT", "LMS", "BIOMETRIC", "API"] = "MANUAL"
    remarks: Optional[str] = None


class AttendanceRecordResponse(BaseSchema):
    id: str
    student_id: str
    course_id: str
    term_id: str
    session_date: date
    session_slot: str
    status: str
    source: str
    recorded_by_faculty_id: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime

    course_code: Optional[str] = None
    course_title: Optional[str] = None


class AttendanceSummaryResponse(BaseModel):
    total_sessions: int
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    attendance_percentage: float


# -----------------------------------------------------------------------------
# Coursework / Assignments
# -----------------------------------------------------------------------------

class AssignmentCreate(BaseModel):
    course_id: str
    term_id: str
    section_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_marks: Decimal = Field(..., gt=0)
    weightage_percentage: Decimal = Field(Decimal("10.00"), ge=0, le=100)
    release_date: datetime
    due_date: datetime
    cutoff_date: Optional[datetime] = None
    allow_late_submission: bool = True


class AssignmentResponse(BaseSchema):
    id: str
    course_id: str
    term_id: str
    section_id: Optional[str] = None
    created_by_faculty_id: str
    title: str
    description: Optional[str] = None
    max_marks: Decimal
    weightage_percentage: Decimal
    release_date: datetime
    due_date: datetime
    cutoff_date: Optional[datetime] = None
    allow_late_submission: bool
    created_at: datetime

    course_code: Optional[str] = None
    course_title: Optional[str] = None


class AssignmentSubmissionCreate(BaseModel):
    submission_content: Optional[str] = None
    attachment_path: Optional[str] = None


class SubmissionGradeRequest(BaseModel):
    marks_obtained: Decimal = Field(..., ge=0)
    feedback: Optional[str] = None


class AssignmentSubmissionResponse(BaseSchema):
    id: str
    assignment_id: str
    student_id: str
    attempt_number: int
    submission_content: Optional[str] = None
    attachment_path: Optional[str] = None
    submitted_at: datetime
    status: str
    marks_obtained: Optional[Decimal] = None
    feedback: Optional[str] = None
    evaluated_by_faculty_id: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    created_at: datetime

    assignment_title: Optional[str] = None
    max_marks: Optional[Decimal] = None


# -----------------------------------------------------------------------------
# Assessments
# -----------------------------------------------------------------------------

class AssessmentCreate(BaseModel):
    course_id: str
    term_id: str
    section_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    assessment_type: str = Field("MIDTERM")  # QUIZ, MIDTERM, FINAL, PRACTICAL, PROJECT
    max_marks: Decimal = Field(..., gt=0)
    weightage_percentage: Decimal = Field(Decimal("20.00"), ge=0, le=100)
    assessment_date: date


class AssessmentResponse(BaseSchema):
    id: str
    course_id: str
    term_id: str
    section_id: Optional[str] = None
    created_by_faculty_id: str
    title: str
    assessment_type: str
    max_marks: Decimal
    weightage_percentage: Decimal
    assessment_date: date
    created_at: datetime

    course_code: Optional[str] = None
    course_title: Optional[str] = None


class AssessmentResultCreate(BaseModel):
    student_id: str
    marks_obtained: Optional[Decimal] = None
    is_absent: bool = False
    remarks: Optional[str] = None


class AssessmentResultResponse(BaseSchema):
    id: str
    assessment_id: str
    student_id: str
    marks_obtained: Optional[Decimal] = None
    is_absent: bool
    remarks: Optional[str] = None
    evaluated_by_faculty_id: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    created_at: datetime

    assessment_title: Optional[str] = None
    assessment_type: Optional[str] = None
    max_marks: Optional[Decimal] = None
    student_enrollment_number: Optional[str] = None
    student_name: Optional[str] = None
