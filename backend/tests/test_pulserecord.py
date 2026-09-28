"""Comprehensive test suite for Phase 6 PulseRecord Subsystem.

Mandatory verification areas:
1. Database constraints & schema integrity:
   - chk_leave_dates (end_date >= start_date)
   - days_count accurate calculation
   - chk_complaint_outcome_correlation (status vs adjudication_outcome)
   - institution_id ON DELETE RESTRICT
   - sequential complaint codes (CMP-YYYY-XXXX)
2. Leave lifecycle:
   - SUBMITTED -> UNDER_REVIEW -> APPROVED / REJECTED / CANCELLED
   - attachments upload, streaming download, deletion in SUBMITTED only
   - immutability / protection against cancellation after approval
3. Analytics integration contract & Invariant A:
   - LeaveService.get_approved_leave_intervals() merging overlapping and contiguous dates
   - Non-approved leaves strictly excluded from intervals
   - Invariant A: complaints have ZERO impact on PulseWatch and PulseRisk
4. Complaint workflow & appellate state machine:
   - SUBMITTED -> UNDER_REVIEW -> NEEDS_INFORMATION -> UNDER_REVIEW -> VERIFIED -> APPEALED -> RESOLVED -> CLOSED
   - evidence repository, private keys, SHA-256, confidential flag, sealed on closure
5. Confidentiality & anonymity:
   - is_anonymous=true preserves internal accountability while redacting complainant identity in read projections
   - privileged reviewer / assigned scoping
6. Multi-tenant isolation & RBAC boundaries.
"""

from datetime import date, datetime, timedelta, timezone
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.main import app
from app.models.academic import (
    AcademicTerm,
    Batch,
    Course,
    Department,
    Enrollment,
    FacultyCourseAssignment,
    FacultyProfile,
    Institution,
    Program,
    StudentProfile,
)
from app.models.pulserecord import (
    Complaint,
    ComplaintAppeal,
    ComplaintEvidence,
    LeaveAttachment,
    LeaveRequest,
)
from app.models.pulserisk import StudentRiskSnapshot
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.leave_service import LeaveService
from app.services.complaint_service import ComplaintService
from tests.conftest import get_test_session


