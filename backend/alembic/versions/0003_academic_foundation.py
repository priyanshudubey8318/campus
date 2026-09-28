"""0003 Academic Domain, Profiles & Academic Data Foundation

Revision ID: 0003_academic_foundation
Revises: 0002_identity_and_access
Create Date: 2026-09-18 15:40:00.000000

"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_academic_foundation"
down_revision: Union[str, None] = "0002_identity_and_access"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    now = datetime.now(timezone.utc)

    # 1. institutions table
    op.create_table(
        "institutions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_institutions_code"), "institutions", ["code"], unique=True)
    op.create_index(op.f("ix_institutions_id"), "institutions", ["id"], unique=False)

    # 2. departments table
    op.create_table(
        "departments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "code", name="uq_departments_institution_code"),
    )
    op.create_index(op.f("ix_departments_id"), "departments", ["id"], unique=False)
    op.create_index(op.f("ix_departments_institution_id"), "departments", ["institution_id"], unique=False)

    # 3. programs table
    op.create_table(
        "programs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("degree_level", sa.String(length=50), nullable=False, server_default="UG"),
        sa.Column("duration_years", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("department_id", "code", name="uq_programs_department_code"),
    )
    op.create_index(op.f("ix_programs_department_id"), "programs", ["department_id"], unique=False)
    op.create_index(op.f("ix_programs_id"), "programs", ["id"], unique=False)

    # 4. batches table
    op.create_table(
        "batches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("program_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=False),
        sa.Column("end_year", sa.Integer(), nullable=False),
        sa.Column("current_semester", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("program_id", "name", name="uq_batches_program_name"),
    )
    op.create_index(op.f("ix_batches_id"), "batches", ["id"], unique=False)
    op.create_index(op.f("ix_batches_program_id"), "batches", ["program_id"], unique=False)

    # 5. sections table
    op.create_table(
        "sections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("batch_id", "name", name="uq_sections_batch_name"),
    )
    op.create_index(op.f("ix_sections_batch_id"), "sections", ["batch_id"], unique=False)
    op.create_index(op.f("ix_sections_id"), "sections", ["id"], unique=False)

    # 6. academic_terms table
    op.create_table(
        "academic_terms",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("term_type", sa.String(length=50), nullable=False, server_default="SEMESTER"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "name", name="uq_academic_terms_institution_name"),
        sa.CheckConstraint("start_date < end_date", name="chk_academic_terms_dates"),
    )
    op.create_index(op.f("ix_academic_terms_id"), "academic_terms", ["id"], unique=False)
    op.create_index(op.f("ix_academic_terms_institution_id"), "academic_terms", ["institution_id"], unique=False)

    # 7. courses table
    op.create_table(
        "courses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("course_type", sa.String(length=50), nullable=False, server_default="THEORY"),
        sa.Column("syllabus_summary", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "code", name="uq_courses_institution_code"),
        sa.CheckConstraint("credits >= 0", name="chk_courses_credits"),
    )
    op.create_index(op.f("ix_courses_department_id"), "courses", ["department_id"], unique=False)
    op.create_index(op.f("ix_courses_id"), "courses", ["id"], unique=False)
    op.create_index(op.f("ix_courses_institution_id"), "courses", ["institution_id"], unique=False)

    # 8. student_profiles table
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("enrollment_number", sa.String(length=100), nullable=False),
        sa.Column("program_id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=36), nullable=True),
        sa.Column("current_semester", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("admission_date", sa.Date(), nullable=False),
        sa.Column("academic_status", sa.String(length=50), nullable=False, server_default="ENROLLED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enrollment_number", name="uq_student_profiles_enrollment_number"),
        sa.UniqueConstraint("user_id", name="uq_student_profiles_user_id"),
    )
    op.create_index(op.f("ix_student_profiles_batch_id"), "student_profiles", ["batch_id"], unique=False)
    op.create_index(op.f("ix_student_profiles_enrollment_number"), "student_profiles", ["enrollment_number"], unique=True)
    op.create_index(op.f("ix_student_profiles_id"), "student_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_student_profiles_program_id"), "student_profiles", ["program_id"], unique=False)
    op.create_index(op.f("ix_student_profiles_section_id"), "student_profiles", ["section_id"], unique=False)
    op.create_index(op.f("ix_student_profiles_user_id"), "student_profiles", ["user_id"], unique=True)

    # 9. faculty_profiles table
    op.create_table(
        "faculty_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("employee_id", sa.String(length=100), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=False),
        sa.Column("designation", sa.String(length=100), nullable=False),
        sa.Column("qualification", sa.String(length=255), nullable=True),
        sa.Column("specialization", sa.String(length=255), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", name="uq_faculty_profiles_employee_id"),
        sa.UniqueConstraint("user_id", name="uq_faculty_profiles_user_id"),
    )
    op.create_index(op.f("ix_faculty_profiles_department_id"), "faculty_profiles", ["department_id"], unique=False)
    op.create_index(op.f("ix_faculty_profiles_employee_id"), "faculty_profiles", ["employee_id"], unique=True)
    op.create_index(op.f("ix_faculty_profiles_id"), "faculty_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_faculty_profiles_user_id"), "faculty_profiles", ["user_id"], unique=True)

    # 10. enrollments table
    op.create_table(
        "enrollments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("term_id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=36), nullable=True),
        sa.Column("enrollment_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ENROLLED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["term_id"], ["academic_terms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_id", "term_id", name="uq_enrollments_student_course_term"),
    )
    op.create_index(op.f("ix_enrollments_course_id"), "enrollments", ["course_id"], unique=False)
    op.create_index(op.f("ix_enrollments_id"), "enrollments", ["id"], unique=False)
    op.create_index(op.f("ix_enrollments_section_id"), "enrollments", ["section_id"], unique=False)
    op.create_index(op.f("ix_enrollments_student_id"), "enrollments", ["student_id"], unique=False)
    op.create_index(op.f("ix_enrollments_term_id"), "enrollments", ["term_id"], unique=False)

    # 11. faculty_course_assignments table
    op.create_table(
        "faculty_course_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("faculty_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("term_id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=36), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="PRIMARY_INSTRUCTOR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["term_id"], ["academic_terms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_faculty_course_assignments_course_id"), "faculty_course_assignments", ["course_id"], unique=False)
    op.create_index(op.f("ix_faculty_course_assignments_faculty_id"), "faculty_course_assignments", ["faculty_id"], unique=False)
    op.create_index(op.f("ix_faculty_course_assignments_id"), "faculty_course_assignments", ["id"], unique=False)
    op.create_index(op.f("ix_faculty_course_assignments_section_id"), "faculty_course_assignments", ["section_id"], unique=False)
    op.create_index(op.f("ix_faculty_course_assignments_term_id"), "faculty_course_assignments", ["term_id"], unique=False)

    # Partial unique indexes for course-wide vs section-specific assignments
    op.create_index(
        "uq_faculty_assignment_course_wide",
        "faculty_course_assignments",
        ["faculty_id", "course_id", "term_id"],
        unique=True,
        postgresql_where=sa.text("section_id IS NULL"),
    )
    op.create_index(
        "uq_faculty_assignment_section",
        "faculty_course_assignments",
        ["faculty_id", "course_id", "term_id", "section_id"],
        unique=True,
        postgresql_where=sa.text("section_id IS NOT NULL"),
    )

    # 12. attendance_records table
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("term_id", sa.String(length=36), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_slot", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="MANUAL"),
        sa.Column("recorded_by_faculty_id", sa.String(length=36), nullable=True),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recorded_by_faculty_id"], ["faculty_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["term_id"], ["academic_terms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_id", "session_date", "session_slot", name="uq_attendance_student_course_date_slot"),
    )
    op.create_index(op.f("ix_attendance_records_course_id"), "attendance_records", ["course_id"], unique=False)
    op.create_index(op.f("ix_attendance_records_id"), "attendance_records", ["id"], unique=False)
    op.create_index(op.f("ix_attendance_records_recorded_by_faculty_id"), "attendance_records", ["recorded_by_faculty_id"], unique=False)
    op.create_index(op.f("ix_attendance_records_session_date"), "attendance_records", ["session_date"], unique=False)
    op.create_index(op.f("ix_attendance_records_student_id"), "attendance_records", ["student_id"], unique=False)
    op.create_index(op.f("ix_attendance_records_term_id"), "attendance_records", ["term_id"], unique=False)

    # 13. assignments table
    op.create_table(
        "assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("term_id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_faculty_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_marks", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("weightage_percentage", sa.Numeric(precision=5, scale=2), nullable=False, server_default="10.00"),
        sa.Column("release_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cutoff_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("allow_late_submission", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_faculty_id"], ["faculty_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["term_id"], ["academic_terms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "term_id", "title", name="uq_assignments_course_term_title"),
        sa.CheckConstraint("release_date <= due_date", name="chk_assignments_release_due"),
        sa.CheckConstraint("cutoff_date IS NULL OR due_date <= cutoff_date", name="chk_assignments_due_cutoff"),
        sa.CheckConstraint("max_marks > 0", name="chk_assignments_max_marks"),
        sa.CheckConstraint("weightage_percentage >= 0 AND weightage_percentage <= 100", name="chk_assignments_weightage"),
    )
    op.create_index(op.f("ix_assignments_course_id"), "assignments", ["course_id"], unique=False)
    op.create_index(op.f("ix_assignments_created_by_faculty_id"), "assignments", ["created_by_faculty_id"], unique=False)
    op.create_index(op.f("ix_assignments_id"), "assignments", ["id"], unique=False)
    op.create_index(op.f("ix_assignments_section_id"), "assignments", ["section_id"], unique=False)
    op.create_index(op.f("ix_assignments_term_id"), "assignments", ["term_id"], unique=False)

    # 14. assignment_submissions table
    op.create_table(
        "assignment_submissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("submission_content", sa.Text(), nullable=True),
        sa.Column("attachment_path", sa.String(length=500), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SUBMITTED"),
        sa.Column("marks_obtained", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("evaluated_by_faculty_id", sa.String(length=36), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluated_by_faculty_id"], ["faculty_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id", "student_id", "attempt_number", name="uq_submissions_assignment_student_attempt"),
        sa.CheckConstraint("attempt_number >= 1", name="chk_submissions_attempt_number"),
        sa.CheckConstraint("marks_obtained IS NULL OR marks_obtained >= 0", name="chk_submissions_marks_obtained"),
    )
    op.create_index(op.f("ix_assignment_submissions_assignment_id"), "assignment_submissions", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_assignment_submissions_evaluated_by_faculty_id"), "assignment_submissions", ["evaluated_by_faculty_id"], unique=False)
    op.create_index(op.f("ix_assignment_submissions_id"), "assignment_submissions", ["id"], unique=False)
    op.create_index(op.f("ix_assignment_submissions_student_id"), "assignment_submissions", ["student_id"], unique=False)

    # 15. assessments table
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("term_id", sa.String(length=36), nullable=False),
        sa.Column("section_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_faculty_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("assessment_type", sa.String(length=50), nullable=False),
        sa.Column("max_marks", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("weightage_percentage", sa.Numeric(precision=5, scale=2), nullable=False, server_default="20.00"),
        sa.Column("assessment_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_faculty_id"], ["faculty_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["term_id"], ["academic_terms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "term_id", "title", name="uq_assessments_course_term_title"),
        sa.CheckConstraint("max_marks > 0", name="chk_assessments_max_marks"),
        sa.CheckConstraint("weightage_percentage >= 0 AND weightage_percentage <= 100", name="chk_assessments_weightage"),
    )
    op.create_index(op.f("ix_assessments_course_id"), "assessments", ["course_id"], unique=False)
    op.create_index(op.f("ix_assessments_created_by_faculty_id"), "assessments", ["created_by_faculty_id"], unique=False)
    op.create_index(op.f("ix_assessments_id"), "assessments", ["id"], unique=False)
    op.create_index(op.f("ix_assessments_section_id"), "assessments", ["section_id"], unique=False)
    op.create_index(op.f("ix_assessments_term_id"), "assessments", ["term_id"], unique=False)

    # 16. assessment_results table
    op.create_table(
        "assessment_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("assessment_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("is_absent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("evaluated_by_faculty_id", sa.String(length=36), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["evaluated_by_faculty_id"], ["faculty_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "student_id", name="uq_assessment_results_assessment_student"),
        sa.CheckConstraint("marks_obtained IS NULL OR marks_obtained >= 0", name="chk_assessment_results_marks_obtained"),
    )
    op.create_index(op.f("ix_assessment_results_assessment_id"), "assessment_results", ["assessment_id"], unique=False)
    op.create_index(op.f("ix_assessment_results_evaluated_by_faculty_id"), "assessment_results", ["evaluated_by_faculty_id"], unique=False)
    op.create_index(op.f("ix_assessment_results_id"), "assessment_results", ["id"], unique=False)
    op.create_index(op.f("ix_assessment_results_student_id"), "assessment_results", ["student_id"], unique=False)

    # 17. Seed academic:write_all permission and assign to ADMIN & SUPER_ADMIN
    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("id", sa.String),
        sa.column("role_id", sa.String),
        sa.column("permission_id", sa.String),
        sa.column("created_at", sa.DateTime),
    )

    perm_id = str(uuid.uuid4())
    op.bulk_insert(
        permissions_table,
        [{
            "id": perm_id,
            "code": "academic:write_all",
            "name": "Write All Academic Hierarchy",
            "description": "Create and manage institutional departments, programs, batches, courses, and profiles",
            "created_at": now,
            "updated_at": now,
        }],
    )

    # Fetch role IDs using SQL subselects / conditional inserts
    # In Alembic upgrade, we can run direct insert select
    bind = op.get_bind()
    super_admin = bind.execute(sa.select(roles_table.c.id).where(roles_table.c.name == "SUPER_ADMIN")).scalar()
    admin = bind.execute(sa.select(roles_table.c.id).where(roles_table.c.name == "ADMIN")).scalar()

    assignments = []
    if super_admin:
        assignments.append({
            "id": str(uuid.uuid4()),
            "role_id": super_admin,
            "permission_id": perm_id,
            "created_at": now,
        })
    if admin:
        assignments.append({
            "id": str(uuid.uuid4()),
            "role_id": admin,
            "permission_id": perm_id,
            "created_at": now,
        })
    if assignments:
        op.bulk_insert(role_permissions_table, assignments)


def downgrade() -> None:
    # 1. Clean up added permission
    bind = op.get_bind()
    perm_id = bind.execute(
        sa.text("SELECT id FROM permissions WHERE code = 'academic:write_all'")
    ).scalar()
    if perm_id:
        bind.execute(sa.text(f"DELETE FROM role_permissions WHERE permission_id = '{perm_id}'"))
        bind.execute(sa.text(f"DELETE FROM permissions WHERE id = '{perm_id}'"))

    # 2. Drop academic domain tables in reverse topological order
    op.drop_table("assessment_results")
    op.drop_table("assessments")
    op.drop_table("assignment_submissions")
    op.drop_table("assignments")
    op.drop_table("attendance_records")

    op.drop_index("uq_faculty_assignment_section", table_name="faculty_course_assignments")
    op.drop_index("uq_faculty_assignment_course_wide", table_name="faculty_course_assignments")
    op.drop_table("faculty_course_assignments")

    op.drop_table("enrollments")
    op.drop_table("faculty_profiles")
    op.drop_table("student_profiles")
    op.drop_table("courses")
    op.drop_table("academic_terms")
    op.drop_table("sections")
    op.drop_table("batches")
    op.drop_table("programs")
    op.drop_table("departments")
    op.drop_table("institutions")
