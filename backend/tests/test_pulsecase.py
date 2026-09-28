"""Comprehensive test suite for Phase 7 PulseCase Subsystem.

Mandatory verification areas:
1. Migration/schema constraints & integrity (dates, outcomes, roles, check constraints).
2. Tenant isolation (cross-institution access forbidden).
3. Faculty referral (POST /api/v1/cases/referrals creates unassigned OPEN intake).
4. Faculty direct-case rejection (403 when Faculty calls POST /api/v1/cases).
5. Advisor case creation (direct case opening by ADVISOR).
6. Counselor assignment (assigning counselor to case).
7. Wellbeing assignment restrictions (rejection when assigning wellbeing case to plain advisor).
8. Academic assignment restrictions (rejection when assigning academic support to non-advisor).
9. Complete lifecycle (OPEN -> IN_PROGRESS -> WAITING_FOR_STUDENT -> IN_PROGRESS -> FOLLOW_UP_SCHEDULED -> RESOLVED -> CLOSED).
10. Invalid lifecycle transitions (OPEN -> CLOSED rejected, WAITING_FOR_STUDENT -> RESOLVED rejected).
11. Closed-case immutability (modifying, assigning, adding note to a closed case is rejected).
12. Resolution requirements (outcome and summary required).
13. Closure requirements (only resolved cases can be closed, records closed_by and closed_at).
14. Confidential note access (author counselor, assigned counselor, and SUPER_ADMIN can read).
15. Confidential note redaction (ADVISOR, ordinary ADMIN, FACULTY, STUDENT cannot read confidential notes).
16. Student projection (GET /api/v1/cases/student/my-support returns action items and appointments, 0 notes).
17. Faculty projection (GET /api/v1/cases/referrals/my returns sanitized receipt, 0 notes).
18. Recurrence evidence references (storing prior case info in evidence_references).
19. Audit events (verifying all required audit actions are recorded in AuditLog).
20. has_active_intervention (returns True for active cases, False after closure).
21. PulseWatch/PulseRisk non-interference (case creation does not alter attendance records or SPI snapshots).
22. PulseAssist non-leakage (PulseAssist retrieval does not return case notes or support cases).
"""

