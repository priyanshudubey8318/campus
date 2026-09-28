"""0005 PulseWatch Behavioral Monitoring Subsystem

Revision ID: 0005_pulsewatch_behavioral_monitoring
Revises: 0004_academic_time_series_indexes
Create Date: 2026-09-18 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_pulsewatch_behavioral_monitoring"
down_revision: Union[str, None] = "0004_academic_time_series_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. student_behavior_baselines table
    op.create_table(
        "student_behavior_baselines",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("baseline_value", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("data_quality", sa.String(length=50), nullable=False, server_default="NO_DATA"),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="pulsewatch-v1.0"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "metric_type",
            "window_days",
            "algorithm_version",
            name="uq_student_baselines_metric_window_algo",
        ),
    )
    op.create_index(op.f("ix_student_behavior_baselines_id"), "student_behavior_baselines", ["id"], unique=False)
    op.create_index(
        op.f("ix_student_behavior_baselines_student_id"),
        "student_behavior_baselines",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_student_baselines_student_id_metric",
        "student_behavior_baselines",
        ["student_id", "metric_type"],
        unique=False,
    )

    # 2. behavior_events table
    op.create_table(
        "behavior_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("observation_window_days", sa.Integer(), nullable=False),
        sa.Column("window_start_date", sa.Date(), nullable=False),
        sa.Column("window_end_date", sa.Date(), nullable=False),
        sa.Column("summary_text", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DETECTED"),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="pulsewatch-v1.0"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "observation_window_days",
            "window_start_date",
            "window_end_date",
            "algorithm_version",
            name="uq_behavior_events_student_window_algo",
        ),
    )
    op.create_index(op.f("ix_behavior_events_id"), "behavior_events", ["id"], unique=False)
    op.create_index(op.f("ix_behavior_events_student_id"), "behavior_events", ["student_id"], unique=False)
    op.create_index(
        "ix_behavior_events_student_id_detected_at",
        "behavior_events",
        ["student_id", "detected_at"],
        unique=False,
    )
    op.create_index(
        "ix_behavior_events_student_id_severity",
        "behavior_events",
        ["student_id", "severity"],
        unique=False,
    )

    # 3. behavior_signal_evidence table
    op.create_table(
        "behavior_signal_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("signal_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("baseline_value", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("delta_value", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("evidence_payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["event_id"], ["behavior_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_behavior_signal_evidence_id"), "behavior_signal_evidence", ["id"], unique=False)
    op.create_index(
        op.f("ix_behavior_signal_evidence_event_id"),
        "behavior_signal_evidence",
        ["event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_behavior_signal_evidence_event_id"), table_name="behavior_signal_evidence")
    op.drop_index(op.f("ix_behavior_signal_evidence_id"), table_name="behavior_signal_evidence")
    op.drop_table("behavior_signal_evidence")

    op.drop_index("ix_behavior_events_student_id_severity", table_name="behavior_events")
    op.drop_index("ix_behavior_events_student_id_detected_at", table_name="behavior_events")
    op.drop_index(op.f("ix_behavior_events_student_id"), table_name="behavior_events")
    op.drop_index(op.f("ix_behavior_events_id"), table_name="behavior_events")
    op.drop_table("behavior_events")

    op.drop_index("ix_student_baselines_student_id_metric", table_name="student_behavior_baselines")
    op.drop_index(op.f("ix_student_behavior_baselines_student_id"), table_name="student_behavior_baselines")
    op.drop_index(op.f("ix_student_behavior_baselines_id"), table_name="student_behavior_baselines")
    op.drop_table("student_behavior_baselines")
