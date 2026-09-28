"""Academic domain database models for CampusPulse.

Includes institutions, departments, programs, batches, sections, academic terms,
courses, student profiles, faculty profiles, enrollments, teaching assignments,
attendance records, assignments, submissions, assessments, and assessment results.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
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


class Institution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Educational institution entity."""

    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    departments: Mapped[List["Department"]] = relationship("Department", back_populates="institution")
    academic_terms: Mapped[List["AcademicTerm"]] = relationship("AcademicTerm", back_populates="institution")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="institution")


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic department within an institution."""

    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_departments_institution_code"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="departments")
    programs: Mapped[List["Program"]] = relationship("Program", back_populates="department")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="department")
    faculty_profiles: Mapped[List["FacultyProfile"]] = relationship("FacultyProfile", back_populates="department")


class Program(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Degree or educational program offered by a department."""

    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint("department_id", "code", name="uq_programs_department_code"),
    )

    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(50), default="UG", nullable=False)  # UG, PG, DIPLOMA, DOCTORAL
    duration_years: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="program")
    student_profiles: Mapped[List["StudentProfile"]] = relationship("StudentProfile", back_populates="program")


class Batch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cohort / intake batch of students for a program."""

    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint("program_id", "name", name="uq_batches_program_name"),
    )

    program_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "2024-2028"
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    current_semester: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    program: Mapped["Program"] = relationship("Program", back_populates="batches")
    sections: Mapped[List["Section"]] = relationship("Section", back_populates="batch")
    student_profiles: Mapped[List["StudentProfile"]] = relationship("StudentProfile", back_populates="batch")


class Section(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Subdivision of a batch into classes/sections."""

    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("batch_id", "name", name="uq_sections_batch_name"),
    )

    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "A", "B"
    capacity: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="sections")
    student_profiles: Mapped[List["StudentProfile"]] = relationship("StudentProfile", back_populates="section")


class AcademicTerm(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic semester, trimester, or annual term."""

    __tablename__ = "academic_terms"
    __table_args__ = (
        UniqueConstraint("institution_id", "name", name="uq_academic_terms_institution_name"),
        CheckConstraint("start_date < end_date", name="chk_academic_terms_dates"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Fall 2026"
    term_type: Mapped[str] = mapped_column(String(50), default="SEMESTER", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="academic_terms")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="term")
    faculty_assignments: Mapped[List["FacultyCourseAssignment"]] = relationship(
        "FacultyCourseAssignment", back_populates="term"
    )
    assignments: Mapped[List["Assignment"]] = relationship("Assignment", back_populates="term")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="term")


class Course(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Course offering within a department and institution."""

    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_courses_institution_code"),
        CheckConstraint("credits >= 0", name="chk_courses_credits"),
    )

    institution_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    course_type: Mapped[str] = mapped_column(String(50), default="THEORY", nullable=False)
    syllabus_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="courses")
    department: Mapped["Department"] = relationship("Department", back_populates="courses")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="course")
    faculty_assignments: Mapped[List["FacultyCourseAssignment"]] = relationship(
        "FacultyCourseAssignment", back_populates="course"
    )
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="course")
    assignments: Mapped[List["Assignment"]] = relationship("Assignment", back_populates="course")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="course")


class StudentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic student profile linked 1:1 to User identity.
    
    Contains strictly academic and cohort metadata.
    Zero authentication credentials, password hashes, or token secrets.
    """

    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("enrollment_number", name="uq_student_profiles_enrollment_number"),
        UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
        Index("ix_student_profiles_enrollment_number", "enrollment_number", unique=True),
        Index("ix_student_profiles_user_id", "user_id", unique=True),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    enrollment_number: Mapped[str] = mapped_column(String(100), nullable=False)
    program_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    current_semester: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)
    academic_status: Mapped[str] = mapped_column(
        String(50), default="ENROLLED", nullable=False
    )  # ENROLLED, SUSPENDED, LEAVE_OF_ABSENCE, GRADUATED, WITHDRAWN

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    program: Mapped["Program"] = relationship("Program", back_populates="student_profiles")
    batch: Mapped["Batch"] = relationship("Batch", back_populates="student_profiles")
    section: Mapped[Optional["Section"]] = relationship("Section", back_populates="student_profiles")
    enrollments: Mapped[List["Enrollment"]] = relationship("Enrollment", back_populates="student")
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship("AttendanceRecord", back_populates="student")
    assignment_submissions: Mapped[List["AssignmentSubmission"]] = relationship(
        "AssignmentSubmission", back_populates="student"
    )
    assessment_results: Mapped[List["AssessmentResult"]] = relationship("AssessmentResult", back_populates="student")


class FacultyProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic faculty profile linked 1:1 to User identity.
    
    Contains institutional teaching and departmental metadata.
    Zero authentication credentials or secrets.
    """

    __tablename__ = "faculty_profiles"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_faculty_profiles_employee_id"),
        UniqueConstraint("user_id", name="uq_faculty_profiles_user_id"),
        Index("ix_faculty_profiles_employee_id", "employee_id", unique=True),
        Index("ix_faculty_profiles_user_id", "user_id", unique=True),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    employee_id: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    qualification: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="faculty_profile")
    department: Mapped["Department"] = relationship("Department", back_populates="faculty_profiles")
    assignments: Mapped[List["FacultyCourseAssignment"]] = relationship(
        "FacultyCourseAssignment", back_populates="faculty"
    )


class Enrollment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Student course enrollment per academic term."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "term_id", name="uq_enrollments_student_course_term"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    term_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_terms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="ENROLLED", nullable=False
    )  # ENROLLED, DROPPED, COMPLETED, AUDITING, WITHDRAWN

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    term: Mapped["AcademicTerm"] = relationship("AcademicTerm", back_populates="enrollments")
    section: Mapped[Optional["Section"]] = relationship("Section")


class FacultyCourseAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Teaching assignment mapping a faculty member to a course/section and term."""

    __tablename__ = "faculty_course_assignments"
    __table_args__ = (
        Index(
            "uq_faculty_assignment_course_wide",
            "faculty_id",
            "course_id",
            "term_id",
            unique=True,
            postgresql_where=Column("section_id").is_(None),
        ),
        Index(
            "uq_faculty_assignment_section",
            "faculty_id",
            "course_id",
            "term_id",
            "section_id",
            unique=True,
            postgresql_where=Column("section_id").is_not(None),
        ),
    )

    faculty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("faculty_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    term_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_terms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    role: Mapped[str] = mapped_column(
        String(50), default="PRIMARY_INSTRUCTOR", nullable=False
    )  # PRIMARY_INSTRUCTOR, CO_INSTRUCTOR, TEACHING_ASSISTANT, LAB_INSTRUCTOR

    # Relationships
    faculty: Mapped["FacultyProfile"] = relationship("FacultyProfile", back_populates="assignments")
    course: Mapped["Course"] = relationship("Course", back_populates="faculty_assignments")
    term: Mapped["AcademicTerm"] = relationship("AcademicTerm", back_populates="faculty_assignments")
    section: Mapped[Optional["Section"]] = relationship("Section")


class AttendanceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular per-session attendance event log.
    
    Raw historical provenance is preserved for future behavioral analysis.
    Percentages and aggregate rates are derived on-demand.
    """

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "session_date", "session_slot",
            name="uq_attendance_student_course_date_slot"
        ),
        Index(
            "ix_attendance_records_student_id_session_date",
            "student_id",
            "session_date",
        ),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    term_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_terms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    session_slot: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "SLOT_1", "09:00-10:00"
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # PRESENT, ABSENT, LATE, EXCUSED
    source: Mapped[str] = mapped_column(String(50), default="MANUAL", nullable=False)  # MANUAL, IMPORT, LMS, BIOMETRIC, API
    recorded_by_faculty_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("faculty_profiles.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="attendance_records")
    course: Mapped["Course"] = relationship("Course", back_populates="attendance_records")
    term: Mapped["AcademicTerm"] = relationship("AcademicTerm")
    recorded_by: Mapped[Optional["FacultyProfile"]] = relationship("FacultyProfile")


class Assignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Coursework assignment with deadlines, weightage, and submission policies."""

    __tablename__ = "assignments"
    __table_args__ = (
        UniqueConstraint("course_id", "term_id", "title", name="uq_assignments_course_term_title"),
        CheckConstraint("release_date <= due_date", name="chk_assignments_release_due"),
        CheckConstraint("cutoff_date IS NULL OR due_date <= cutoff_date", name="chk_assignments_due_cutoff"),
        CheckConstraint("max_marks > 0", name="chk_assignments_max_marks"),
        CheckConstraint("weightage_percentage >= 0 AND weightage_percentage <= 100", name="chk_assignments_weightage"),
    )

    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    term_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_terms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_by_faculty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("faculty_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    weightage_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.00"), nullable=False)
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cutoff_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    allow_late_submission: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="assignments")
    term: Mapped["AcademicTerm"] = relationship("AcademicTerm", back_populates="assignments")
    section: Mapped[Optional["Section"]] = relationship("Section")
    created_by: Mapped["FacultyProfile"] = relationship("FacultyProfile")
    submissions: Mapped[List["AssignmentSubmission"]] = relationship("AssignmentSubmission", back_populates="assignment")


class AssignmentSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Student assignment submission attempt with deterministic lateness tracking."""

    __tablename__ = "assignment_submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", "attempt_number", name="uq_submissions_assignment_student_attempt"),
        CheckConstraint("attempt_number >= 1", name="chk_submissions_attempt_number"),
        CheckConstraint("marks_obtained IS NULL OR marks_obtained >= 0", name="chk_submissions_marks_obtained"),
        Index(
            "ix_assignment_submissions_student_id_submitted_at",
            "student_id",
            "submitted_at",
        ),
    )

    assignment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assignments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    submission_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="SUBMITTED", nullable=False
    )  # DRAFT, SUBMITTED, LATE, EVALUATED, RESUBMITTED
    marks_obtained: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluated_by_faculty_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("faculty_profiles.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="assignment_submissions")
    evaluated_by: Mapped[Optional["FacultyProfile"]] = relationship("FacultyProfile")


class Assessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Formal evaluation event: quiz, midterm, final examination, or practical."""

    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint("course_id", "term_id", "title", name="uq_assessments_course_term_title"),
        CheckConstraint("max_marks > 0", name="chk_assessments_max_marks"),
        CheckConstraint("weightage_percentage >= 0 AND weightage_percentage <= 100", name="chk_assessments_weightage"),
    )

    course_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    term_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academic_terms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    section_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sections.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_by_faculty_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("faculty_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # QUIZ, MIDTERM, FINAL, PRACTICAL, PROJECT
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    weightage_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("20.00"), nullable=False)
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="assessments")
    term: Mapped["AcademicTerm"] = relationship("AcademicTerm", back_populates="assessments")
    section: Mapped[Optional["Section"]] = relationship("Section")
    created_by: Mapped["FacultyProfile"] = relationship("FacultyProfile")
    results: Mapped[List["AssessmentResult"]] = relationship("AssessmentResult", back_populates="assessment")


class AssessmentResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Student assessment score and evaluation outcome.
    
    Database enforces marks_obtained >= 0.
    Service layer enforces marks_obtained <= assessment.max_marks.
    """

    __tablename__ = "assessment_results"
    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", name="uq_assessment_results_assessment_student"),
        CheckConstraint("marks_obtained IS NULL OR marks_obtained >= 0", name="chk_assessment_results_marks_obtained"),
    )

    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    marks_obtained: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evaluated_by_faculty_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("faculty_profiles.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="results")
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="assessment_results")
    evaluated_by: Mapped[Optional["FacultyProfile"]] = relationship("FacultyProfile")