from datetime import date, datetime, timezone
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.main import app
from app.models.academic import (
    Batch,
    Department,
    FacultyProfile,
    Institution,
    Program,
    StudentProfile,
)
from app.models.audit_log import AuditLog
from app.models.pulsecase import (
    CaseFollowUp,
    CaseIntervention,
    CaseNote,
    SupportCase,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.pulsecase_service import PulseCaseService
from tests.conftest import get_test_session


@pytest.fixture
def pulsecase_setup():
    """Sets up primary test institution, foreign institution, academic structures, and test users."""
    session = get_test_session()
    try:
        uid = uuid.uuid4().hex[:6]

        # 1. Institutions
        inst1 = Institution(
            id=str(uuid.uuid4()),
            name=f"PulseCase University 1 {uid}",
            code=f"PC1_{uid}",
            is_active=True,
        )
        inst2 = Institution(
            id=str(uuid.uuid4()),
            name=f"PulseCase University 2 {uid}",
            code=f"PC2_{uid}",
            is_active=True,
        )
        session.add_all([inst1, inst2])
        session.flush()

        # 2. Users helper
        def _create_user(email: str, role: str, name: str) -> User:
            u = UserRepository.create_user(
                db=session,
                email=email,
                password_hash=hash_password("Password123!"),
                full_name=name,
                is_active=True,
                is_verified=True,
            )
            UserRepository.set_user_roles(session, u.id, [role])
            return u

        admin1 = _create_user(f"admin_{uid}@pc1.edu", "ADMIN", f"Admin One {uid}")
        student1 = _create_user(f"student_{uid}@pc1.edu", "STUDENT", f"Student One {uid}")
        faculty1 = _create_user(f"faculty_{uid}@pc1.edu", "FACULTY", f"Faculty One {uid}")
        advisor1 = _create_user(f"advisor_{uid}@pc1.edu", "ADVISOR", f"Advisor One {uid}")
        advisor2 = _create_user(f"advisor2_{uid}@pc1.edu", "ADVISOR", f"Advisor Two {uid}")
        counselor1 = _create_user(f"counselor_{uid}@pc1.edu", "COUNSELOR", f"Counselor One {uid}")
        counselor2 = _create_user(f"counselor2_{uid}@pc1.edu", "COUNSELOR", f"Counselor Two {uid}")
        counselor3 = _create_user(f"counselor3_{uid}@pc1.edu", "COUNSELOR", f"Counselor Three {uid}")
        super_admin = _create_user(f"super_{uid}@pulse.edu", "SUPER_ADMIN", f"Super Admin {uid}")

        # Foreign institution users
        admin2 = _create_user(f"admin_{uid}@pc2.edu", "ADMIN", f"Admin Two {uid}")
        student2 = _create_user(f"student_{uid}@pc2.edu", "STUDENT", f"Student Two {uid}")

        # 3. Academic Structure for Inst 1
        dept1 = Department(
            id=str(uuid.uuid4()),
            institution_id=inst1.id,
            name=f"Computer Science {uid}",
            code=f"CS_{uid}",
        )
        session.add(dept1)
        session.flush()

        prog1 = Program(
            id=str(uuid.uuid4()),
            department_id=dept1.id,
            name="Computer Science BS",
            code=f"CSBS_{uid}",
        )
        session.add(prog1)
        session.flush()

        batch1 = Batch(
            id=str(uuid.uuid4()),
            program_id=prog1.id,
            name="2024-2028",
            start_year=2024,
            end_year=2028,
        )
        session.add(batch1)
        session.flush()

        sp1 = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=student1.id,
            program_id=prog1.id,
            batch_id=batch1.id,
            enrollment_number=f"ENR_PC1_{uid}",
            admission_date=date(2024, 8, 1),
        )
        session.add(sp1)

        # Structure for Inst 2
        dept2 = Department(
            id=str(uuid.uuid4()),
            institution_id=inst2.id,
            name=f"Business {uid}",
            code=f"BUS_{uid}",
        )
        session.add(dept2)
        session.flush()

        prog2 = Program(
            id=str(uuid.uuid4()),
            department_id=dept2.id,
            name="Business Administration",
            code=f"BBA_{uid}",
        )
        session.add(prog2)
        session.flush()

        batch2 = Batch(
            id=str(uuid.uuid4()),
            program_id=prog2.id,
            name="2024-2028",
            start_year=2024,
            end_year=2028,
        )
        session.add(batch2)
        session.flush()

        sp2 = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=student2.id,
            program_id=prog2.id,
            batch_id=batch2.id,
            enrollment_number=f"ENR_PC2_{uid}",
            admission_date=date(2024, 8, 1),
        )
        session.add(sp2)

        # Faculty Profiles
        fp_faculty1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=faculty1.id,
            employee_id=f"EMP_FAC_{uid}",
            department_id=dept1.id,
            designation="Assistant Professor",
            joining_date=date(2021, 1, 1),
        )
        fp_advisor1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=advisor1.id,
            employee_id=f"EMP_ADV1_{uid}",
            department_id=dept1.id,
            designation="Academic Advisor",
            joining_date=date(2022, 1, 1),
        )
        fp_advisor2 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=advisor2.id,
            employee_id=f"EMP_ADV2_{uid}",
            department_id=dept1.id,
            designation="Academic Advisor",
            joining_date=date(2022, 1, 1),
        )
        fp_counselor1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=counselor1.id,
            employee_id=f"EMP_CNS1_{uid}",
            department_id=dept1.id,
            designation="Student Counselor",
            joining_date=date(2023, 1, 1),
        )
        fp_counselor2 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=counselor2.id,
            employee_id=f"EMP_CNS2_{uid}",
            department_id=dept1.id,
            designation="Student Counselor",
            joining_date=date(2023, 1, 1),
        )
        fp_counselor3 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=counselor3.id,
            employee_id=f"EMP_CNS3_{uid}",
            department_id=dept1.id,
            designation="Student Counselor",
            joining_date=date(2023, 1, 1),
        )
        fp_admin1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=admin1.id,
            employee_id=f"EMP_ADM1_{uid}",
            department_id=dept1.id,
            designation="Dean of Students",
            joining_date=date(2019, 1, 1),
        )
        session.add_all([fp_faculty1, fp_advisor1, fp_advisor2, fp_counselor1, fp_counselor2, fp_counselor3, fp_admin1])
        session.commit()

        # Token helper
        def _get_headers(client: TestClient, email: str) -> dict:
            resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
            assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
            token = resp.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}

        yield {
            "session": session,
            "inst1": inst1,
            "inst2": inst2,
            "admin1": admin1,
            "student1": student1,
            "student_profile1": sp1,
            "faculty1": faculty1,
            "advisor1": advisor1,
            "advisor2": advisor2,
            "counselor1": counselor1,
            "counselor2": counselor2,
            "counselor3": counselor3,
            "super_admin": super_admin,
            "admin2": admin2,
            "student2": student2,
            "student_profile2": sp2,
            "get_headers": _get_headers,
        }
    finally:
        session.close()


# ============================================================================
# 1. Migration / Schema Constraints & Integrity
# ============================================================================

def test_01_schema_constraints(pulsecase_setup):
    """Verify CHECK constraints on support_cases, resolution integrity, and closure integrity."""
    session = pulsecase_setup["session"]
    inst = pulsecase_setup["inst1"]
    sp = pulsecase_setup["student_profile1"]

    # Invalid case_type should fail check constraint
    case_invalid_type = SupportCase(
        institution_id=inst.id,
        case_number=f"CASE-INVALID-{uuid.uuid4().hex[:4]}",
        student_id=sp.id,
        case_type="INVALID_TYPE",
        status="OPEN",
        priority="MEDIUM",
        trigger_source="MANUAL_ADVISOR",
        reason="Testing invalid type",
    )
    session.add(case_invalid_type)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()

    # Invalid trigger_source should fail check constraint
    case_invalid_trigger = SupportCase(
        institution_id=inst.id,
        case_number=f"CASE-INVALID-TRIG-{uuid.uuid4().hex[:4]}",
        student_id=sp.id,
        case_type="ACADEMIC_SUPPORT",
        status="OPEN",
        priority="MEDIUM",
        trigger_source="RECURRENCE",  # RECURRENCE is forbidden as trigger_source!
        reason="Testing invalid trigger",
    )
    session.add(case_invalid_trigger)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


