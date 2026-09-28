"""0002 Identity, Authentication, Authorization & RBAC

Revision ID: 0002_identity_and_access
Revises: 0001_initial_foundation
Create Date: 2026-09-18 11:30:00.000000

"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_identity_and_access"
down_revision: Union[str, None] = "0001_initial_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_is_active"), "users", ["is_active"], unique=False)

    # 2. roles table
    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_system_role", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    # 3. permissions table
    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_permissions_code"), "permissions", ["code"], unique=True)
    op.create_index(op.f("ix_permissions_id"), "permissions", ["id"], unique=False)

    # 4. user_roles association table
    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
    op.create_index(op.f("ix_user_roles_id"), "user_roles", ["id"], unique=False)
    op.create_index(op.f("ix_user_roles_role_id"), "user_roles", ["role_id"], unique=False)
    op.create_index(op.f("ix_user_roles_user_id"), "user_roles", ["user_id"], unique=False)

    # 5. role_permissions association table
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("permission_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index(op.f("ix_role_permissions_id"), "role_permissions", ["id"], unique=False)
    op.create_index(op.f("ix_role_permissions_permission_id"), "role_permissions", ["permission_id"], unique=False)
    op.create_index(op.f("ix_role_permissions_role_id"), "role_permissions", ["role_id"], unique=False)

    # 6. refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_expires_at"), "refresh_tokens", ["expires_at"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    # Seed Initial Roles and Permissions
    now = datetime.now(timezone.utc)
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("is_system_role", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("id", sa.String),
        sa.column("role_id", sa.String),
        sa.column("permission_id", sa.String),
        sa.column("created_at", sa.DateTime),
    )

    initial_roles = [
        ("SUPER_ADMIN", "Full institutional system administration and audit inspection"),
        ("ADMIN", "Administrative user management and role assignment"),
        ("FACULTY", "Academic operations, attendance and marks tracking"),
        ("ADVISOR", "Student advising, support review, and case coordination"),
        ("COUNSELOR", "Wellbeing and supportive intervention review"),
        ("STUDENT", "Student self-service portal, check-ins, and leave requests"),
        ("EXTERNAL_REPORTER", "Authorized reporter for formal complaints"),
    ]

    role_id_map = {}
    roles_data = []
    for role_name, desc in initial_roles:
        rid = str(uuid.uuid4())
        role_id_map[role_name] = rid
        roles_data.append({
            "id": rid,
            "name": role_name,
            "description": desc,
            "is_system_role": True,
            "created_at": now,
            "updated_at": now,
        })
    op.bulk_insert(roles_table, roles_data)

    initial_permissions = [
        ("users:read", "Read Users", "View user accounts and profiles"),
        ("users:write", "Write Users", "Create, update, and deactivate users"),
        ("roles:read", "Read Roles", "View role and permission assignments"),
        ("roles:write", "Write Roles", "Assign or revoke roles"),
        ("audit:read", "Read Audit Logs", "View system and security audit trails"),
        ("profile:read_own", "Read Own Profile", "View authenticated user's own profile"),
        ("profile:read_assigned", "Read Assigned Profiles", "View profiles of assigned students"),
        ("profile:read_all", "Read All Profiles", "View all student profiles"),
        ("academic:read_own", "Read Own Academic Data", "View own attendance and marks"),
        ("academic:write_assigned", "Write Academic Data", "Record attendance and grades"),
        ("academic:read_all", "Read All Academic Data", "View institutional academic records"),
        ("pulsewatch:read_own", "Read Own Alerts", "View own engagement check-in notifications"),
        ("pulsewatch:read_assigned", "Read Assigned Alerts", "View engagement signals for assigned students"),
        ("pulsewatch:read_all", "Read All Alerts", "View institutional engagement signals"),
        ("cases:read_assigned", "Read Assigned Cases", "View assigned intervention cases"),
        ("cases:write_assigned", "Write Assigned Cases", "Update notes and statuses on assigned cases"),
        ("cases:read_all", "Read All Cases", "View all institutional intervention cases"),
        ("complaints:create", "Create Complaint", "Submit formal institutional grievances"),
        ("complaints:read_own", "Read Own Complaints", "Track submitted grievances"),
        ("complaints:read_all", "Read All Complaints", "Review all submitted grievances"),
    ]

    perm_id_map = {}
    perms_data = []
    for code, name, desc in initial_permissions:
        pid = str(uuid.uuid4())
        perm_id_map[code] = pid
        perms_data.append({
            "id": pid,
            "code": code,
            "name": name,
            "description": desc,
            "created_at": now,
            "updated_at": now,
        })
    op.bulk_insert(permissions_table, perms_data)

    # Initial Role-Permission mappings
    role_perm_map = {
        "SUPER_ADMIN": list(perm_id_map.keys()),
        "ADMIN": [
            "users:read", "users:write", "roles:read", "roles:write", "audit:read",
            "profile:read_all", "academic:read_all", "pulsewatch:read_all", "cases:read_all", "complaints:read_all"
        ],
        "FACULTY": [
            "profile:read_own", "profile:read_assigned",
            "academic:read_own", "academic:write_assigned",
            "pulsewatch:read_assigned",
        ],
        "ADVISOR": [
            "profile:read_own", "profile:read_assigned",
            "academic:read_own", "pulsewatch:read_assigned",
            "cases:read_assigned", "cases:write_assigned",
        ],
        "COUNSELOR": [
            "profile:read_own", "profile:read_assigned",
            "cases:read_assigned", "cases:write_assigned",
        ],
        "STUDENT": [
            "profile:read_own", "academic:read_own",
            "pulsewatch:read_own", "complaints:create", "complaints:read_own",
        ],
        "EXTERNAL_REPORTER": [
            "complaints:create", "complaints:read_own",
        ],
    }

    role_perms_data = []
    for rname, codes in role_perm_map.items():
        rid = role_id_map[rname]
        for c in codes:
            if c in perm_id_map:
                role_perms_data.append({
                    "id": str(uuid.uuid4()),
                    "role_id": rid,
                    "permission_id": perm_id_map[c],
                    "created_at": now,
                })
    op.bulk_insert(role_permissions_table, role_perms_data)


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