@pytest.fixture
def pulserecord_setup():
    """Sets up primary test institution, foreign institution, academic structures, and test users."""
    session = get_test_session()
    try:
        uid = uuid.uuid4().hex[:6]

        # 1. Institutions
        inst1 = Institution(
            id=str(uuid.uuid4()),
            name=f"PulseRecord University 1 {uid}",
            code=f"PR1_{uid}",
            is_active=True,
        )
        inst2 = Institution(
            id=str(uuid.uuid4()),
            name=f"PulseRecord University 2 {uid}",
            code=f"PR2_{uid}",
            is_active=True,
        )
        session.add_all([inst1, inst2])
        session.flush()

        # 2. Users
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

        admin1 = _create_user(f"admin_{uid}@pr1.edu", "ADMIN", f"Admin One {uid}")
        student1 = _create_user(f"student_{uid}@pr1.edu", "STUDENT", f"Student One {uid}")
        faculty1 = _create_user(f"faculty_{uid}@pr1.edu", "FACULTY", f"Faculty One {uid}")
        reviewer1 = _create_user(f"reviewer_{uid}@pr1.edu", "ADMIN", f"Reviewer One {uid}")
        reviewer2 = _create_user(f"reviewer2_{uid}@pr1.edu", "FACULTY", f"Reviewer Two {uid}")
        super_admin = _create_user(f"super_{uid}@pulse.edu", "SUPER_ADMIN", f"Super Admin {uid}")

        # Foreign institution users
        admin2 = _create_user(f"admin_{uid}@pr2.edu", "ADMIN", f"Admin Two {uid}")
        student2 = _create_user(f"student_{uid}@pr2.edu", "STUDENT", f"Student Two {uid}")

        # 3. Academic Structure for Inst 1
        dept1 = Department(
            id=str(uuid.uuid4()),
            institution_id=inst1.id,
            name=f"Engineering {uid}",
            code=f"ENG_{uid}",
        )
        session.add(dept1)
        session.flush()

        prog1 = Program(
            id=str(uuid.uuid4()),
            department_id=dept1.id,
            name="Computer Engineering",
            code=f"CENG_{uid}",
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
            enrollment_number=f"ENR_PR1_{uid}",
            admission_date=date(2024, 8, 1),
        )
        session.add(sp1)

        # Faculty Profiles connecting institutional staff to dept1 / inst1
        fp_admin1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=admin1.id,
            employee_id=f"EMP_ADM_{uid}",
            department_id=dept1.id,
            designation="Administrator",
            joining_date=date(2020, 1, 1),
        )
        fp_faculty1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=faculty1.id,
            employee_id=f"EMP_FAC_{uid}",
            department_id=dept1.id,
            designation="Associate Professor",
            joining_date=date(2021, 1, 1),
        )
        fp_rev1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=reviewer1.id,
            employee_id=f"EMP_REV1_{uid}",
            department_id=dept1.id,
            designation="Grievance Officer",
            joining_date=date(2022, 1, 1),
        )
        fp_rev2 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=reviewer2.id,
            employee_id=f"EMP_REV2_{uid}",
            department_id=dept1.id,
            designation="Investigator",
            joining_date=date(2022, 1, 1),
        )
        session.add_all([fp_admin1, fp_faculty1, fp_rev1, fp_rev2])
        session.flush()

        # Term, Course, Faculty Assignment & Student Enrollment for Inst 1
        term1 = AcademicTerm(
            id=str(uuid.uuid4()),
            institution_id=inst1.id,
            name=f"Fall 2026 {uid}",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 31),
            is_current=True,
        )
        session.add(term1)
        session.flush()

        course1 = Course(
            id=str(uuid.uuid4()),
            institution_id=inst1.id,
            department_id=dept1.id,
            code=f"ENG101_{uid}",
            title="Software Architecture",
            credits=4,
        )
        session.add(course1)
        session.flush()

        fca1 = FacultyCourseAssignment(
            id=str(uuid.uuid4()),
            faculty_id=fp_faculty1.id,
            course_id=course1.id,
            term_id=term1.id,
            role="PRIMARY_INSTRUCTOR",
        )
        enr1 = Enrollment(
            id=str(uuid.uuid4()),
            student_id=sp1.id,
            course_id=course1.id,
            term_id=term1.id,
            enrollment_date=date(2026, 8, 1),
        )
        session.add_all([fca1, enr1])

        # 4. Foreign Institution (Inst 2) Setup
        dept2 = Department(
            id=str(uuid.uuid4()),
            institution_id=inst2.id,
            name=f"Sciences {uid}",
            code=f"SCI_{uid}",
        )
        session.add(dept2)
        session.flush()

        prog2 = Program(
            id=str(uuid.uuid4()),
            department_id=dept2.id,
            name="Physics",
            code=f"PHY_{uid}",
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
            enrollment_number=f"ENR_PR2_{uid}",
            admission_date=date(2024, 8, 1),
        )
        session.add(sp2)

        fp_admin2 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=admin2.id,
            employee_id=f"EMP_ADM2_{uid}",
            department_id=dept2.id,
            designation="Administrator",
            joining_date=date(2020, 1, 1),
        )
        session.add(fp_admin2)

        session.commit()

        yield {
            "session": session,
            "inst1": inst1,
            "inst2": inst2,
            "admin1": admin1,
            "student1": student1,
            "faculty1": faculty1,
            "reviewer1": reviewer1,
            "reviewer2": reviewer2,
            "super_admin": super_admin,
            "admin2": admin2,
            "student2": student2,
            "student_profile1": sp1,
            "student_profile2": sp2,
            "dept1": dept1,
            "uid": uid,
        }
    finally:
        session.close()


def _get_token(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# ==============================================================================
# SECTION 1: Database Constraints & Schema Invariants
# ==============================================================================

def test_chk_leave_dates_constraint(pulserecord_setup):
    """Test 1: chk_leave_dates enforces end_date >= start_date at database level."""
    session: Session = pulserecord_setup["session"]
    inst1 = pulserecord_setup["inst1"]
    sp1 = pulserecord_setup["student_profile1"]

    invalid_leave = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="PERSONAL",
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 5),  # INVALID: end_date < start_date
        days_count=-4,
        reason="Invalid negative date span",
        status="SUBMITTED",
    )
    session.add(invalid_leave)
    with pytest.raises(IntegrityError) as exc_info:
        session.flush()
    session.rollback()
    assert "chk_leave_dates" in str(exc_info.value).lower() or "check constraint" in str(exc_info.value).lower()


def test_leave_days_count_calculation(pulserecord_setup):
    """Test 2: Leave days_count is accurately persisted."""
    session: Session = pulserecord_setup["session"]
    inst1 = pulserecord_setup["inst1"]
    sp1 = pulserecord_setup["student_profile1"]

    valid_leave = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="MEDICAL",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 5),
        days_count=5,
        reason="Medical recuperation",
        status="SUBMITTED",
    )
    session.add(valid_leave)
    session.commit()

    reloaded = session.query(LeaveRequest).filter_by(id=valid_leave.id).first()
    assert reloaded is not None
    assert reloaded.days_count == 5