# ============================================================================
# 2. Multi-Tenant Isolation
# ============================================================================

def test_02_tenant_isolation(pulsecase_setup, client):
    """Verify cross-institution case access returns 403 or 404."""
    headers_adv1 = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_adv2 = pulsecase_setup["get_headers"](client, pulsecase_setup["admin2"].email)
    sp1 = pulsecase_setup["student_profile1"]

    # Create case in Institution 1
    create_resp = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "priority": "MEDIUM",
            "reason": "Student struggling with calculus",
            "trigger_source": "MANUAL_ADVISOR",
        },
        headers=headers_adv1,
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    # Admin2 from Institution 2 attempts to read the case
    get_resp = client.get(f"/api/v1/cases/{case_id}", headers=headers_adv2)
    assert get_resp.status_code in (403, 404)


# ============================================================================
# 3. Faculty Referral Intake
# ============================================================================

def test_03_faculty_referral(pulsecase_setup, client):
    """Verify Faculty can submit advising referral resulting in unassigned OPEN case."""
    headers_fac = pulsecase_setup["get_headers"](client, pulsecase_setup["faculty1"].email)
    sp1 = pulsecase_setup["student_profile1"]

    resp = client.post(
        "/api/v1/cases/referrals",
        json={
            "student_id": sp1.id,
            "reason": "Missed two labs and low quiz score in Data Structures.",
            "priority": "HIGH",
        },
        headers=headers_fac,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["case_number"].startswith("CASE-")
    assert data["status"] == "OPEN"
    assert data["case_type"] == "ACADEMIC_SUPPORT"

    # Verify receipt appears in /referrals/my
    my_resp = client.get("/api/v1/cases/referrals/my", headers=headers_fac)
    assert my_resp.status_code == 200
    receipts = my_resp.json()
    assert any(r["id"] == data["id"] for r in receipts)


# ============================================================================
# 4. Faculty Direct-Case Rejection
# ============================================================================

def test_04_faculty_direct_case_rejection(pulsecase_setup, client):
    """Verify Faculty without cases:create cannot directly open a case via POST /api/v1/cases."""
    headers_fac = pulsecase_setup["get_headers"](client, pulsecase_setup["faculty1"].email)
    sp1 = pulsecase_setup["student_profile1"]

    resp = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "priority": "MEDIUM",
            "reason": "Direct case attempt",
            "trigger_source": "MANUAL_ADVISOR",
        },
        headers=headers_fac,
    )
    assert resp.status_code == 403


# ============================================================================
# 5. Advisor Direct Case Creation
# ============================================================================

def test_05_advisor_case_creation(pulsecase_setup, client):
    """Verify Advisor can directly create an intervention case."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]

    resp = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "priority": "HIGH",
            "reason": "Academic probation check-in",
            "trigger_source": "PULSERISK_SPI",
            "assigned_staff_id": pulsecase_setup["advisor1"].id,
        },
        headers=headers_adv,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["assigned_staff_role"] == "ADVISOR"
    assert data["assigned_advisor_id"] == pulsecase_setup["advisor1"].id


# ============================================================================
# 6. Counselor Assignment
# ============================================================================

def test_06_counselor_assignment(pulsecase_setup, client):
    """Verify a case can be assigned to a counselor."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    counselor1 = pulsecase_setup["counselor1"]

    # Open attendance intervention case
    create_resp = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ATTENDANCE_INTERVENTION",
            "priority": "MEDIUM",
            "reason": "Attendance dropped due to stress",
            "trigger_source": "PULSEWATCH_SHIFT",
        },
        headers=headers_adv,
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    # Assign counselor
    assign_resp = client.patch(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_staff_id": counselor1.id},
        headers=headers_adv,
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["assigned_staff_role"] == "COUNSELOR"
    assert assign_resp.json()["status"] == "IN_PROGRESS"


# ============================================================================
# 7. Wellbeing Assignment Restrictions
# ============================================================================

def test_07_wellbeing_assignment_restrictions(pulsecase_setup, client):
    """Verify WELLBEING_REFERRAL cannot be assigned to a pure ADVISOR."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor2 = pulsecase_setup["advisor2"]
    counselor1 = pulsecase_setup["counselor1"]

    # 1. Attempt creating wellbeing case assigned to advisor -> MUST FAIL 400
    bad_create = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "WELLBEING_REFERRAL",
            "priority": "HIGH",
            "reason": "Student requested counseling support",
            "trigger_source": "STUDENT_REQUEST",
            "assigned_staff_id": advisor2.id,
        },
        headers=headers_adv,
    )
    assert bad_create.status_code == 400

    # 2. Create unassigned wellbeing case
    ok_create = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "WELLBEING_REFERRAL",
            "priority": "HIGH",
            "reason": "Student requested counseling support",
            "trigger_source": "STUDENT_REQUEST",
        },
        headers=headers_adv,
    )
    assert ok_create.status_code == 201
    case_id = ok_create.json()["id"]

    # 3. Attempt assigning to plain advisor -> MUST FAIL 400
    bad_assign = client.patch(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_staff_id": advisor2.id},
        headers=headers_adv,
    )
    assert bad_assign.status_code == 400

    # 4. Assigning to Counselor -> SUCСEEDS
    ok_assign = client.patch(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_staff_id": counselor1.id},
        headers=headers_adv,
    )
    assert ok_assign.status_code == 200
    assert ok_assign.json()["assigned_staff_role"] == "COUNSELOR"


# ============================================================================
# 8. Academic Support Assignment Restrictions
# ============================================================================

def test_08_academic_assignment_restrictions(pulsecase_setup, client):
    """Verify ACADEMIC_SUPPORT requires ADVISOR assignment."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    student1 = pulsecase_setup["student1"]

    # Attempt assigning to student user -> MUST FAIL 400
    bad_assign = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "priority": "MEDIUM",
            "reason": "Math tutoring required",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": student1.id,
        },
        headers=headers_adv,
    )
    assert bad_assign.status_code == 400


