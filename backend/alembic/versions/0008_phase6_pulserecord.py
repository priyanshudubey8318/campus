"""0008 Phase 6 PulseRecord Subsystem

Revision ID: 0008_phase6_pulserecord
Revises: 0007_pulseassist_rag_knowledge
Create Date: 2026-09-24 00:00:00.000000

Implements:
- leave_requests
- leave_attachments
- complaints
- complaint_evidence
- complaint_appeals
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008_phase6_pulserecord"
down_revision: Union[str, None] = "0007_pulseassist_rag_knowledge"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. leave_requests
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("leave_type", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("days_count", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="SUBMITTED", nullable=False),
        sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("end_date >= start_date", name="chk_leave_dates"),
        sa.CheckConstraint("days_count > 0", name="chk_leave_days_count"),
        sa.CheckConstraint(
            "leave_type IN ('MEDICAL', 'ACADEMIC_DUTY', 'PERSONAL', 'EMERGENCY', 'BEREAVEMENT')",
            name="chk_leave_type",
        ),
        sa.CheckConstraint(
            "status IN ('SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CANCELLED')",
            name="chk_leave_status",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leave_requests_id", "leave_requests", ["id"])
    op.create_index("ix_leave_requests_institution_id", "leave_requests", ["institution_id"])
    op.create_index("ix_leave_requests_student_id", "leave_requests", ["student_id"])
    op.create_index("ix_leave_requests_inst_student", "leave_requests", ["institution_id", "student_id"])
    op.create_index("ix_leave_requests_inst_status", "leave_requests", ["institution_id", "status"])
    op.create_index("ix_leave_requests_student_dates", "leave_requests", ["student_id", "start_date", "end_date"])
    op.create_index("ix_leave_requests_query_contract", "leave_requests", ["student_id", "status", "start_date", "end_date"])

    # 2. leave_attachments
    op.create_table(
        "leave_attachments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("leave_request_id", sa.String(length=36), nullable=False),
        sa.Column("uploader_user_id", sa.String(length=36), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("file_size_bytes > 0 AND file_size_bytes <= 10485760", name="chk_leave_attachment_size"),
        sa.CheckConstraint(
            "mime_type IN ('application/pdf', 'image/jpeg', 'image/png')",
            name="chk_leave_attachment_mime",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["leave_request_id"], ["leave_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploader_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_leave_attachments_id", "leave_attachments", ["id"])
    op.create_index("ix_leave_attachments_institution_id", "leave_attachments", ["institution_id"])
    op.create_index("ix_leave_attachments_leave_request_id", "leave_attachments", ["leave_request_id"])

    # 3. complaints
    op.create_table(
        "complaints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("complaint_code", sa.String(length=50), nullable=False),
        sa.Column("complainant_user_id", sa.String(length=36), nullable=False),
        sa.Column("complainant_role", sa.String(length=50), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_student_id", sa.String(length=36), nullable=True),
        sa.Column("target_department_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="SUBMITTED", nullable=False),
        sa.Column("assigned_reviewer_id", sa.String(length=36), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("adjudication_outcome", sa.String(length=50), nullable=True),
        sa.Column("adjudication_summary", sa.Text(), nullable=True),
        sa.Column("internal_reviewer_notes", sa.Text(), nullable=True),
        sa.Column("info_request_details", sa.Text(), nullable=True),
        sa.Column("info_response_details", sa.Text(), nullable=True),
        sa.Column("closed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "complainant_role IN ('STUDENT', 'EXTERNAL_REPORTER', 'FACULTY', 'OTHER')",
            name="chk_complaints_complainant_role",
        ),
        sa.CheckConstraint(
            "category IN ('ACADEMIC_INTEGRITY', 'FACILITY_HARASSMENT', 'DISCRIMINATION', 'GRADING_DISPUTE', 'SAFETY_CONCERN', 'OTHER')",
            name="chk_complaints_category",
        ),
        sa.CheckConstraint(
            "target_type IN ('STUDENT', 'FACULTY', 'DEPARTMENT', 'FACILITY', 'OTHER')",
            name="chk_complaints_target_type",
        ),
        sa.CheckConstraint(
            "status IN ('SUBMITTED', 'UNDER_REVIEW', 'NEEDS_INFORMATION', 'VERIFIED', 'DISMISSED', 'OTHER_AUTHORIZED_OUTCOME', 'APPEALED', 'RESOLVED', 'CLOSED')",
            name="chk_complaints_status",
        ),
        sa.CheckConstraint(
            "(status NOT IN ('VERIFIED', 'DISMISSED', 'OTHER_AUTHORIZED_OUTCOME', 'APPEALED', 'RESOLVED', 'CLOSED') AND adjudication_outcome IS NULL) "
            "OR (status IN ('VERIFIED', 'DISMISSED', 'OTHER_AUTHORIZED_OUTCOME', 'APPEALED', 'RESOLVED', 'CLOSED') AND adjudication_outcome IS NOT NULL)",
            name="chk_complaint_outcome_correlation",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["complainant_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_reviewer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "complaint_code", name="uq_complaints_inst_code"),
    )
    op.create_index("ix_complaints_id", "complaints", ["id"])
    op.create_index("ix_complaints_institution_id", "complaints", ["institution_id"])
    op.create_index("ix_complaints_complainant_user_id", "complaints", ["complainant_user_id"])
    op.create_index("ix_complaints_target_student_id", "complaints", ["target_student_id"])
    op.create_index("ix_complaints_assigned_reviewer_id", "complaints", ["assigned_reviewer_id"])
    op.create_index("ix_complaints_inst_status", "complaints", ["institution_id", "status"])
    op.create_index("ix_complaints_complainant", "complaints", ["complainant_user_id", "status"])
    op.create_index("ix_complaints_target_student", "complaints", ["target_student_id", "status"])
    op.create_index("ix_complaints_reviewer", "complaints", ["assigned_reviewer_id", "status"])

    # 4. complaint_evidence
    op.create_table(
        "complaint_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("complaint_id", sa.String(length=36), nullable=False),
        sa.Column("uploader_user_id", sa.String(length=36), nullable=False),
        sa.Column("uploader_role", sa.String(length=50), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_confidential", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_sealed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("file_size_bytes > 0 AND file_size_bytes <= 20971520", name="chk_complaint_evidence_size"),
        sa.CheckConstraint(
            "mime_type IN ('application/pdf', 'image/jpeg', 'image/png', 'text/plain')",
            name="chk_complaint_evidence_mime",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploader_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_complaint_evidence_id", "complaint_evidence", ["id"])
    op.create_index("ix_complaint_evidence_institution_id", "complaint_evidence", ["institution_id"])
    op.create_index("ix_complaint_evidence_complaint_id", "complaint_evidence", ["complaint_id"])

    # 5. complaint_appeals
    op.create_table(
        "complaint_appeals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("complaint_id", sa.String(length=36), nullable=False),
        sa.Column("appellant_user_id", sa.String(length=36), nullable=False),
        sa.Column("appeal_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="SUBMITTED", nullable=False),
        sa.Column("reviewer_user_id", sa.String(length=36), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("disposition_summary", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "status IN ('SUBMITTED', 'UNDER_REVIEW', 'UPHELD', 'OVERTURNED', 'MODIFIED', 'DISMISSED')",
            name="chk_complaint_appeals_status",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["appellant_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id", "appeal_number", name="uq_complaint_appeals_seq"),
    )
    op.create_index("ix_complaint_appeals_id", "complaint_appeals", ["id"])
    op.create_index("ix_complaint_appeals_institution_id", "complaint_appeals", ["institution_id"])
    op.create_index("ix_complaint_appeals_complaint_id", "complaint_appeals", ["complaint_id"])
    op.create_index("ix_complaint_appeals_appellant", "complaint_appeals", ["appellant_user_id"])


def downgrade() -> None:
    op.drop_table("complaint_appeals")
    op.drop_table("complaint_evidence")
    op.drop_table("complaints")
    op.drop_table("leave_attachments")
    op.drop_table("leave_requests")