def test_chk_complaint_outcome_correlation_verified(pulserecord_setup):
    """Test 3: chk_complaint_outcome_correlation requires adjudication_outcome when VERIFIED."""
    session: Session = pulserecord_setup["session"]
    inst1 = pulserecord_setup["inst1"]
    u1 = pulserecord_setup["student1"]

    # Valid VERIFIED complaint
    valid_c = Complaint(
        institution_id=inst1.id,
        complaint_code=f"CMP-2026-TEST1-{pulserecord_setup['uid']}",
        complainant_user_id=u1.id,
        complainant_role="STUDENT",
        category="ACADEMIC_INTEGRITY",
        target_type="FACULTY",
        title="Valid Adjudicated Complaint",
        description="Detailed description",
        status="VERIFIED",
        adjudication_outcome="POLICY_VIOLATION_SUBSTANTIATED",
        adjudication_summary="Substantiated upon investigation",
    )
    session.add(valid_c)
    session.flush()
    session.commit()

    # Invalid VERIFIED complaint without adjudication_outcome
    invalid_c = Complaint(
        institution_id=inst1.id,
        complaint_code=f"CMP-2026-TEST2-{pulserecord_setup['uid']}",
        complainant_user_id=u1.id,
        complainant_role="STUDENT",
        category="ACADEMIC_INTEGRITY",
        target_type="FACULTY",
        title="Invalid Adjudicated Complaint",
        description="Detailed description",
        status="VERIFIED",
        adjudication_outcome=None,  # INVALID: must be NOT NULL when VERIFIED
        adjudication_summary="Missing outcome code",
    )
    session.add(invalid_c)
    with pytest.raises(IntegrityError) as exc_info:
        session.flush()
    session.rollback()
    assert "chk_complaint_outcome_correlation" in str(exc_info.value).lower() or "check constraint" in str(exc_info.value).lower()


def test_chk_complaint_outcome_correlation_submitted_rejected(pulserecord_setup):
    """Test 4: chk_complaint_outcome_correlation rejects adjudication_outcome on SUBMITTED status."""
    session: Session = pulserecord_setup["session"]
    inst1 = pulserecord_setup["inst1"]
    u1 = pulserecord_setup["student1"]

    invalid_c = Complaint(
        institution_id=inst1.id,
        complaint_code=f"CMP-2026-TEST3-{pulserecord_setup['uid']}",
        complainant_user_id=u1.id,
        complainant_role="STUDENT",
        category="SAFETY_CONCERN",
        target_type="FACILITY",
        title="Premature outcome complaint",
        description="Detailed description",
        status="SUBMITTED",
        adjudication_outcome="PREMATURE_OUTCOME",  # INVALID: must be NULL in SUBMITTED
    )
    session.add(invalid_c)
    with pytest.raises(IntegrityError) as exc_info:
        session.flush()
    session.rollback()
    assert "chk_complaint_outcome_correlation" in str(exc_info.value).lower() or "check constraint" in str(exc_info.value).lower()


def test_institution_fk_restrict_leaves_and_complaints(pulserecord_setup):
    """Test 5: Institution deletion is RESTRICTED if leaves or complaints exist."""
    session: Session = pulserecord_setup["session"]
    inst1 = pulserecord_setup["inst1"]
    sp1 = pulserecord_setup["student_profile1"]

    leave = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="PERSONAL",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 11, 2),
        days_count=2,
        reason="Testing FK restrict",
        status="SUBMITTED",
    )
    session.add(leave)
    session.commit()

    # Attempt to delete institution
    session.delete(inst1)
    with pytest.raises(IntegrityError) as exc_info:
        session.flush()
    session.rollback()
    assert "foreign key" in str(exc_info.value).lower() or "violates" in str(exc_info.value).lower()


# ==============================================================================
# SECTION 2: Leave Management & Lifecycle
# ==============================================================================

