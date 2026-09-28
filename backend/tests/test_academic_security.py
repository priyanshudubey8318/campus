"""Security and scoped authorization tests for Academic Domain endpoints."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.academic import (
    AcademicTerm,
    Course,
    Department,
    Enrollment,
    FacultyCourseAssignment,
    FacultyProfile,
    Institution,
    Program,
    Batch,
    Section,
    StudentProfile,
)
from app.repositories.user_repo import UserRepository
from tests.conftest import get_test_session


def _create_user_with_role(session: Session, email: str, role: str, name: str) -> str:
    user = UserRepository.get_by_email(session, email)
    if not user:
        user = UserRepository.create_user(
            db=session,
            email=email,
            password_hash=hash_password("Password123!"),
            full_name=name,
            is_active=True,
            is_verified=True,
        )
    UserRepository.set_user_roles(session, user.id, [role])
    return user.id


def _get_token(client: TestClient, email: str, password: str = "Password123!") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


@pytest.fixture
def security_setup(client: TestClient):
    """Set up two distinct students, two distinct faculty members, and two distinct courses."""
    session = get_test_session()
    try:
        # Hierarchy
        inst = Institution(id=str(uuid.uuid4()), name="Security Test Inst", code=f"STI_{uuid.uuid4().hex[:6]}")
        session.add(inst)
        session.flush()

        dept = Department(id=str(uuid.uuid4()), institution_id=inst.id, name="Security Dept", code=f"SD_{uuid.uuid4().hex[:6]}")
        session.add(dept)
        session.flush()

        prog = Program(id=str(uuid.uuid4()), department_id=dept.id, name="Sec Prog", code=f"SP_{uuid.uuid4().hex[:6]}")
        session.add(prog)
        session.flush()

        batch = Batch(id=str(uuid.uuid4()), program_id=prog.id, name=f"Batch_{uuid.uuid4().hex[:4]}", start_year=2024, end_year=2028)
        session.add(batch)
        session.flush()

        term = AcademicTerm(id=str(uuid.uuid4()), institution_id=inst.id, name=f"Term_{uuid.uuid4().hex[:4]}", start_date=date(2026, 8, 1), end_date=date(2026, 12, 15), is_current=True)
        session.add(term)
        session.flush()

        course_a = Course(id=str(uuid.uuid4()), institution_id=inst.id, department_id=dept.id, code=f"CSA_{uuid.uuid4().hex[:6]}", title="Course Alpha", credits=4)
        course_b = Course(id=str(uuid.uuid4()), institution_id=inst.id, department_id=dept.id, code=f"CSB_{uuid.uuid4().hex[:6]}", title="Course Beta", credits=4)
        session.add_all([course_a, course_b])
        session.flush()

        # Users
        u_stu_a_id = _create_user_with_role(session, f"student_a_{uuid.uuid4().hex[:4]}@test.edu", "STUDENT", "Student A")
        u_stu_b_id = _create_user_with_role(session, f"student_b_{uuid.uuid4().hex[:4]}@test.edu", "STUDENT", "Student B")
        u_fac_a_id = _create_user_with_role(session, f"faculty_a_{uuid.uuid4().hex[:4]}@test.edu", "FACULTY", "Prof Alpha")
        u_fac_b_id = _create_user_with_role(session, f"faculty_b_{uuid.uuid4().hex[:4]}@test.edu", "FACULTY", "Prof Beta")
        u_admin_id = _create_user_with_role(session, f"admin_{uuid.uuid4().hex[:4]}@test.edu", "ADMIN", "Admin User")

        stu_a_user = UserRepository.get_by_id(session, u_stu_a_id)
        stu_b_user = UserRepository.get_by_id(session, u_stu_b_id)
        fac_a_user = UserRepository.get_by_id(session, u_fac_a_id)
        fac_b_user = UserRepository.get_by_id(session, u_fac_b_id)
        admin_user = UserRepository.get_by_id(session, u_admin_id)

        # Profiles
        prof_stu_a = StudentProfile(id=str(uuid.uuid4()), user_id=stu_a_user.id, enrollment_number=f"ENR_A_{uuid.uuid4().hex[:6]}", program_id=prog.id, batch_id=batch.id, admission_date=date(2024, 8, 1))
        prof_stu_b = StudentProfile(id=str(uuid.uuid4()), user_id=stu_b_user.id, enrollment_number=f"ENR_B_{uuid.uuid4().hex[:6]}", program_id=prog.id, batch_id=batch.id, admission_date=date(2024, 8, 1))
        prof_fac_a = FacultyProfile(id=str(uuid.uuid4()), user_id=fac_a_user.id, employee_id=f"EMP_A_{uuid.uuid4().hex[:6]}", department_id=dept.id, designation="Professor", joining_date=date(2020, 1, 1))
        prof_fac_b = FacultyProfile(id=str(uuid.uuid4()), user_id=fac_b_user.id, employee_id=f"EMP_B_{uuid.uuid4().hex[:6]}", department_id=dept.id, designation="Professor", joining_date=date(2020, 1, 1))
        session.add_all([prof_stu_a, prof_stu_b, prof_fac_a, prof_fac_b])
        session.flush()

        # Faculty A teaches Course A; Faculty B teaches Course B
        session.add(FacultyCourseAssignment(id=str(uuid.uuid4()), faculty_id=prof_fac_a.id, course_id=course_a.id, term_id=term.id, role="PRIMARY_INSTRUCTOR"))
        session.add(FacultyCourseAssignment(id=str(uuid.uuid4()), faculty_id=prof_fac_b.id, course_id=course_b.id, term_id=term.id, role="PRIMARY_INSTRUCTOR"))

        # Student A is enrolled in Course A; Student B is enrolled in Course B
        session.add(Enrollment(id=str(uuid.uuid4()), student_id=prof_stu_a.id, course_id=course_a.id, term_id=term.id, enrollment_date=date(2026, 8, 1)))
        session.add(Enrollment(id=str(uuid.uuid4()), student_id=prof_stu_b.id, course_id=course_b.id, term_id=term.id, enrollment_date=date(2026, 8, 1)))

        session.commit()

        yield {
            "term": term,
            "course_a": course_a,
            "course_b": course_b,
            "stu_a_email": stu_a_user.email,
            "stu_b_email": stu_b_user.email,
            "fac_a_email": fac_a_user.email,
            "fac_b_email": fac_b_user.email,
            "admin_email": admin_user.email,
            "prof_stu_a_id": prof_stu_a.id,
            "prof_stu_b_id": prof_stu_b.id,
            "prof_fac_a_id": prof_fac_a.id,
            "prof_fac_b_id": prof_fac_b.id,
        }
    finally:
        session.close()


def test_unauthenticated_requests_return_401(client: TestClient):
    """Verify that unauthenticated callers are rejected with 401 across academic endpoints."""
    endpoints = [
        "/api/v1/academic/student-profiles/me",
        "/api/v1/academic/faculty-profiles/me",
        "/api/v1/academic/institutions",
        "/api/v1/academic/departments",
        "/api/v1/academic/programs",
        "/api/v1/academic/courses",
        "/api/v1/academic/enrollments",
        "/api/v1/academic/attendance",
        "/api/v1/academic/assignments",
        "/api/v1/academic/assessments",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 401, f"Expected 401 on {ep}, got {res.status_code}"


def test_cross_student_profile_access_forbidden(client: TestClient, security_setup: dict):
    """Verify that Student A cannot access Student B's academic profile (403 Forbidden)."""
    data = security_setup
    token_a = _get_token(client, data["stu_a_email"])

    # 1. Student A can access own profile via /me
    res_me = client.get(
        "/api/v1/academic/student-profiles/me",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["id"] == data["prof_stu_a_id"]

    # 2. Student A accessing Student B's profile directly returns 403 Forbidden
    res_other = client.get(
        f"/api/v1/academic/student-profiles/{data['prof_stu_b_id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_other.status_code == 403
    assert "Students may only inspect their own academic records" in res_other.text


def test_student_cannot_record_attendance_or_create_coursework(client: TestClient, security_setup: dict):
    """Verify that students lack permissions to record attendance or create coursework (403 Forbidden)."""
    data = security_setup
    token_a = _get_token(client, data["stu_a_email"])
    headers = {"Authorization": f"Bearer {token_a}"}

    # Attempt to record attendance
    res_att = client.post(
        "/api/v1/academic/attendance",
        json={
            "student_id": data["prof_stu_a_id"],
            "course_id": data["course_a"].id,
            "term_id": data["term"].id,
            "session_date": "2026-09-10",
            "session_slot": "SLOT_1",
            "status": "PRESENT",
        },
        headers=headers,
    )
    assert res_att.status_code == 403

    # Attempt to create assignment
    res_asg = client.post(
        "/api/v1/academic/assignments",
        json={
            "course_id": data["course_a"].id,
            "term_id": data["term"].id,
            "title": "Unauthorized Student Assignment",
            "max_marks": 50.0,
            "release_date": "2026-09-01T09:00:00Z",
            "due_date": "2026-09-15T23:59:59Z",
        },
        headers=headers,
    )
    assert res_asg.status_code == 403


def test_faculty_cannot_manage_unassigned_course(client: TestClient, security_setup: dict):
    """Verify that Faculty A cannot manage attendance or create assignments for Faculty B's course (403 Forbidden)."""
    data = security_setup
    token_fac_a = _get_token(client, data["fac_a_email"])
    headers = {"Authorization": f"Bearer {token_fac_a}"}

    # Faculty A attempts to create assignment for Course B (which is assigned only to Faculty B)
    res_asg = client.post(
        "/api/v1/academic/assignments",
        json={
            "course_id": data["course_b"].id,  # Unassigned to Faculty A!
            "term_id": data["term"].id,
            "title": "Intruder Assignment",
            "max_marks": 50.0,
            "release_date": "2026-09-01T09:00:00Z",
            "due_date": "2026-09-15T23:59:59Z",
        },
        headers=headers,
    )
    assert res_asg.status_code == 403
    assert "Faculty member is not assigned to this course offering" in res_asg.text

    # Faculty A attempts to record attendance for Course B
    res_att = client.post(
        "/api/v1/academic/attendance",
        json={
            "student_id": data["prof_stu_b_id"],
            "course_id": data["course_b"].id,  # Unassigned!
            "term_id": data["term"].id,
            "session_date": "2026-09-10",
            "session_slot": "SLOT_1",
            "status": "PRESENT",
        },
        headers=headers,
    )
    assert res_att.status_code == 403


def test_admin_has_institutional_oversight(client: TestClient, security_setup: dict):
    """Verify that institutional Admin can inspect all courses and enrollments."""
    data = security_setup
    token_admin = _get_token(client, data["admin_email"])
    headers = {"Authorization": f"Bearer {token_admin}"}

    res_courses = client.get("/api/v1/academic/courses", headers=headers)
    assert res_courses.status_code == 200
    assert len(res_courses.json()) >= 2

    res_enr = client.get("/api/v1/academic/enrollments", headers=headers)
    assert res_enr.status_code == 200
    assert len(res_enr.json()) >= 2