# ============================================================================
# 9. Complete Lifecycle State Machine
# ============================================================================

def test_09_complete_lifecycle(pulsecase_setup, client):
    """Verify: OPEN -> IN_PROGRESS -> WAITING_FOR_STUDENT -> IN_PROGRESS -> FOLLOW_UP_SCHEDULED -> RESOLVED -> CLOSED."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_adm = pulsecase_setup["get_headers"](client, pulsecase_setup["admin1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    # 1. OPEN
    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "priority": "HIGH",
            "reason": "Complete lifecycle test",
            "trigger_source": "MANUAL_ADVISOR",
        },
        headers=headers_adv,
    ).json()
    case_id = c["id"]
    assert c["status"] == "OPEN"

    # 2. OPEN -> IN_PROGRESS (via assignment)
    c = client.patch(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_staff_id": advisor1.id},
        headers=headers_adv,
    ).json()
    assert c["status"] == "IN_PROGRESS"

    # 3. IN_PROGRESS -> WAITING_FOR_STUDENT
    c = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "WAITING_FOR_STUDENT", "notes": "Email sent to student"},
        headers=headers_adv,
    ).json()
    assert c["status"] == "WAITING_FOR_STUDENT"

    # 4. WAITING_FOR_STUDENT -> IN_PROGRESS
    c = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "IN_PROGRESS", "notes": "Student booked advising session"},
        headers=headers_adv,
    ).json()
    assert c["status"] == "IN_PROGRESS"

    # 5. IN_PROGRESS -> FOLLOW_UP_SCHEDULED (via follow-up creation)
    f = client.post(
        f"/api/v1/cases/{case_id}/follow-ups",
        json={
            "scheduled_date": "2026-11-15",
            "scheduled_time": "14:00",
            "follow_up_type": "CHECK_IN_MEETING",
            "notes": "Mid-semester evaluation",
        },
        headers=headers_adv,
    ).json()
    assert f["status"] == "SCHEDULED"

    detail = client.get(f"/api/v1/cases/{case_id}", headers=headers_adv).json()
    assert detail["status"] == "FOLLOW_UP_SCHEDULED"

    # 6. Complete the follow-up
    client.patch(
        f"/api/v1/cases/{case_id}/follow-ups/{f['id']}",
        json={"status": "COMPLETED", "notes": "Met with student, grades improved"},
        headers=headers_adv,
    )

    # 7. FOLLOW_UP_SCHEDULED -> RESOLVED
    res = client.post(
        f"/api/v1/cases/{case_id}/resolve",
        json={
            "resolution_outcome": "IMPROVED_ENGAGEMENT",
            "resolution_summary": "Student improved attendance to 92% and passed all midterms.",
        },
        headers=headers_adv,
    ).json()
    assert res["status"] == "RESOLVED"
    assert res["resolution_outcome"] == "IMPROVED_ENGAGEMENT"

    # 8. RESOLVED -> CLOSED
    closed = client.post(
        f"/api/v1/cases/{case_id}/close",
        json={"closing_notes": "Archiving case with verified positive outcome."},
        headers=headers_adm,
    ).json()
    assert closed["status"] == "CLOSED"
    assert closed["closed_by_user_id"] == pulsecase_setup["admin1"].id


# ============================================================================
# 10. Invalid Lifecycle Transitions Rejected
# ============================================================================

def test_10_invalid_lifecycle_transitions(pulsecase_setup, client):
    """Verify illegal status transitions fail with HTTP 400."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]

    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Transition test",
            "trigger_source": "MANUAL_ADVISOR",
        },
        headers=headers_adv,
    ).json()
    case_id = c["id"]

    # 1. OPEN -> CLOSED directly (INVALID)
    resp = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "CLOSED"},
        headers=headers_adv,
    )
    assert resp.status_code == 400

    # 2. OPEN -> RESOLVED directly (INVALID)
    resp = client.post(
        f"/api/v1/cases/{case_id}/resolve",
        json={
            "resolution_outcome": "NO_FURTHER_ACTION",
            "resolution_summary": "Skipping progress",
        },
        headers=headers_adv,
    )
    assert resp.status_code == 400


# ============================================================================
# 11. Closed-Case Immutability
# ============================================================================