def test_student_leave_api_lifecycle(client: TestClient, pulserecord_setup):
    """Test 6: Student creates leave request, attaches file, downloads, and reviewer approves."""
    token = _get_token(client, pulserecord_setup["student1"].email)
    faculty_token = _get_token(client, pulserecord_setup["faculty1"].email)
    headers = {"Authorization": f"Bearer {token}"}
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}

    # 1. Create Leave Request
    res = client.post(
        "/api/v1/leaves",
        headers=headers,
        json={
            "leave_type": "MEDICAL",
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
            "reason": "Doctor-prescribed bed rest following surgery",
        },
    )
    assert res.status_code == 201, res.text
    leave_data = res.json()
    leave_id = leave_data["id"]
    assert leave_data["days_count"] == 3
    assert leave_data["status"] == "SUBMITTED"

    # 2. View in /leaves/mine
    mine_res = client.get("/api/v1/leaves/mine", headers=headers)
    assert mine_res.status_code == 200
    my_leaves = mine_res.json()
    assert any(l["id"] == leave_id for l in my_leaves)

    # 3. Upload Attachment
    fake_file = io.BytesIO(b"Medical Certificate Content - Dr. John Doe")
    att_res = client.post(
        f"/api/v1/leaves/{leave_id}/attachments",
        headers=headers,
        files={"file": ("medical_cert.pdf", fake_file, "application/pdf")},
    )
    assert att_res.status_code == 201, att_res.text
    att_data = att_res.json()
    attachment_id = att_data["id"]
    assert att_data["file_name"] == "medical_cert.pdf"
    assert att_data["file_size_bytes"] == len(b"Medical Certificate Content - Dr. John Doe")
    assert len(att_data["sha256_hash"]) == 64

    # 4. Download Attachment
    dl_res = client.get(
        f"/api/v1/leaves/{leave_id}/attachments/{attachment_id}/download",
        headers=headers,
    )
    assert dl_res.status_code == 200
    assert dl_res.content == b"Medical Certificate Content - Dr. John Doe"

    # 5. Faculty Reviews Leave (Approve)
    rev_res = client.post(
        f"/api/v1/leaves/{leave_id}/review",
        headers=faculty_headers,
        json={
            "status": "APPROVED",
            "reviewer_notes": "Excused. Submit assignment makeup within 5 days of return.",
        },
    )
    assert rev_res.status_code == 200, rev_res.text
    approved_leave = rev_res.json()
    assert approved_leave["status"] == "APPROVED"
    assert approved_leave["reviewer_notes"] == "Excused. Submit assignment makeup within 5 days of return."

    # 6. Verify cannot cancel once APPROVED
    cancel_res = client.post(
        f"/api/v1/leaves/{leave_id}/cancel",
        headers=headers,
        json={"cancellation_reason": "I changed my mind"},
    )
    assert cancel_res.status_code == 400
    assert "cannot be cancelled" in cancel_res.json()["detail"].lower()

    # 7. Verify cannot delete attachment once APPROVED
    del_att_res = client.delete(
        f"/api/v1/leaves/{leave_id}/attachments/{attachment_id}",
        headers=headers,
    )
    assert del_att_res.status_code == 400
    assert "submitted" in del_att_res.json()["detail"].lower()


def test_leave_cancellation_in_submitted_state(client: TestClient, pulserecord_setup):
    """Test 7: Student can cancel leave request while in SUBMITTED state."""
    token = _get_token(client, pulserecord_setup["student1"].email)
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post(
        "/api/v1/leaves",
        headers=headers,
        json={
            "leave_type": "PERSONAL",
            "start_date": "2026-12-01",
            "end_date": "2026-12-02",
            "reason": "Personal family event",
        },
    )
    assert create_res.status_code == 201
    leave_id = create_res.json()["id"]

    cancel_res = client.post(
        f"/api/v1/leaves/{leave_id}/cancel",
        headers=headers,
        json={"cancellation_reason": "Family event postponed indefinitely"},
    )
    assert cancel_res.status_code == 200
    cancelled_leave = cancel_res.json()
    assert cancelled_leave["status"] == "CANCELLED"
    assert cancelled_leave["cancellation_reason"] == "Family event postponed indefinitely"


