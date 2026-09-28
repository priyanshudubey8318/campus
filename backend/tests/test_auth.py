"""Comprehensive tests for authentication, registration, session management, and password security."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.rate_limit import login_rate_limiter
from app.models.audit_log import AuditLog
from app.models.user import User


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset in-memory rate limiter before each test."""
    login_rate_limiter.clear()
    yield
    login_rate_limiter.clear()


def test_user_registration_success(client: TestClient, db_session: Session):
    """Verify standard user registration with Argon2id hashing and default role assignment."""
    payload = {
        "email": "fresh.student@university.edu",
        "password": "SecurePassword123!",
        "full_name": "Student Tester",
        "phone": "+1234567890",
        "role": "STUDENT",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "fresh.student@university.edu"
    assert data["full_name"] == "Student Tester"
    assert data["is_active"] is True
    assert "STUDENT" in data["roles"]
    assert "password" not in data
    assert "password_hash" not in data

    # Verify audit log was written
    audit = db_session.query(AuditLog).filter_by(action="ACCOUNT_CREATED", entity_id=data["id"]).first()
    assert audit is not None
    assert audit.action == "ACCOUNT_CREATED"


def test_user_registration_duplicate_email(client: TestClient):
    """Verify duplicate email registration is rejected with 400 Bad Request."""
    payload = {
        "email": "duplicate@university.edu",
        "password": "SecurePassword123!",
        "full_name": "Duplicate Tester",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already registered" in res2.json()["detail"].lower()


def test_user_registration_password_complexity_validation(client: TestClient):
    """Verify that passwords missing uppercase, digit, or special character are rejected with 422."""
    weak_passwords = [
        "short1!",        # < 8 chars
        "alllowercase1!", # missing uppercase
        "ALLUPPERCASE1!", # missing lowercase
        "NoDigitsHere!",  # missing digit
        "NoSpecialChar1", # missing special char
    ]
    for weak_pw in weak_passwords:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"test_{abs(hash(weak_pw))}@university.edu",
                "password": weak_pw,
                "full_name": "Weak Password Tester",
            },
        )
        assert response.status_code == 422, f"Expected 422 for password: {weak_pw}"


def test_login_success_and_cookie_issuance(client: TestClient):
    """Verify login sets secure HTTP-only cookies and returns access token."""
    reg_payload = {
        "email": "login.test@university.edu",
        "password": "CorrectPassword123!",
        "full_name": "Login Tester",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "login.test@university.edu",
        "password": "CorrectPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login.test@university.edu"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Verify cookies
    assert "campuspulse_access_token" in response.cookies
    assert "campuspulse_refresh_token" in response.cookies


def test_login_invalid_credentials_prevents_enumeration(client: TestClient):
    """Verify incorrect credentials return 401 with generic error, preventing account enumeration."""
    # Register genuine user
    client.post("/api/v1/auth/register", json={
        "email": "enum.check@university.edu",
        "password": "CorrectPassword123!",
        "full_name": "Enum Check",
    })

    # 1. Existing user, wrong password
    res_wrong_pw = client.post("/api/v1/auth/login", json={
        "email": "enum.check@university.edu",
        "password": "WrongPassword123!",
    })
    assert res_wrong_pw.status_code == 401
    assert res_wrong_pw.json()["detail"] == "Invalid email or password"

    # 2. Non-existent user
    res_no_user = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@university.edu",
        "password": "AnyPassword123!",
    })
    assert res_no_user.status_code == 401
    assert res_no_user.json()["detail"] == "Invalid email or password"


def test_login_rate_limiting(client: TestClient):
    """Verify that repeated failed login attempts trigger HTTP 429 Too Many Requests."""
    target_email = "ratelimit.target@university.edu"
    for i in range(5):
        res = client.post("/api/v1/auth/login", json={
            "email": target_email,
            "password": f"WrongAttempt{i}!",
        })
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limiter
    res_blocked = client.post("/api/v1/auth/login", json={
        "email": target_email,
        "password": "AnyPassword123!",
    })
    assert res_blocked.status_code == 429
    assert "too many failed login attempts" in res_blocked.json()["detail"].lower()
    assert "Retry-After" in res_blocked.headers


def test_token_refresh_and_rotation(client: TestClient):
    """Verify session refresh issues a new access token and rotates the refresh token."""
    client.post("/api/v1/auth/register", json={
        "email": "refresh.user@university.edu",
        "password": "ValidPassword123!",
        "full_name": "Refresh User",
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": "refresh.user@university.edu",
        "password": "ValidPassword123!",
    })
    initial_refresh = login_res.cookies.get("campuspulse_refresh_token")
    assert initial_refresh is not None

    # Refresh session using cookie
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"campuspulse_refresh_token": initial_refresh},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data

    rotated_refresh = refresh_res.cookies.get("campuspulse_refresh_token")
    assert rotated_refresh is not None
    assert rotated_refresh != initial_refresh

    # Using the old refresh token again should be rejected (token rotation)
    stale_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"campuspulse_refresh_token": initial_refresh},
    )
    assert stale_res.status_code == 401


