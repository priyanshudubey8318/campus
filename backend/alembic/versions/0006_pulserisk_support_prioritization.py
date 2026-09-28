"""0006 PulseRisk Support Prioritization Subsystem

Revision ID: 0006_pulserisk_support_prioritization
Revises: 0005_pulsewatch_behavioral_monitoring
Create Date: 2026-09-22 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_pulserisk_support_prioritization"
down_revision: Union[str, None] = "0005_pulsewatch_behavioral_monitoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. risk_policies table
    op.create_table(
        "risk_policies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("institution_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("weight_attendance", sa.Numeric(precision=5, scale=3), nullable=False, server_default="0.350"),
        sa.Column("weight_coursework", sa.Numeric(precision=5, scale=3), nullable=False, server_default="0.300"),
        sa.Column("weight_assessment", sa.Numeric(precision=5, scale=3), nullable=False, server_default="0.250"),
        sa.Column("weight_persistence", sa.Numeric(precision=5, scale=3), nullable=False, server_default="0.100"),
        sa.Column("threshold_moderate", sa.Numeric(precision=5, scale=2), nullable=False, server_default="25.00"),
        sa.Column("threshold_elevated", sa.Numeric(precision=5, scale=2), nullable=False, server_default="50.00"),
        sa.Column("threshold_urgent", sa.Numeric(precision=5, scale=2), nullable=False, server_default="75.00"),
        sa.Column("persistence_half_life_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("policy_version", sa.String(length=20), nullable=False, server_default="v1.0"),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "weight_attendance + weight_coursework + weight_assessment + weight_persistence = 1.000",
            name="chk_risk_policies_weight_sum",
        ),
        sa.CheckConstraint(
            "threshold_moderate < threshold_elevated AND threshold_elevated < threshold_urgent",
            name="chk_risk_policies_threshold_order",
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "code", "policy_version", name="uq_risk_policies_institution_code_version"),
    )
    op.create_index(op.f("ix_risk_policies_id"), "risk_policies", ["id"], unique=False)
    op.create_index(op.f("ix_risk_policies_institution_id"), "risk_policies", ["institution_id"], unique=False)
    op.create_index(op.f("ix_risk_policies_status"), "risk_policies", ["status"], unique=False)
    op.create_index(
        "uq_risk_policies_active_scope",
        "risk_policies",
        ["institution_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )

    # 2. student_risk_snapshots table
    op.create_table(
        "student_risk_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=36), nullable=False),
        sa.Column("policy_id", sa.String(length=36), nullable=False),
        sa.Column("evaluation_date", sa.Date(), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("support_priority_index", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("priority_tier", sa.String(length=50), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=2), nullable=False, server_default="1.00"),
        sa.Column("data_quality", sa.String(length=50), nullable=False),
        sa.Column("primary_driver", sa.String(length=50), nullable=True),
        sa.Column("input_snapshot_json", sa.Text(), nullable=True),
        sa.Column("decomposition_json", sa.Text(), nullable=False),
        sa.Column("summary_text", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="EVALUATED"),
        sa.Column("algorithm_version", sa.String(length=20), nullable=False, server_default="pulserisk-v1.0"),
        sa.Column("policy_version", sa.String(length=20), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["policy_id"], ["risk_policies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "evaluation_date",
            "window_days",
            "algorithm_version",
            "policy_version",
            name="uq_student_risk_snapshots_identity",
        ),
    )
    op.create_index(op.f("ix_student_risk_snapshots_id"), "student_risk_snapshots", ["id"], unique=False)
    op.create_index(op.f("ix_student_risk_snapshots_student_id"), "student_risk_snapshots", ["student_id"], unique=False)
    op.create_index(op.f("ix_student_risk_snapshots_policy_id"), "student_risk_snapshots", ["policy_id"], unique=False)
    op.create_index(
        "ix_student_risk_snapshots_student_id_date",
        "student_risk_snapshots",
        ["student_id", "evaluation_date"],
        unique=False,
    )
    op.create_index(
        "ix_student_risk_snapshots_priority_tier",
        "student_risk_snapshots",
        ["priority_tier"],
        unique=False,
    )
    op.create_index(
        "ix_student_risk_snapshots_spi",
        "student_risk_snapshots",
        ["support_priority_index"],
        unique=False,
    )

    # 3. risk_signal_contributions table
    op.create_table(
        "risk_signal_contributions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("dimension", sa.String(length=50), nullable=False),
        sa.Column("metric_label", sa.String(length=100), nullable=False),
        sa.Column("observed_value", sa.String(length=100), nullable=True),
        sa.Column("baseline_value", sa.String(length=100), nullable=True),
        sa.Column("delta_value", sa.String(length=100), nullable=True),
        sa.Column("factor_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("assigned_weight", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column("weighted_contribution", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("data_quality", sa.String(length=50), nullable=False),
        sa.Column("source_signal", sa.String(length=50), nullable=True),
        sa.Column("evidence_payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["snapshot_id"], ["student_risk_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_risk_signal_contributions_id"), "risk_signal_contributions", ["id"], unique=False)
    op.create_index(op.f("ix_risk_signal_contributions_snapshot_id"), "risk_signal_contributions", ["snapshot_id"], unique=False)
    op.create_index(
        "ix_risk_signal_contributions_snapshot_dimension",
        "risk_signal_contributions",
        ["snapshot_id", "dimension"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("risk_signal_contributions")
    op.drop_table("student_risk_snapshots")
    op.drop_table("risk_policies")