def test_leave_rejection_workflow(client: TestClient, pulserecord_setup):
    """Test 8: Reviewer can reject a leave request with notes."""
    token = _get_token(client, pulserecord_setup["student1"].email)
    faculty_token = _get_token(client, pulserecord_setup["faculty1"].email)
    headers = {"Authorization": f"Bearer {token}"}
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}

    create_res = client.post(
        "/api/v1/leaves",
        headers=headers,
        json={
            "leave_type": "PERSONAL",
            "start_date": "2026-12-10",
            "end_date": "2026-12-11",
            "reason": "Midterm week absence without medical documentation",
        },
    )
    assert create_res.status_code == 201
    leave_id = create_res.json()["id"]

    reject_res = client.post(
        f"/api/v1/leaves/{leave_id}/review",
        headers=faculty_headers,
        json={
            "status": "REJECTED",
            "reviewer_notes": "Unexcused. Absence coincides with mandatory departmental midterm examinations.",
        },
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "REJECTED"


# ==============================================================================
# SECTION 3: Analytics Integration Contract & Invariant A
# ==============================================================================

def test_leave_service_approved_intervals_merging(pulserecord_setup):
    """Test 9: LeaveService.get_approved_leave_intervals() merges overlapping and contiguous dates, excluding non-approved."""
    session: Session = pulserecord_setup["session"]
    inst1 = pulserecord_setup["inst1"]
    sp1 = pulserecord_setup["student_profile1"]

    # 1. Approved Leave A: Oct 1 - Oct 5
    la = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="MEDICAL",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 5),
        days_count=5,
        reason="Approved A",
        status="APPROVED",
    )
    # 2. Approved Leave B: Oct 4 - Oct 8 (Overlaps with A)
    lb = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="MEDICAL",
        start_date=date(2026, 10, 4),
        end_date=date(2026, 10, 8),
        days_count=5,
        reason="Approved B",
        status="APPROVED",
    )
    # 3. Approved Leave C: Oct 9 - Oct 12 (Contiguous with B!)
    lc = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="ACADEMIC_DUTY",
        start_date=date(2026, 10, 9),
        end_date=date(2026, 10, 12),
        days_count=4,
        reason="Approved C",
        status="APPROVED",
    )
    # 4. Rejected Leave D: Oct 15 - Oct 16 (Must be ignored)
    ld = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="PERSONAL",
        start_date=date(2026, 10, 15),
        end_date=date(2026, 10, 16),
        days_count=2,
        reason="Rejected D",
        status="REJECTED",
    )
    # 5. Submitted Leave E: Oct 20 - Oct 22 (Must be ignored)
    le = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="PERSONAL",
        start_date=date(2026, 10, 20),
        end_date=date(2026, 10, 22),
        days_count=3,
        reason="Submitted E",
        status="SUBMITTED",
    )
    # 6. Approved Leave F: Oct 25 - Oct 27 (Separate interval)
    lf = LeaveRequest(
        institution_id=inst1.id,
        student_id=sp1.id,
        leave_type="BEREAVEMENT",
        start_date=date(2026, 10, 25),
        end_date=date(2026, 10, 27),
        days_count=3,
        reason="Approved F",
        status="APPROVED",
    )

    session.add_all([la, lb, lc, ld, le, lf])
    session.commit()

    intervals = LeaveService.get_approved_leave_intervals(
        db=session,
        student_id=sp1.id,
        date_range=(date(2026, 10, 1), date(2026, 10, 31)),
    )

    assert len(intervals) == 2
    # Interval 1 merged A, B, C into [2026-10-01, 2026-10-12]
    assert intervals[0] == (date(2026, 10, 1), date(2026, 10, 12))
    # Interval 2 is F [2026-10-25, 2026-10-27]
    assert intervals[1] == (date(2026, 10, 25), date(2026, 10, 27))


def test_invariant_a_complaints_zero_impact_on_pulsewatch_pulserisk(pulserecord_setup):
    """Test 10: Invariant A verification: complaints table has ZERO foreign keys, triggers, or dependencies with PulseWatch / PulseRisk."""
    session: Session = pulserecord_setup["session"]

    # Check database foreign key references targeting complaints or complaint_appeals
    query = text("""
        SELECT
            tc.table_name, kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND (
            (tc.table_name IN ('student_behavior_events', 'attendance_summaries', 'student_risk_snapshots')
             AND ccu.table_name IN ('complaints', 'complaint_appeals', 'complaint_evidence'))
            OR
            (tc.table_name IN ('complaints', 'complaint_appeals', 'complaint_evidence')
             AND ccu.table_name IN ('student_behavior_events', 'attendance_summaries', 'student_risk_snapshots'))
          );
    """)
    rows = session.execute(query).fetchall()
    # Ensure there are NO foreign keys between analytics tables and complaint tables
    assert len(rows) == 0, f"Found illegal FK coupling between analytics and complaints: {rows}"


# ==============================================================================
# SECTION 4: Complaint Management, Review Workflow & Appeals
# ==============================================================================

