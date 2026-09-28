"""0004 Academic Time-Series Indexes

Revision ID: 0004_academic_time_series_indexes
Revises: 0003_academic_foundation
Create Date: 2026-09-18 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_academic_time_series_indexes"
down_revision: Union[str, None] = "0003_academic_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure alembic_version table can accommodate revision identifiers longer than 32 chars
    op.alter_column("alembic_version", "version_num", type_=sa.String(length=64))

    # 1. Composite time-series index for student attendance window queries
    op.create_index(
        "ix_attendance_records_student_id_session_date",
        "attendance_records",
        ["student_id", "session_date"],
        unique=False,
    )

    # 2. Composite time-series index for student assignment submission velocity queries
    op.create_index(
        "ix_assignment_submissions_student_id_submitted_at",
        "assignment_submissions",
        ["student_id", "submitted_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop composite time-series indexes
    op.drop_index("ix_assignment_submissions_student_id_submitted_at", table_name="assignment_submissions")
    op.drop_index("ix_attendance_records_student_id_session_date", table_name="attendance_records")