def test_logout_revocation_and_cookie_clearing(client: TestClient):
    """Verify logout revokes active session and removes cookies."""
    client.post("/api/v1/auth/register", json={
        "email": "logout.user@university.edu",
        "password": "ValidPassword123!",
        "full_name": "Logout User",
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": "logout.user@university.edu",
        "password": "ValidPassword123!",
    })
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.cookies.get("campuspulse_refresh_token")

    # Logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"campuspulse_refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200
    assert "logged out" in logout_res.json()["message"].lower()

    # Attempting to refresh with the revoked refresh token must fail
    refresh_after_logout = client.post(
        "/api/v1/auth/refresh",
        cookies={"campuspulse_refresh_token": refresh_token},
    )
    assert refresh_after_logout.status_code == 401


def test_get_current_user_profile(client: TestClient):
    """Verify /me returns active user profile with Bearer auth and rejects unauthenticated requests."""
    # Unauthenticated request
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # Authenticate
    client.post("/api/v1/auth/register", json={
        "email": "profile.user@university.edu",
        "password": "ValidPassword123!",
        "full_name": "Profile User",
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": "profile.user@university.edu",
        "password": "ValidPassword123!",
    })
    token = login_res.json()["access_token"]

    # Authenticated via Bearer header
    auth_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_res.status_code == 200
    profile = auth_res.json()
    assert profile["email"] == "profile.user@university.edu"
    assert profile["full_name"] == "Profile User"
    assert "STUDENT" in profile["roles"]


def test_refresh_token_replay_rejected(client: TestClient, db_session: Session):
    """Explicitly verify refresh token replay scenario:
    Login -> Token A -> Refresh with A -> Token B -> Refresh with A -> Rejected with 401 & audit logged.
    """
    email = "replay.check@university.edu"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Replay User",
    })

    # Step 1: Login to get refresh token A
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!",
    })
    token_a = login_res.cookies.get("campuspulse_refresh_token")
    assert token_a is not None

    # Step 2: Refresh using token A -> receive token B
    refresh_1 = client.post(
        "/api/v1/auth/refresh",
        cookies={"campuspulse_refresh_token": token_a},
    )
    assert refresh_1.status_code == 200
    token_b = refresh_1.cookies.get("campuspulse_refresh_token")
    assert token_b is not None
    assert token_b != token_a

    # Step 3: Verify replacement token B is valid
    refresh_2 = client.post(
        "/api/v1/auth/refresh",
        cookies={"campuspulse_refresh_token": token_b},
    )
    assert refresh_2.status_code == 200
    token_c = refresh_2.cookies.get("campuspulse_refresh_token")
    assert token_c is not None
    assert token_c != token_b

    # Step 4: Attempt refresh again using rotated token A -> MUST be rejected
    replay_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"campuspulse_refresh_token": token_a},
    )
    assert replay_res.status_code == 401
    assert "revoked" in replay_res.json()["detail"].lower()

    # Step 5: Verify security audit log captured TOKEN_REPLAY_ATTEMPT
    db_session.expire_all()
    audit_replay = db_session.query(AuditLog).filter_by(action="TOKEN_REPLAY_ATTEMPT").order_by(AuditLog.created_at.desc()).first()
    assert audit_replay is not None
    assert "revoked refresh token" in audit_replay.details.lower()



def test_audit_records_never_contain_sensitive_credentials(client: TestClient, db_session: Session):
    """Verify that all generated audit log entries strictly omit passwords, hashes, JWTs, and token secrets."""
    test_password = "SensitivePassword999!"
    wrong_password = "WrongGuessPassword888!"
    email = "audit.leak.test@university.edu"

    # Run full lifecycle: register, failed login, successful login, refresh, logout
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": test_password,
        "full_name": "Audit Security Tester",
    })

    client.post("/api/v1/auth/login", json={
        "email": email,
        "password": wrong_password,
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": test_password,
    })
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.cookies.get("campuspulse_refresh_token")

    client.post(
        "/api/v1/auth/refresh",
        cookies={"campuspulse_refresh_token": refresh_token},
    )

    client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"campuspulse_refresh_token": refresh_token},
    )

    # Inspect all audit logs in database
    db_session.expire_all()
    all_logs = db_session.query(AuditLog).all()
    assert len(all_logs) > 0

    for log in all_logs:
        fields = [
            log.action or "",
            log.details or "",
            log.actor_role or "",
            log.entity_type or "",
            log.ip_address or "",
        ]
        combined_text = " ".join(fields)

        # Asserts: No plaintext password
        assert test_password not in combined_text, f"Plaintext password leaked in audit log: {log.id}"
        assert wrong_password not in combined_text, f"Failed password attempt leaked in audit log: {log.id}"

        # Asserts: No Argon2id hash fragments
        assert "$argon2id$" not in combined_text, f"Password hash leaked in audit log: {log.id}"

        # Asserts: No raw JWT access tokens
        assert access_token not in combined_text, f"JWT access token leaked in audit log: {log.id}"

        # Asserts: No raw refresh token
        assert refresh_token not in combined_text, f"Raw refresh token leaked in audit log: {log.id}"