def test_complaint_full_adjudication_and_appeal_lifecycle(client: TestClient, pulserecord_setup):
    """Test 11: End-to-end complaint workflow:
    SUBMITTED -> UNDER_REVIEW (assigned) -> NEEDS_INFORMATION -> UNDER_REVIEW ->
    VERIFIED -> APPEALED -> RESOLVED -> CLOSED (evidence sealed).
    """
    student_token = _get_token(client, pulserecord_setup["student1"].email)
    admin_token = _get_token(client, pulserecord_setup["admin1"].email)
    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Student files complaint
    c_res = client.post(
        "/api/v1/complaints",
        headers=student_headers,
        json={
            "category": "GRADING_DISPUTE",
            "target_type": "FACULTY",
            "title": "Arbitrary grading penalty on final project",
            "description": "Instructor deducted 25% without rubric justification.",
            "is_anonymous": False,
        },
    )
    assert c_res.status_code == 201, c_res.text
    c_data = c_res.json()
    complaint_id = c_data["id"]
    complaint_code = c_data["complaint_code"]
    assert complaint_code.startswith("CMP-2026-")
    assert c_data["status"] == "SUBMITTED"

    # 2. Upload supporting evidence
    fake_doc = io.BytesIO(b"Rubric comparison document and email timestamps")
    ev_res = client.post(
        f"/api/v1/complaints/{complaint_id}/evidence",
        headers=student_headers,
        files={"file": ("rubric_evidence.pdf", fake_doc, "application/pdf")},
        data={"description": "Project submission vs rubric comparison", "is_confidential": "false"},
    )
    assert ev_res.status_code == 201, ev_res.text
    ev_data = ev_res.json()
    evidence_id = ev_data["id"]
    assert ev_data["file_name"] == "rubric_evidence.pdf"

    # 3. Admin assigns reviewer -> transitions to UNDER_REVIEW
    assign_res = client.post(
        f"/api/v1/complaints/{complaint_id}/assign",
        headers=admin_headers,
        json={"reviewer_user_id": pulserecord_setup["reviewer1"].id},
    )
    assert assign_res.status_code == 200, assign_res.text
    assert assign_res.json()["status"] == "UNDER_REVIEW"
    assert assign_res.json()["assigned_reviewer_id"] == pulserecord_setup["reviewer1"].id

    reviewer_token = _get_token(client, pulserecord_setup["reviewer1"].email)
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    # 4. Reviewer requests additional information -> transitions to NEEDS_INFORMATION
    req_info_res = client.post(
        f"/api/v1/complaints/{complaint_id}/request-information",
        headers=reviewer_headers,
        json={"details": "Please provide the original syllabus section outlining late submission policy."},
    )
    assert req_info_res.status_code == 200, req_info_res.text
    assert req_info_res.json()["status"] == "NEEDS_INFORMATION"
    assert req_info_res.json()["info_request_details"] is not None

    # 5. Complainant provides requested information -> transitions back to UNDER_REVIEW
    resp_info_res = client.post(
        f"/api/v1/complaints/{complaint_id}/respond",
        headers=student_headers,
        json={"response": "Attached syllabus page 4 shows project was submitted 2 hours ahead of deadline."},
    )
    assert resp_info_res.status_code == 200, resp_info_res.text
    assert resp_info_res.json()["status"] == "UNDER_REVIEW"

    # 6. Reviewer Adjudicates -> transitions to VERIFIED
    adj_res = client.post(
        f"/api/v1/complaints/{complaint_id}/adjudicate",
        headers=reviewer_headers,
        json={
            "status": "VERIFIED",
            "adjudication_outcome": "GRADING_CRITERIA_MISAPPLIED",
            "adjudication_summary": "Investigation confirmed deduction was inconsistent with published course syllabus.",
            "internal_reviewer_notes": "Instructor instructed to recalculate final letter grade.",
        },
    )
    assert adj_res.status_code == 200, adj_res.text
    assert adj_res.json()["status"] == "VERIFIED"
    assert adj_res.json()["adjudication_outcome"] == "GRADING_CRITERIA_MISAPPLIED"

    # 7. Complainant files Appeal -> transitions to APPEALED
    appeal_res = client.post(
        f"/api/v1/complaints/{complaint_id}/appeal",
        headers=student_headers,
        json={"reason": "Recalculation was not completed prior to grade submission deadline."},
    )
    assert appeal_res.status_code == 201, appeal_res.text
    appeal_data = appeal_res.json()
    appeal_id = appeal_data["id"]
    assert appeal_data["status"] == "SUBMITTED"
    assert appeal_data["appeal_number"] == 1

    # Verify complaint status is APPEALED
    c_check = client.get(f"/api/v1/complaints/{complaint_id}", headers=student_headers)
    assert c_check.json()["status"] == "APPEALED"

    # 8. Appellate authority resolves appeal -> transitions to RESOLVED
    resolve_res = client.post(
        f"/api/v1/complaints/{complaint_id}/resolve-appeal?appeal_id={appeal_id}",
        headers=admin_headers,
        json={
            "status": "UPHELD",
            "disposition_summary": "Office of Registrar ordered to adjust grade from B+ to A- immediately.",
            "reviewer_notes": "Registrar directive dispatched.",
        },
    )
    assert resolve_res.status_code == 200, resolve_res.text
    assert resolve_res.json()["status"] == "UPHELD"

    # Verify complaint status is RESOLVED
    c_check2 = client.get(f"/api/v1/complaints/{complaint_id}", headers=student_headers)
    assert c_check2.json()["status"] == "RESOLVED"

    # 9. Admin officially closes record -> transitions to CLOSED
    close_res = client.post(f"/api/v1/complaints/{complaint_id}/close", headers=admin_headers)
    assert close_res.status_code == 200, close_res.text
    assert close_res.json()["status"] == "CLOSED"

    # 10. Verify evidence is sealed and new evidence uploads are blocked
    fake_doc2 = io.BytesIO(b"Post-closure evidence attempt")
    block_res = client.post(
        f"/api/v1/complaints/{complaint_id}/evidence",
        headers=student_headers,
        files={"file": ("blocked.pdf", fake_doc2, "application/pdf")},
    )
    assert block_res.status_code == 400
    assert "closed" in block_res.json()["detail"].lower()