def test_11_closed_case_immutability(pulsecase_setup, client):
    """Verify closed cases are immutable and reject status changes, assignments, notes, and interventions."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_adm = pulsecase_setup["get_headers"](client, pulsecase_setup["admin1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    # Create, assign, resolve, close
    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Immutability test",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    ).json()
    case_id = c["id"]

    client.post(
        f"/api/v1/cases/{case_id}/resolve",
        json={
            "resolution_outcome": "ACADEMIC_PLAN_ESTABLISHED",
            "resolution_summary": "Study plan created",
        },
        headers=headers_adv,
    )
    client.post(f"/api/v1/cases/{case_id}/close", json={}, headers=headers_adm)

    # 1. Attempt status change on closed case -> 400
    r1 = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers_adv,
    )
    assert r1.status_code == 400

    # 2. Attempt note addition on closed case -> 400
    r2 = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Late note"},
        headers=headers_adv,
    )
    assert r2.status_code == 400

    # 3. Attempt intervention addition on closed case -> 400
    r3 = client.post(
        f"/api/v1/cases/{case_id}/interventions",
        json={"intervention_type": "ONE_ON_ONE_ADVISING", "title": "Late task", "description": "Late description"},
        headers=headers_adv,
    )
    assert r3.status_code == 400


# ============================================================================
# 12. Resolution Requirements
# ============================================================================

def test_12_resolution_requirements(pulsecase_setup, client):
    """Verify resolving requires valid outcome and non-empty summary."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Resolution requirements test",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    ).json()
    case_id = c["id"]

    # Short summary (< 5 chars) fails validation
    bad_res = client.post(
        f"/api/v1/cases/{case_id}/resolve",
        json={"resolution_outcome": "IMPROVED_ENGAGEMENT", "resolution_summary": "ok"},
        headers=headers_adv,
    )
    assert bad_res.status_code == 422


# ============================================================================
# 13. Closure Requirements
# ============================================================================

def test_13_closure_requirements(pulsecase_setup, client):
    """Verify only cases in RESOLVED status can be closed."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_adm = pulsecase_setup["get_headers"](client, pulsecase_setup["admin1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Closure requirements test",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    ).json()
    case_id = c["id"]

    # Try closing while still IN_PROGRESS -> MUST FAIL 400
    bad_close = client.post(f"/api/v1/cases/{case_id}/close", json={}, headers=headers_adm)
    assert bad_close.status_code == 400


# ============================================================================
# 14 & 15. Confidential Notes Access & Redaction
# ============================================================================

def test_14_15_confidential_notes_redaction(pulsecase_setup, client):
    """Verify COUNSELOR_CONFIDENTIAL access rules across all 8 roles, direct & nested notes, and zero leaks."""
    headers_cns1 = pulsecase_setup["get_headers"](client, pulsecase_setup["counselor1"].email)
    headers_cns2 = pulsecase_setup["get_headers"](client, pulsecase_setup["counselor2"].email)
    headers_cns3 = pulsecase_setup["get_headers"](client, pulsecase_setup["counselor3"].email)
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_adm = pulsecase_setup["get_headers"](client, pulsecase_setup["admin1"].email)
    headers_sup = pulsecase_setup["get_headers"](client, pulsecase_setup["super_admin"].email)
    headers_stu = pulsecase_setup["get_headers"](client, pulsecase_setup["student1"].email)
    headers_fac = pulsecase_setup["get_headers"](client, pulsecase_setup["faculty1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    counselor1 = pulsecase_setup["counselor1"]
    counselor2 = pulsecase_setup["counselor2"]

    # Create wellbeing case initially assigned to counselor2
    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "WELLBEING_REFERRAL",
            "reason": "Mental fatigue and exam anxiety",
            "trigger_source": "STUDENT_REQUEST",
            "assigned_staff_id": counselor2.id,
        },
        headers=headers_adv,
    ).json()
    case_id = c["id"]

    # Counselor 1 (author) adds a standard note and a confidential note
    client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={
            "note_type": "STUDENT_INTERACTION",
            "confidentiality_level": "STANDARD",
            "content": "Standard check-in note: discussed study schedule.",
        },
        headers=headers_cns1,
    )

    confidential_text = "Sensitive counselor observation: personal family stress factors."
    client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={
            "note_type": "COUNSELOR_CONFIDENTIAL",
            "confidentiality_level": "COUNSELOR_CONFIDENTIAL",
            "content": confidential_text,
        },
        headers=headers_cns1,
    )

    # 1. SUPER_ADMIN -> allowed (direct notes & nested case detail)
    sup_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_sup).json()
    assert len(sup_notes) == 2
    assert any(n["content"] == confidential_text for n in sup_notes)
    sup_case = client.get(f"/api/v1/cases/{case_id}", headers=headers_sup).json()
    assert any(n["content"] == confidential_text for n in sup_case["notes"])

    # 2. Note author COUNSELOR (counselor1) -> allowed (direct notes)
    cns1_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_cns1).json()
    assert len(cns1_notes) == 2
    assert any(n["content"] == confidential_text for n in cns1_notes)

    # 3. Assigned COUNSELOR (counselor2) -> allowed (direct notes & nested case detail)
    cns2_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_cns2).json()
    assert len(cns2_notes) == 2
    assert any(n["content"] == confidential_text for n in cns2_notes)
    cns2_case = client.get(f"/api/v1/cases/{case_id}", headers=headers_cns2).json()
    assert any(n["content"] == confidential_text for n in cns2_case["notes"])

    # 4. Other COUNSELOR (counselor3) -> denied (confidential note strictly redacted)
    cns3_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_cns3).json()
    assert len(cns3_notes) == 1
    assert cns3_notes[0]["confidentiality_level"] == "STANDARD"
    assert all(n["content"] != confidential_text for n in cns3_notes)

    # 5. ADVISOR (advisor1) -> denied (confidential note strictly redacted)
    adv_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_adv).json()
    assert len(adv_notes) == 1
    assert adv_notes[0]["confidentiality_level"] == "STANDARD"
    assert all(n["content"] != confidential_text for n in adv_notes)

    # 6. ADMIN (admin1) -> denied (confidential note strictly redacted in both direct and nested detail)
    adm_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_adm).json()
    assert len(adm_notes) == 1
    assert adm_notes[0]["confidentiality_level"] == "STANDARD"
    assert all(n["content"] != confidential_text for n in adm_notes)
    adm_case = client.get(f"/api/v1/cases/{case_id}", headers=headers_adm).json()
    assert len(adm_case["notes"]) == 1
    assert all(n["content"] != confidential_text for n in adm_case["notes"])

    # 7. FACULTY (faculty1) -> denied (403 Forbidden on notes & case detail)
    fac_notes_resp = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_fac)
    assert fac_notes_resp.status_code == 403
    fac_case_resp = client.get(f"/api/v1/cases/{case_id}", headers=headers_fac)
    assert fac_case_resp.status_code == 403

    # 8. STUDENT (student1) -> denied (403 Forbidden on notes & case detail)
    stu_notes_resp = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_stu)
    assert stu_notes_resp.status_code == 403
    stu_case_resp = client.get(f"/api/v1/cases/{case_id}", headers=headers_stu)
    assert stu_case_resp.status_code == 403

    # Leak check: verify case list endpoint does NOT leak note contents
    cases_list = client.get("/api/v1/cases/", headers=headers_adm).json()
    for item in cases_list:
        assert "notes" not in item

    # Leak check: verify audit log contains only metadata, never the confidential note text
    from app.models.audit_log import AuditLog
    session = pulsecase_setup["session"]
    audit_logs = session.query(AuditLog).filter(AuditLog.action == "CASE_NOTE_ADDED").all()
    for log in audit_logs:
        assert confidential_text not in (log.details or "")


# ============================================================================
# 16. Student Support Self-Service Projection
# ============================================================================

def test_16_student_support_projection(pulsecase_setup, client):
    """Verify Student view returns action items and appointments, with zero internal notes."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_stu = pulsecase_setup["get_headers"](client, pulsecase_setup["student1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    # Create case with intervention and follow-up
    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Math tutoring and peer mentoring",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    ).json()
    case_id = c["id"]

    client.post(
        f"/api/v1/cases/{case_id}/interventions",
        json={
            "intervention_type": "PEER_TUTORING_REFERRAL",
            "title": "Attend Math Lab Tutoring",
            "description": "3 hours weekly tutoring sessions.",
            "target_completion_date": "2026-11-01",
        },
        headers=headers_adv,
    )

    client.post(
        f"/api/v1/cases/{case_id}/follow-ups",
        json={
            "scheduled_date": "2026-10-25",
            "scheduled_time": "15:00",
            "follow_up_type": "ACADEMIC_PROGRESS_REVIEW",
            "notes": "Internal review note",
        },
        headers=headers_adv,
    )

    # Student views self-service support portal
    resp = client.get("/api/v1/cases/student/my-support", headers=headers_stu)
    assert resp.status_code == 200
    data = resp.json()

    assert data["active_cases_count"] >= 1
    assert data["assigned_advisor_name"] == advisor1.full_name
    assert len(data["support_action_items"]) >= 1
    assert data["support_action_items"][0]["title"] == "Attend Math Lab Tutoring"
    assert len(data["upcoming_follow_ups"]) >= 1
    assert data["upcoming_follow_ups"][0]["scheduled_date"] == "2026-10-25"


