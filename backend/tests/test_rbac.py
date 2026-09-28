"""Tests for role-based and permission-based access control (RBAC)."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth_deps import check_resource_ownership
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegisterRequest


from tests.conftest import get_test_session


@pytest.fixture
def test_users(client: TestClient):
    """Seed test users with different roles: student, admin, and super_admin directly in database."""
    session = get_test_session()
    users = {}
    specs = [
        ("student", "test.student@univ.edu", "STUDENT"),
        ("admin", "test.admin@univ.edu", "ADMIN"),
        ("super_admin", "test.superadmin@univ.edu", "SUPER_ADMIN"),
    ]
    try:
        for key, email, role in specs:
            user = UserRepository.get_by_email(session, email)
            if not user:
                user = UserRepository.create_user(
                    db=session,
                    email=email,
                    password_hash=hash_password("Password123!"),
                    full_name=f"Test {role}",
                    is_active=True,
                    is_verified=True,
                )
            UserRepository.set_user_roles(session, user.id, [role])
            users[key] = UserRepository.get_by_id(session, user.id)
        yield users
    finally:
        session.close()




def _get_token(client: TestClient, email: str, password: str = "Password123!") -> str:
    """Helper to authenticate and return access token."""
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_rbac_unauthenticated_request_rejected(client: TestClient):
    """Verify unauthenticated requests to protected endpoints return 401."""
    res = client.get("/api/v1/auth/role-check/admin")
    assert res.status_code == 401
    assert "not provided" in res.json()["detail"].lower()


def test_rbac_role_enforcement_student_vs_admin(client: TestClient, test_users):
    """Verify STUDENT role can access student endpoint but is rejected from admin endpoint with 403."""
    student_token = _get_token(client, "test.student@univ.edu")

    # Access student endpoint -> allowed
    res_student = client.get(
        "/api/v1/auth/role-check/student",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == 200
    assert "Student access granted" in res_student.json()["message"]

    # Access admin endpoint -> forbidden (403)
    res_admin = client.get(
        "/api/v1/auth/role-check/admin",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_admin.status_code == 403
    assert "requires one of roles" in res_admin.json()["detail"].lower()


def test_rbac_admin_can_access_admin_endpoint(client: TestClient, test_users):
    """Verify ADMIN role accesses admin endpoint successfully."""
    admin_token = _get_token(client, "test.admin@univ.edu")
    res = client.get(
        "/api/v1/auth/role-check/admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert "Admin access granted" in res.json()["message"]


def test_rbac_super_admin_bypass_on_any_role(client: TestClient, test_users):
    """Verify SUPER_ADMIN satisfies role constraints across all endpoints."""
    super_admin_token = _get_token(client, "test.superadmin@univ.edu")

    # Super admin accesses admin check
    res_admin = client.get(
        "/api/v1/auth/role-check/admin",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_admin.status_code == 200

    # Super admin accesses student check
    res_student = client.get(
        "/api/v1/auth/role-check/student",
        headers={"Authorization": f"Bearer {super_admin_token}"},
    )
    assert res_student.status_code == 200


def test_rbac_permission_check_enforcement(client: TestClient, test_users):
    """Verify permission check permits ADMIN (has users:write) and rejects STUDENT."""
    student_token = _get_token(client, "test.student@univ.edu")
    admin_token = _get_token(client, "test.admin@univ.edu")

    # Student lacks users:write -> 403
    res_student = client.get(
        "/api/v1/auth/permission-check/user-manage",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == 403
    assert "requires permissions" in res_student.json()["detail"].lower()

    # Admin has users:write -> 200
    res_admin = client.get(
        "/api/v1/auth/permission-check/user-manage",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    assert "Permission granted" in res_admin.json()["message"]


def test_inactive_user_access_blocked(client: TestClient):
    """Verify inactive user accounts are blocked with 403 Forbidden even with valid token."""
    email = "inactive.user@univ.edu"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Inactive User",
        "role": "STUDENT",
    })
    assert reg_res.status_code == 201

    # Generate token while active
    token_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
    })
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]

    # Deactivate account in database
    with get_test_session() as session:
        user = session.query(User).filter_by(email=email).first()
        assert user is not None
        user.is_active = False
        session.commit()

    # Attempt to access protected endpoint
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "inactive" in res.json()["detail"].lower()


def test_resource_ownership_helper(test_users):
    """Verify check_resource_ownership allows owner and admins, rejects third parties."""
    student = test_users["student"]
    admin = test_users["admin"]
    super_admin = test_users["super_admin"]

    # 1. Owner accessing own resource -> succeeds
    assert check_resource_ownership(user=student, resource_owner_id=str(student.id)) is True

    # 2. Admin accessing student's resource -> succeeds
    assert check_resource_ownership(user=admin, resource_owner_id=str(student.id)) is True

    # 3. Super Admin accessing student's resource -> succeeds
    assert check_resource_ownership(user=super_admin, resource_owner_id=str(student.id)) is True

    # 4. Student accessing another user's resource -> raises 403
    with pytest.raises(HTTPException) as exc_info:
        check_resource_ownership(user=student, resource_owner_id="different-user-id-12345")
    assert exc_info.value.status_code == 403


def test_external_reporter_role_access(client: TestClient):
    """Verify EXTERNAL_REPORTER role is supported, can register, and has appropriate access boundaries."""
    email = "reporter.test@external.org"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "External Reporter",
        "role": "EXTERNAL_REPORTER",
    })
    assert reg_res.status_code == 201
    assert "EXTERNAL_REPORTER" in reg_res.json()["roles"]

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
    })
    token = login_res.json()["access_token"]

    # 1. Access external reporter check -> 200
    res_reporter = client.get(
        "/api/v1/auth/role-check/external-reporter",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_reporter.status_code == 200
    assert "External reporter access granted" in res_reporter.json()["message"]

    # 2. Access admin check -> 403 Forbidden
    res_admin = client.get(
        "/api/v1/auth/role-check/admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_admin.status_code == 403


def test_privilege_escalation_prevention_registration(client: TestClient):
    """Verify unauthenticated users cannot self-assign privileged roles during registration."""
    forbidden_roles = ["ADMIN", "SUPER_ADMIN", "FACULTY", "ADVISOR", "COUNSELOR"]
    for privileged_role in forbidden_roles:
        res = client.post("/api/v1/auth/register", json={
            "email": f"hacker.{privileged_role.lower()}@evil.org",
            "password": "Password123!",
            "full_name": f"Hacker {privileged_role}",
            "role": privileged_role,
        })
        assert res.status_code == 400, f"Expected 400 for self-assigning role {privileged_role}"
        assert "not permitted" in res.json()["detail"].lower()


def test_privilege_escalation_prevention_role_modification(client: TestClient, test_users):
    """Verify non-admin users cannot call role assignment endpoint or modify user roles."""
    student = test_users["student"]
    admin = test_users["admin"]
    student_token = _get_token(client, "test.student@univ.edu")
    admin_token = _get_token(client, "test.admin@univ.edu")

    # 1. Student attempts to promote self to ADMIN -> 403 Forbidden
    res_self = client.put(
        f"/api/v1/auth/users/{student.id}/roles",
        json={"roles": ["ADMIN"]},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_self.status_code == 403
    assert "requires permissions: [roles:write]" in res_self.json()["detail"].lower()

    # 2. Student attempts to demote ADMIN -> 403 Forbidden
    res_target = client.put(
        f"/api/v1/auth/users/{admin.id}/roles",
        json={"roles": ["STUDENT"]},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_target.status_code == 403

    # 3. Admin with roles:write updates student roles -> 200 OK
    res_admin = client.put(
        f"/api/v1/auth/users/{student.id}/roles",
        json={"roles": ["STUDENT", "EXTERNAL_REPORTER"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    roles = res_admin.json()["roles"]
    assert "STUDENT" in roles
    assert "EXTERNAL_REPORTER" in roles


def test_immediate_role_removal_enforcement(client: TestClient):
    """Verify that removing a role immediately denies access on the very next request
    even when using an already-issued, unexpired JWT access token.
    """
    email = "temp.admin@univ.edu"
    # Register as student
    reg_res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Temporary Admin",
        "role": "STUDENT",
    })
    user_id = reg_res.json()["id"]

    # Promote to ADMIN in database
    with get_test_session() as session:
        admin_role = UserRepository.get_role_by_name(session, "ADMIN")
        assert admin_role is not None
        UserRepository.assign_role(session, user_id, admin_role.id)

    # Login and receive JWT access token
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
    })
    token = login_res.json()["access_token"]

    # Request 1: Verify token has admin access
    res1 = client.get(
        "/api/v1/auth/role-check/admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200

    # Demote user back to STUDENT (removing ADMIN role)
    with get_test_session() as session:
        UserRepository.set_user_roles(session, user_id, ["STUDENT"])

    # Request 2: With the SAME already-issued access token, verify access is IMMEDIATELY revoked
    res2 = client.get(
        "/api/v1/auth/role-check/admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 403
    assert "requires one of roles" in res2.json()["detail"].lower()