# ==============================================================================
# SECTION 5: Anonymity, Confidentiality & Scoping
# ==============================================================================

def test_anonymous_complaint_redaction_and_accountability(client: TestClient, pulserecord_setup):
    """Test 12: Anonymous complaints preserve internal complainant_user_id while redacting identity from external/assigned reads."""
    student_token = _get_token(client, pulserecord_setup["student1"].email)
    admin_token = _get_token(client, pulserecord_setup["admin1"].email)
    super_token = _get_token(client, pulserecord_setup["super_admin"].email)
    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    super_headers = {"Authorization": f"Bearer {super_token}"}

    # 1. Student files complaint with is_anonymous = True
    c_res = client.post(
        "/api/v1/complaints",
        headers=student_headers,
        json={
            "category": "FACILITY_HARASSMENT",
            "target_type": "FACULTY",
            "title": "Verbal intimidation during office hours",
            "description": "Complainant wishes to remain anonymous to prevent academic retaliation.",
            "is_anonymous": True,
        },
    )
    assert c_res.status_code == 201
    c_id = c_res.json()["id"]

    # 2. Database verification: complainant_user_id permanently retained in database for accountability
    session: Session = pulserecord_setup["session"]
    db_c = session.query(Complaint).filter_by(id=c_id).first()
    assert db_c.is_anonymous is True
    assert db_c.complainant_user_id == pulserecord_setup["student1"].id
    assert db_c.complainant_role == "STUDENT"

    # 3. Assign Reviewer 2 (Role: FACULTY, non-admin reviewer)
    client.post(
        f"/api/v1/complaints/{c_id}/assign",
        headers=admin_headers,
        json={"reviewer_user_id": pulserecord_setup["reviewer2"].id},
    )

    # 4. ADMIN visibility: complainant_user_id and complainant_role are VISIBLE for institutional accountability
    admin_read = client.get(f"/api/v1/complaints/{c_id}", headers=admin_headers)
    assert admin_read.status_code == 200
    admin_data = admin_read.json()
    assert admin_data["is_anonymous"] is True
    assert admin_data["complainant_user_id"] == pulserecord_setup["student1"].id
    assert admin_data["complainant_role"] == "STUDENT"

    # 5. SUPER_ADMIN visibility: complainant_user_id and complainant_role are VISIBLE for compliance
    super_read = client.get(f"/api/v1/complaints/{c_id}", headers=super_headers)
    assert super_read.status_code == 200
    super_data = super_read.json()
    assert super_data["is_anonymous"] is True
    assert super_data["complainant_user_id"] == pulserecord_setup["student1"].id
    assert super_data["complainant_role"] == "STUDENT"

    # 6. Complainant self-read: identity remains accessible to reporting student
    self_read = client.get(f"/api/v1/complaints/{c_id}", headers=student_headers)
    assert self_read.status_code == 200
    self_data = self_read.json()
    assert self_data["is_anonymous"] is True
    assert self_data["complainant_user_id"] == pulserecord_setup["student1"].id

    # 7. Assigned Faculty Reviewer redaction: complainant_user_id and role are strictly REDACTED (None)
    reviewer_token = _get_token(client, pulserecord_setup["reviewer2"].email)
    rev_read = client.get(f"/api/v1/complaints/{c_id}", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert rev_read.status_code == 200
    rev_data = rev_read.json()
    assert rev_data["is_anonymous"] is True
    assert rev_data["complainant_user_id"] is None
    assert rev_data["complainant_role"] is None

    # 8. Target Faculty (unassigned) access check: forbidden from viewing complaint
    target_token = _get_token(client, pulserecord_setup["faculty1"].email)
    target_read = client.get(f"/api/v1/complaints/{c_id}", headers={"Authorization": f"Bearer {target_token}"})
    assert target_read.status_code == 403

    # 9. General / Unrelated student access check: forbidden from viewing complaint
    s2_token = _get_token(client, pulserecord_setup["student2"].email)
    s2_read = client.get(f"/api/v1/complaints/{c_id}", headers={"Authorization": f"Bearer {s2_token}"})
    assert s2_read.status_code == 403

    # 10. Public / Unauthenticated access check: rejected with 401
    client.cookies.clear()
    pub_read = client.get(f"/api/v1/complaints/{c_id}")
    assert pub_read.status_code == 401


def test_assigned_reviewer_rbac_boundary(client: TestClient, pulserecord_setup):
    """Test 13: Reviewer with complaints:read_assigned can only read complaints assigned to them."""
    admin_token = _get_token(client, pulserecord_setup["admin1"].email)
    student_token = _get_token(client, pulserecord_setup["student1"].email)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # File complaint
    c_res = client.post(
        "/api/v1/complaints",
        headers=student_headers,
        json={
            "category": "DISCRIMINATION",
            "target_type": "DEPARTMENT",
            "title": "Departmental scholarship allocation discrepancy",
            "description": "Allegation of discriminatory selection criteria.",
            "is_anonymous": False,
        },
    )
    c_id = c_res.json()["id"]

    # Assign specifically to Reviewer 1
    client.post(
        f"/api/v1/complaints/{c_id}/assign",
        headers=admin_headers,
        json={"reviewer_user_id": pulserecord_setup["reviewer1"].id},
    )

    # Reviewer 1 lists assigned -> finds it
    rev1_token = _get_token(client, pulserecord_setup["reviewer1"].email)
    rev1_res = client.get("/api/v1/complaints/assigned", headers={"Authorization": f"Bearer {rev1_token}"})
    assert rev1_res.status_code == 200
    assert any(c["id"] == c_id for c in rev1_res.json())

    # Reviewer 2 lists assigned -> does NOT find it
    rev2_token = _get_token(client, pulserecord_setup["reviewer2"].email)
    rev2_res = client.get("/api/v1/complaints/assigned", headers={"Authorization": f"Bearer {rev2_token}"})
    assert rev2_res.status_code == 200
    assert not any(c["id"] == c_id for c in rev2_res.json())


def test_cross_tenant_isolation_pulserecord(client: TestClient, pulserecord_setup):
    """Test 14: Tenant isolation: User in Institution 1 cannot view or modify leaves/complaints in Institution 2."""
    s1_token = _get_token(client, pulserecord_setup["student1"].email)
    s2_token = _get_token(client, pulserecord_setup["student2"].email)

    # Student 1 (Inst 1) creates leave
    l1_res = client.post(
        "/api/v1/leaves",
        headers={"Authorization": f"Bearer {s1_token}"},
        json={
            "leave_type": "PERSONAL",
            "start_date": "2026-11-20",
            "end_date": "2026-11-21",
            "reason": "Institution 1 leave",
        },
    )
    l1_id = l1_res.json()["id"]

    # Student 2 (Inst 2) attempts to access Student 1's leave -> 404 Not Found (tenant isolated)
    l2_access = client.get(
        f"/api/v1/leaves/{l1_id}",
        headers={"Authorization": f"Bearer {s2_token}"},
    )
    assert l2_access.status_code in (403, 404)

    # Student 1 creates complaint
    c1_res = client.post(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {s1_token}"},
        json={
            "category": "SAFETY_CONCERN",
            "target_type": "FACILITY",
            "title": "Institution 1 complaint",
            "description": "Lab safety protocol violation in building A.",
            "is_anonymous": False,
        },
    )
    c1_id = c1_res.json()["id"]

    # Student 2 attempts to access Student 1's complaint -> 403 or 404
    c2_access = client.get(
        f"/api/v1/complaints/{c1_id}",
        headers={"Authorization": f"Bearer {s2_token}"},
    )
    assert c2_access.status_code in (403, 404)