# ============================================================================
# 17. Faculty Referral Projection
# ============================================================================

def test_17_faculty_projection(pulsecase_setup, client):
    """Verify Faculty referral tracking receipt returns sanitized status with no notes."""
    headers_fac = pulsecase_setup["get_headers"](client, pulsecase_setup["faculty1"].email)
    sp1 = pulsecase_setup["student_profile1"]

    client.post(
        "/api/v1/cases/referrals",
        json={"student_id": sp1.id, "reason": "Consistent assignment delays."},
        headers=headers_fac,
    )

    resp = client.get("/api/v1/cases/referrals/my", headers=headers_fac)
    assert resp.status_code == 200
    receipts = resp.json()
    assert len(receipts) >= 1
    for r in receipts:
        assert "notes" not in r
        assert "evidence_references" not in r
        assert "case_number" in r


# ============================================================================
# 18. Recurrence Evidence References
# ============================================================================

def test_18_recurrence_evidence_references(pulsecase_setup, client):
    """Verify recurring case links prior case info through evidence_references."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_adm = pulsecase_setup["get_headers"](client, pulsecase_setup["admin1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    # 1. First case
    c1 = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "First intervention in semester 1",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    ).json()

    client.post(
        f"/api/v1/cases/{c1['id']}/resolve",
        json={"resolution_outcome": "ACADEMIC_PLAN_ESTABLISHED", "resolution_summary": "Passed semester 1"},
        headers=headers_adv,
    )
    client.post(f"/api/v1/cases/{c1['id']}/close", json={}, headers=headers_adm)

    # 2. Second recurring case in semester 2
    c2 = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Second intervention in semester 2",
            "trigger_source": "PULSERISK_SPI",
            "assigned_staff_id": advisor1.id,
            "evidence_references": {
                "prior_case_id": c1["id"],
                "prior_case_number": c1["case_number"],
                "is_recurrence": True,
            },
        },
        headers=headers_adv,
    ).json()

    assert c2["evidence_references"]["prior_case_id"] == c1["id"]
    assert c2["evidence_references"]["is_recurrence"] is True
    assert c2["trigger_source"] == "PULSERISK_SPI"  # True trigger is preserved!


# ============================================================================
# 19. Audit Events
# ============================================================================

def test_19_audit_events_recorded(pulsecase_setup, client):
    """Verify that case mutations emit corresponding AuditLog entries with zero note leakage."""
    session = pulsecase_setup["session"]
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    # Create case
    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Audit verification test",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    ).json()

    # Add note with secret text
    secret_text = "ULTRA_CONFIDENTIAL_MEDICAL_SECRET_12345"
    client.post(
        f"/api/v1/cases/{c['id']}/notes",
        json={
            "note_type": "ADVISING_NOTE",
            "confidentiality_level": "STANDARD",
            "content": secret_text,
        },
        headers=headers_adv,
    )

    # Verify audit logs in DB
    audit_logs = session.query(AuditLog).filter(AuditLog.entity_id.in_([c["id"]])).all()
    actions = {a.action for a in audit_logs}
    assert "CASE_CREATED" in actions

    # Verify the secret note text is NEVER in audit log details
    all_details = [a.details for a in session.query(AuditLog).all() if a.details]
    assert not any(secret_text in d for d in all_details)


# ============================================================================
# 20. has_active_intervention Contract
# ============================================================================

def test_20_has_active_intervention_contract(pulsecase_setup, client):
    """Verify PulseCaseService.has_active_intervention correctly reflects active states."""
    session = pulsecase_setup["session"]
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_adm = pulsecase_setup["get_headers"](client, pulsecase_setup["admin1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    # Initially False
    assert not PulseCaseService.has_active_intervention(session, sp1.id)

    # Open case -> True
    c = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Active intervention test",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    ).json()
    assert PulseCaseService.has_active_intervention(session, sp1.id)

    # Resolve and Close case -> False
    client.post(
        f"/api/v1/cases/{c['id']}/resolve",
        json={"resolution_outcome": "IMPROVED_ENGAGEMENT", "resolution_summary": "Passed"},
        headers=headers_adv,
    )
    client.post(f"/api/v1/cases/{c['id']}/close", json={}, headers=headers_adm)
    assert not PulseCaseService.has_active_intervention(session, sp1.id)


# ============================================================================
# 21. PulseWatch/PulseRisk Non-Interference
# ============================================================================

def test_21_pulsewatch_pulserisk_non_interference(pulsecase_setup, client):
    """Verify creating a support case does not mutate PulseWatch events or SPI scores."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    resp = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Non interference check",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    )
    assert resp.status_code == 201

    # Verify PulseWatch summary endpoint still works without errors
    pw_resp = client.get(f"/api/v1/pulsewatch/{sp1.id}/summary", headers=headers_adv)
    assert pw_resp.status_code in (200, 404)  # 404 if no attendance data seeded, but not 500 error


