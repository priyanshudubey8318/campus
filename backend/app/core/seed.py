"""Database seeding utilities for system roles and permissions."""

import uuid
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.role import Role, Permission, RolePermission


INITIAL_ROLES = [
    ("SUPER_ADMIN", "Full institutional system administration and audit inspection"),
    ("ADMIN", "Administrative user management and role assignment"),
    ("FACULTY", "Academic operations, attendance and marks tracking"),
    ("ADVISOR", "Student advising, support review, and case coordination"),
    ("COUNSELOR", "Wellbeing and supportive intervention review"),
    ("STUDENT", "Student self-service portal, check-ins, and leave requests"),
    ("EXTERNAL_REPORTER", "Authorized reporter for formal complaints"),
]

INITIAL_PERMISSIONS = [
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
    ("cases:create", "Create Support Case", "Open intervention cases directly"),
    ("cases:refer", "Refer Student", "Submit advising referral for an enrolled student"),
    ("cases:assign", "Assign Case Handler", "Assign or reassign advisor/counselor"),
    ("cases:close", "Close Case", "Formally close and archive resolved intervention cases"),
    ("cases:read_own", "Read Own Case Summary", "Student self-service overview of support action items"),
    ("complaints:create", "Create Complaint", "Submit formal institutional grievances"),
    ("complaints:read_own", "Read Own Complaints", "Track submitted grievances"),
    ("complaints:read_assigned", "Read Assigned Complaints", "View complaints assigned to caller for review"),
    ("complaints:read_all", "Read All Complaints", "Review all submitted grievances"),
    ("complaints:review", "Review Complaint", "Adjudicate, request info, verify, dismiss, or resolve grievances"),
    ("complaints:appeal", "Appeal Complaint", "File formal contestation against an adjudication"),
    ("leaves:create", "Create Leave", "Apply for personal or academic leave"),
    ("leaves:read_own", "Read Own Leaves", "View own submitted leave requests and history"),
    ("leaves:read_assigned", "Read Assigned Leaves", "View leave requests for enrolled/assigned students"),
    ("leaves:read_all", "Read All Leaves", "Institutional overview of all leave requests"),
    ("leaves:review", "Review Leave", "Approve or reject student leave requests"),
]

ROLE_PERMISSION_MAP: Dict[str, List[str]] = {
    "SUPER_ADMIN": [p[0] for p in INITIAL_PERMISSIONS],
    "ADMIN": [
        "users:read", "users:write", "roles:read", "roles:write", "audit:read",
        "profile:read_all", "academic:read_all", "pulsewatch:read_all",
        "cases:read_all", "cases:write_assigned", "cases:create", "cases:refer", "cases:assign", "cases:close",
        "complaints:create", "complaints:read_own", "complaints:read_assigned", "complaints:read_all", "complaints:review",
        "leaves:read_all", "leaves:review",
    ],
    "FACULTY": [
        "profile:read_own", "profile:read_assigned",
        "academic:read_own", "academic:write_assigned",
        "pulsewatch:read_assigned",
        "cases:refer",
        "leaves:read_assigned", "leaves:review",
        "complaints:read_assigned", "complaints:review",
    ],
    "ADVISOR": [
        "profile:read_own", "profile:read_assigned",
        "academic:read_own", "pulsewatch:read_assigned",
        "cases:read_assigned", "cases:write_assigned", "cases:create", "cases:refer", "cases:assign", "cases:close",
        "leaves:read_assigned", "leaves:review",
        "complaints:read_assigned", "complaints:review",
    ],
    "COUNSELOR": [
        "profile:read_own", "profile:read_assigned",
        "cases:read_assigned", "cases:write_assigned",
        "complaints:read_assigned", "complaints:review",
    ],
    "STUDENT": [
        "profile:read_own", "academic:read_own",
        "pulsewatch:read_own",
        "cases:read_own",
        "leaves:create", "leaves:read_own",
        "complaints:create", "complaints:read_own", "complaints:appeal",
    ],
    "EXTERNAL_REPORTER": [
        "complaints:create", "complaints:read_own", "complaints:appeal",
    ],
}


def seed_roles_and_permissions(db: Session) -> None:
    """Idempotently seed foundational roles, permissions, and role-permission mappings."""
    # 1. Seed Roles
    existing_roles = {r.name: r for r in db.query(Role).all()}
    for name, desc in INITIAL_ROLES:
        if name not in existing_roles:
            role = Role(
                id=str(uuid.uuid4()),
                name=name,
                description=desc,
                is_system_role=True,
            )
            db.add(role)
            existing_roles[name] = role

    # 2. Seed Permissions
    existing_perms = {p.code: p for p in db.query(Permission).all()}
    for code, name, desc in INITIAL_PERMISSIONS:
        if code not in existing_perms:
            perm = Permission(
                id=str(uuid.uuid4()),
                code=code,
                name=name,
                description=desc,
            )
            db.add(perm)
            existing_perms[code] = perm

    db.commit()

    # Re-query all to get IDs
    roles_by_name = {r.name: r for r in db.query(Role).all()}
    perms_by_code = {p.code: p for p in db.query(Permission).all()}

    # 3. Seed Mappings
    existing_mappings = {
        (rp.role_id, rp.permission_id)
        for rp in db.query(RolePermission).all()
    }

    for role_name, perm_codes in ROLE_PERMISSION_MAP.items():
        role = roles_by_name.get(role_name)
        if not role:
            continue
        desired_perm_ids = {perms_by_code[p].id for p in perm_codes if p in perms_by_code}
        for rp in db.query(RolePermission).filter(RolePermission.role_id == role.id).all():
            if rp.permission_id not in desired_perm_ids:
                db.delete(rp)
                existing_mappings.discard((role.id, rp.permission_id))
        for pcode in perm_codes:
            perm = perms_by_code.get(pcode)
            if not perm:
                continue
            if (role.id, perm.id) not in existing_mappings:
                rp = RolePermission(
                    id=str(uuid.uuid4()),
                    role_id=role.id,
                    permission_id=perm.id,
                )
                db.add(rp)
                existing_mappings.add((role.id, perm.id))

    db.commit()
