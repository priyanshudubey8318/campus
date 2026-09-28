"""0009 Phase 7 PulseCase Subsystem

Revision ID: 0009_phase7_pulsecase
Revises: 0008_phase6_pulserecord
Create Date: 2026-09-24 01:00:00.000000

Implements:
- support_cases
- case_notes
- case_interventions
- case_follow_ups
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0009_phase7_pulsecase"
down_revision: Union[str, None] = "0008_phase6_pulserecord"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. support_cases
    op.create_table(
        "support_cases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("case_number", sa.String(length=50), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("case_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="OPEN", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="MEDIUM", nullable=False),
        sa.Column("trigger_source", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("assigned_staff_id", sa.String(length=36), nullable=True),
        sa.Column("assigned_staff_role", sa.String(length=50), nullable=True),
        sa.Column("referred_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_outcome", sa.String(length=50), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "case_type IN ('ACADEMIC_SUPPORT', 'ATTENDANCE_INTERVENTION', 'EARLY_WARNING_TRIAGE', 'WELLBEING_REFERRAL')",
            name="chk_case_type",
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'WAITING_FOR_STUDENT', 'FOLLOW_UP_SCHEDULED', 'RESOLVED', 'CLOSED')",
            name="chk_case_status",
        ),
        sa.CheckConstraint(
            "priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')",
            name="chk_case_priority",
        ),
        sa.CheckConstraint(
            "trigger_source IN ('PULSERISK_SPI', 'PULSEWATCH_SHIFT', 'FACULTY_REFERRAL', 'STUDENT_REQUEST', 'MANUAL_ADVISOR')",
            name="chk_case_trigger_source",
        ),
        sa.CheckConstraint(
            "assigned_staff_role IS NULL OR assigned_staff_role IN ('ADVISOR', 'COUNSELOR')",
            name="chk_case_assigned_role",
        ),
        sa.CheckConstraint(
            "(status = 'RESOLVED' AND resolution_outcome IS NOT NULL AND resolved_at IS NOT NULL) OR (status != 'RESOLVED')",
            name="chk_case_resolution_integrity",
        ),
        sa.CheckConstraint(
            "resolution_outcome IS NULL OR resolution_outcome IN ('IMPROVED_ENGAGEMENT', 'ACADEMIC_PLAN_ESTABLISHED', 'REFERRED_TO_EXTERNAL_RESOURCE', 'STUDENT_UNRESPONSIVE', 'NO_FURTHER_ACTION')",
            name="chk_case_resolution_outcome_enum",
        ),
        sa.CheckConstraint(
            "(status = 'CLOSED' AND closed_at IS NOT NULL AND closed_by_user_id IS NOT NULL) OR (status != 'CLOSED')",
            name="chk_case_closed_integrity",
        ),
        sa.CheckConstraint(
            "(case_type != 'WELLBEING_REFERRAL') OR (assigned_staff_role IS NULL OR assigned_staff_role = 'COUNSELOR')",
            name="chk_case_wellbeing_role",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_staff_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["referred_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number", name="uq_support_cases_case_number"),
    )
    op.create_index("ix_support_cases_id", "support_cases", ["id"])
    op.create_index("ix_support_cases_institution_id", "support_cases", ["institution_id"])
    op.create_index("ix_support_cases_student_id", "support_cases", ["student_id"])
    op.create_index("ix_support_cases_inst_student", "support_cases", ["institution_id", "student_id"])
    op.create_index("ix_support_cases_inst_status", "support_cases", ["institution_id", "status"])
    op.create_index("ix_support_cases_assigned_staff", "support_cases", ["institution_id", "assigned_staff_id", "status"])
    op.create_index("ix_support_cases_referred_by", "support_cases", ["institution_id", "referred_by_user_id"])
    op.create_index("ix_support_cases_created", "support_cases", ["institution_id", "created_at"])

    # 2. case_notes
    op.create_table(
        "case_notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("author_user_id", sa.String(length=36), nullable=False),
        sa.Column("note_type", sa.String(length=50), server_default="ADVISING_NOTE", nullable=False),
        sa.Column("confidentiality_level", sa.String(length=50), server_default="STANDARD", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "note_type IN ('ADVISING_NOTE', 'STUDENT_INTERACTION', 'COUNSELOR_CONFIDENTIAL', 'ACTION_PLAN', 'SYSTEM_EVENT')",
            name="chk_case_note_type",
        ),
        sa.CheckConstraint(
            "confidentiality_level IN ('STANDARD', 'RESTRICTED_ADVISING', 'COUNSELOR_CONFIDENTIAL')",
            name="chk_case_note_confidentiality",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["case_id"], ["support_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_notes_id", "case_notes", ["id"])
    op.create_index("ix_case_notes_institution_id", "case_notes", ["institution_id"])
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id"])
    op.create_index("ix_case_notes_author_user_id", "case_notes", ["author_user_id"])
    op.create_index("ix_case_notes_case", "case_notes", ["case_id", "created_at"])
    op.create_index("ix_case_notes_confidentiality", "case_notes", ["case_id", "confidentiality_level"])

    # 3. case_interventions
    op.create_table(
        "case_interventions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("intervention_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("assigned_to_user_id", sa.String(length=36), nullable=True),
        sa.Column("target_completion_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="PLANNED", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "intervention_type IN ('ONE_ON_ONE_ADVISING', 'PEER_TUTORING_REFERRAL', 'ACADEMIC_SKILLS_WORKSHOP', 'ATTENDANCE_CONTRACT', 'WELLBEING_SUPPORT', 'COURSE_LOAD_ADJUSTMENT')",
            name="chk_case_intervention_type",
        ),
        sa.CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')",
            name="chk_case_intervention_status",
        ),
        sa.CheckConstraint(
            "(status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status != 'COMPLETED')",
            name="chk_case_intervention_completed",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["case_id"], ["support_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_interventions_id", "case_interventions", ["id"])
    op.create_index("ix_case_interventions_institution_id", "case_interventions", ["institution_id"])
    op.create_index("ix_case_interventions_case_id", "case_interventions", ["case_id"])
    op.create_index("ix_case_interventions_case", "case_interventions", ["case_id", "status"])

    # 4. case_follow_ups
    op.create_table(
        "case_follow_ups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.String(length=20), nullable=True),
        sa.Column("follow_up_type", sa.String(length=50), server_default="CHECK_IN_MEETING", nullable=False),
        sa.Column("assigned_staff_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="SCHEDULED", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "follow_up_type IN ('CHECK_IN_MEETING', 'ACADEMIC_PROGRESS_REVIEW', 'ATTENDANCE_CHECK', 'WELLBEING_FOLLOW_UP')",
            name="chk_case_follow_up_type",
        ),
        sa.CheckConstraint(
            "status IN ('SCHEDULED', 'COMPLETED', 'MISSED', 'RESCHEDULED', 'CANCELLED')",
            name="chk_case_follow_up_status",
        ),
        sa.CheckConstraint(
            "(status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status != 'COMPLETED')",
            name="chk_case_follow_up_completed",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["case_id"], ["support_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_staff_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_follow_ups_id", "case_follow_ups", ["id"])
    op.create_index("ix_case_follow_ups_institution_id", "case_follow_ups", ["institution_id"])
    op.create_index("ix_case_follow_ups_case_id", "case_follow_ups", ["case_id"])
    op.create_index("ix_case_follow_ups_assigned_staff_id", "case_follow_ups", ["assigned_staff_id"])
    op.create_index("ix_case_follow_ups_case", "case_follow_ups", ["case_id", "scheduled_date"])
    op.create_index("ix_case_follow_ups_staff_date", "case_follow_ups", ["assigned_staff_id", "scheduled_date"])


def downgrade() -> None:
    op.drop_index("ix_case_follow_ups_staff_date", table_name="case_follow_ups")
    op.drop_index("ix_case_follow_ups_case", table_name="case_follow_ups")
    op.drop_index("ix_case_follow_ups_assigned_staff_id", table_name="case_follow_ups")
    op.drop_index("ix_case_follow_ups_case_id", table_name="case_follow_ups")
    op.drop_index("ix_case_follow_ups_institution_id", table_name="case_follow_ups")
    op.drop_index("ix_case_follow_ups_id", table_name="case_follow_ups")
    op.drop_table("case_follow_ups")

    op.drop_index("ix_case_interventions_case", table_name="case_interventions")
    op.drop_index("ix_case_interventions_case_id", table_name="case_interventions")
    op.drop_index("ix_case_interventions_institution_id", table_name="case_interventions")
    op.drop_index("ix_case_interventions_id", table_name="case_interventions")
    op.drop_table("case_interventions")

    op.drop_index("ix_case_notes_confidentiality", table_name="case_notes")
    op.drop_index("ix_case_notes_case", table_name="case_notes")
    op.drop_index("ix_case_notes_author_user_id", table_name="case_notes")
    op.drop_index("ix_case_notes_case_id", table_name="case_notes")
    op.drop_index("ix_case_notes_institution_id", table_name="case_notes")
    op.drop_index("ix_case_notes_id", table_name="case_notes")
    op.drop_table("case_notes")

    op.drop_index("ix_support_cases_created", table_name="support_cases")
    op.drop_index("ix_support_cases_referred_by", table_name="support_cases")
    op.drop_index("ix_support_cases_assigned_staff", table_name="support_cases")
    op.drop_index("ix_support_cases_inst_status", table_name="support_cases")
    op.drop_index("ix_support_cases_inst_student", table_name="support_cases")
    op.drop_index("ix_support_cases_student_id", table_name="support_cases")
    op.drop_index("ix_support_cases_institution_id", table_name="support_cases")
    op.drop_index("ix_support_cases_id", table_name="support_cases")
    op.drop_table("support_cases")