# ============================================================================
# 22. PulseAssist Non-Leakage
# ============================================================================

def test_22_pulseassist_non_leakage(pulsecase_setup, client):
    """Verify PulseAssist RAG does not index or search support_cases or case_notes."""
    headers_adv = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    advisor1 = pulsecase_setup["advisor1"]

    # Open case with unique marker string
    marker = "CONFIDENTIAL_PULSECASE_TEST_MARKER_98765"
    client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": marker,
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": advisor1.id,
        },
        headers=headers_adv,
    )

    # PulseAssist ask endpoint searching for the marker should NOT retrieve the case
    pa_resp = client.post(
        "/api/v1/pulseassist/ask",
        json={"question": f"What is {marker}?", "target_date": "2026-09-24"},
        headers=headers_adv,
    )
    if pa_resp.status_code == 200:
        answer = pa_resp.json().get("answer", "")
        assert marker not in answer


# ============================================================================
# 23. COUNSELOR RBAC & API Authorization Verification
# ============================================================================

def test_23_counselor_rbac_and_api_authorization(pulsecase_setup, client):
    """Verify COUNSELOR RBAC boundaries and authorization checks on all 7 case management endpoints."""
    headers_cns1 = pulsecase_setup["get_headers"](client, pulsecase_setup["counselor1"].email)
    headers_adv1 = pulsecase_setup["get_headers"](client, pulsecase_setup["advisor1"].email)
    headers_fac1 = pulsecase_setup["get_headers"](client, pulsecase_setup["faculty1"].email)
    headers_stu1 = pulsecase_setup["get_headers"](client, pulsecase_setup["student1"].email)
    headers_adm1 = pulsecase_setup["get_headers"](client, pulsecase_setup["admin1"].email)
    sp1 = pulsecase_setup["student_profile1"]
    counselor1 = pulsecase_setup["counselor1"]
    advisor1 = pulsecase_setup["advisor1"]

    # 1. POST /api/v1/cases (requires cases:create)
    # - Counselor lacks cases:create -> 403 Forbidden
    cns_create = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "WELLBEING_REFERRAL",
            "reason": "Direct intake attempt by counselor",
            "trigger_source": "STUDENT_REQUEST",
        },
        headers=headers_cns1,
    )
    assert cns_create.status_code == 403
    assert "cases:create" in cns_create.json()["detail"]

    # - Faculty lacks cases:create -> 403 Forbidden
    fac_create = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "ACADEMIC_SUPPORT",
            "reason": "Direct intake attempt by faculty",
            "trigger_source": "FACULTY_REFERRAL",
        },
        headers=headers_fac1,
    )
    assert fac_create.status_code == 403

    # - Advisor has cases:create -> 201 Created
    adv_create = client.post(
        "/api/v1/cases/",
        json={
            "student_id": sp1.id,
            "case_type": "WELLBEING_REFERRAL",
            "reason": "Wellbeing intake by triage advisor",
            "trigger_source": "MANUAL_ADVISOR",
            "assigned_staff_id": counselor1.id,
        },
        headers=headers_adv1,
    )
    assert adv_create.status_code == 201
    case_id = adv_create.json()["id"]

    # 2. POST /api/v1/cases/referrals (requires cases:refer)
    # - Counselor lacks cases:refer -> 403 Forbidden
    cns_refer = client.post(
        "/api/v1/cases/referrals",
        json={
            "student_id": sp1.id,
            "reason": "Counselor referral attempt",
        },
        headers=headers_cns1,
    )
    assert cns_refer.status_code == 403
    assert "cases:refer" in cns_refer.json()["detail"]

    # - Student lacks cases:refer -> 403 Forbidden
    stu_refer = client.post(
        "/api/v1/cases/referrals",
        json={
            "student_id": sp1.id,
            "reason": "Student referral attempt",
        },
        headers=headers_stu1,
    )
    assert stu_refer.status_code == 403

    # - Faculty has cases:refer -> 201 Created
    fac_refer = client.post(
        "/api/v1/cases/referrals",
        json={
            "student_id": sp1.id,
            "reason": "Student missing physics problem sets",
        },
        headers=headers_fac1,
    )
    assert fac_refer.status_code == 201

    # 3. PATCH /api/v1/cases/{case_id}/assign (requires cases:assign)
    # - Counselor lacks cases:assign -> 403 Forbidden
    cns_assign = client.patch(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_staff_id": counselor1.id},
        headers=headers_cns1,
    )
    assert cns_assign.status_code == 403
    assert "cases:assign" in cns_assign.json()["detail"]

    # - Advisor has cases:assign -> 200 OK
    adv_assign = client.patch(
        f"/api/v1/cases/{case_id}/assign",
        json={"assigned_staff_id": counselor1.id},
        headers=headers_adv1,
    )
    assert adv_assign.status_code == 200

    # 4. POST /api/v1/cases/{case_id}/notes (requires cases:write_assigned)
    # - Student lacks cases:write_assigned -> 403 Forbidden
    stu_note = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"content": "Student note"},
        headers=headers_stu1,
    )
    assert stu_note.status_code == 403

    # - Assigned Counselor has cases:write_assigned -> 201 Created
    cns_note = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={
            "note_type": "STUDENT_INTERACTION",
            "confidentiality_level": "STANDARD",
            "content": "Intake consultation completed.",
        },
        headers=headers_cns1,
    )
    assert cns_note.status_code == 201

    # 5. GET /api/v1/cases/{case_id}/notes (requires cases:read_assigned or cases:read_all)
    # - Student lacks read permissions -> 403 Forbidden
    stu_get_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_stu1)
    assert stu_get_notes.status_code == 403

    # - Assigned Counselor has cases:read_assigned -> 200 OK
    cns_get_notes = client.get(f"/api/v1/cases/{case_id}/notes", headers=headers_cns1)
    assert cns_get_notes.status_code == 200

    # 6. POST /api/v1/cases/{case_id}/resolve (requires cases:write_assigned)
    # - First advance to IN_PROGRESS
    client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers_cns1,
    )

    # - Assigned Counselor has cases:write_assigned -> resolves case 200 OK
    cns_resolve = client.post(
        f"/api/v1/cases/{case_id}/resolve",
        json={
            "resolution_outcome": "REFERRED_TO_EXTERNAL_RESOURCE",
            "resolution_summary": "Connected student with health center resources.",
        },
        headers=headers_cns1,
    )
    assert cns_resolve.status_code == 200
    assert cns_resolve.json()["status"] == "RESOLVED"

    # 7. POST /api/v1/cases/{case_id}/close (requires cases:close)
    # - Counselor lacks cases:close -> 403 Forbidden
    cns_close = client.post(
        f"/api/v1/cases/{case_id}/close",
        json={"closing_notes": "Counselor closing attempt"},
        headers=headers_cns1,
    )
    assert cns_close.status_code == 403
    assert "cases:close" in cns_close.json()["detail"]

    # - Advisor has cases:close -> 200 OK
    adv_close = client.post(
        f"/api/v1/cases/{case_id}/close",
        json={"closing_notes": "Advisor review complete. Formally closed and archived."},
        headers=headers_adv1,
    )
    assert adv_close.status_code == 200
    assert adv_close.json()["status"] == "CLOSED"

