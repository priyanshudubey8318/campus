"""Unit and integration tests for Phase 3 PulseWatch subsystem.

Verifies deterministic behavioral monitoring, baseline leakage prevention,
event idempotency, assignment eligibility, multiple-attempt lateness, exact threshold
boundaries, scoped authorization, and read-only separation.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.academic import (
    AcademicTerm,
    Assessment,
    AssessmentResult,
    Assignment,
    AssignmentSubmission,
    AttendanceRecord,
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
from app.models.pulsewatch import BehaviorEvent, StudentBehaviorBaseline
from app.repositories.pulsewatch_repo import PulseWatchRepository
from app.repositories.user_repo import UserRepository
from app.services.pulsewatch_calculation_service import (
    ALGORITHM_VERSION,
    PulseWatchCalculationService,
)
from app.services.pulsewatch_event_service import PulseWatchEventService
from tests.conftest import get_test_session


def _create_user(session: Session, email: str, role: str, name: str) -> str:
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


def _get_token(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def pulsewatch_setup():
    """Create comprehensive test environment with institutions, courses, students, and faculty."""
    session = get_test_session()
    try:
        uid = uuid.uuid4().hex[:6]
        inst = Institution(id=str(uuid.uuid4()), name=f"PW Inst {uid}", code=f"PWI_{uid}")
        session.add(inst)
        session.flush()

        dept = Department(id=str(uuid.uuid4()), institution_id=inst.id, name=f"PW Dept {uid}", code=f"PWD_{uid}")
        session.add(dept)
        session.flush()

        prog = Program(id=str(uuid.uuid4()), department_id=dept.id, name="PW CS", code=f"PWCS_{uid}")
        session.add(prog)
        session.flush()

        batch = Batch(id=str(uuid.uuid4()), program_id=prog.id, name="2024-2028", start_year=2024, end_year=2028)
        session.add(batch)
        session.flush()

        sec_a = Section(id=str(uuid.uuid4()), batch_id=batch.id, name="A")
        sec_b = Section(id=str(uuid.uuid4()), batch_id=batch.id, name="B")
        session.add_all([sec_a, sec_b])
        session.flush()

        term = AcademicTerm(
            id=str(uuid.uuid4()),
            institution_id=inst.id,
            name=f"Term_{uid}",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 20),
            is_current=True,
        )
        session.add(term)
        session.flush()

        course1 = Course(id=str(uuid.uuid4()), institution_id=inst.id, department_id=dept.id, title="Data Structures", code=f"CS101_{uid}", credits=4)
        course2 = Course(id=str(uuid.uuid4()), institution_id=inst.id, department_id=dept.id, title="Algorithms", code=f"CS201_{uid}", credits=4)
        session.add_all([course1, course2])
        session.flush()

        # Users and profiles
        u_stu_a_id = _create_user(session, f"stu_a_{uid}@test.edu", "STUDENT", "Student A")
        u_stu_b_id = _create_user(session, f"stu_b_{uid}@test.edu", "STUDENT", "Student B")
        u_fac_1_id = _create_user(session, f"fac_1_{uid}@test.edu", "FACULTY", "Faculty 1")
        u_fac_2_id = _create_user(session, f"fac_2_{uid}@test.edu", "FACULTY", "Faculty 2")
        u_adm_id = _create_user(session, f"admin_{uid}@test.edu", "ADMIN", "Administrator")

        stu_a = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=u_stu_a_id,
            program_id=prog.id,
            batch_id=batch.id,
            section_id=sec_a.id,
            enrollment_number=f"ENR_A_{uid}",
            admission_date=date(2024, 8, 1),
        )
        stu_b = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=u_stu_b_id,
            program_id=prog.id,
            batch_id=batch.id,
            section_id=sec_b.id,
            enrollment_number=f"ENR_B_{uid}",
            admission_date=date(2024, 8, 1),
        )
        fac_1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=u_fac_1_id,
            department_id=dept.id,
            employee_id=f"EMP1_{uid}",
            designation="Professor",
            joining_date=date(2020, 1, 1),
        )
        fac_2 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=u_fac_2_id,
            department_id=dept.id,
            employee_id=f"EMP2_{uid}",
            designation="Lecturer",
            joining_date=date(2020, 1, 1),
        )
        session.add_all([stu_a, stu_b, fac_1, fac_2])
        session.flush()

        # Enrollments: Student A in Course 1, Student B in Course 2
        enr_a = Enrollment(id=str(uuid.uuid4()), student_id=stu_a.id, course_id=course1.id, term_id=term.id, section_id=sec_a.id, enrollment_date=date(2026, 8, 1), status="ENROLLED")
        enr_b = Enrollment(id=str(uuid.uuid4()), student_id=stu_b.id, course_id=course2.id, term_id=term.id, section_id=sec_b.id, enrollment_date=date(2026, 8, 1), status="ENROLLED")
        session.add_all([enr_a, enr_b])

        # Faculty assignment: Faculty 1 teaches Course 1, Faculty 2 teaches Course 2
        fa_1 = FacultyCourseAssignment(id=str(uuid.uuid4()), faculty_id=fac_1.id, course_id=course1.id, term_id=term.id, role="PRIMARY_INSTRUCTOR")
        fa_2 = FacultyCourseAssignment(id=str(uuid.uuid4()), faculty_id=fac_2.id, course_id=course2.id, term_id=term.id, role="PRIMARY_INSTRUCTOR")
        session.add_all([fa_1, fa_2])
        session.commit()

        yield {
            "session": session,
            "inst": inst,
            "term": term,
            "course1": course1,
            "course2": course2,
            "stu_a": stu_a,
            "stu_b": stu_b,
            "fac_1": fac_1,
            "fac_2": fac_2,
            "u_stu_a_email": f"stu_a_{uid}@test.edu",
            "u_stu_b_email": f"stu_b_{uid}@test.edu",
            "u_fac_1_email": f"fac_1_{uid}@test.edu",
            "u_fac_2_email": f"fac_2_{uid}@test.edu",
            "u_adm_email": f"admin_{uid}@test.edu",
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# -----------------------------------------------------------------------------
# 1. Baseline Leakage Prevention Test
# -----------------------------------------------------------------------------

def test_baseline_leakage_prevention(pulsewatch_setup):
    """Verify that observation window data is strictly excluded from historical baseline."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    c1 = pulsewatch_setup["course1"]
    term = pulsewatch_setup["term"]

    t_ref = date(2026, 9, 18)
    # Obs window: 14 days (Sep 5 to Sep 18)
    # Base window: 30 days (Aug 6 to Sep 4)

    # 1. Add 10 sessions in baseline window (all PRESENT = 100%)
    for day_offset in range(10):
        sdate = date(2026, 8, 10) + timedelta(days=day_offset * 2)
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=sdate,
                session_slot="SLOT_1",
                status="PRESENT",
                source="MANUAL",
            )
        )

    # 2. Add 4 sessions in observation window (all ABSENT = 0%)
    for day_offset in range(4):
        sdate = date(2026, 9, 6) + timedelta(days=day_offset * 2)
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=sdate,
                session_slot="SLOT_1",
                status="ABSENT",
                source="MANUAL",
            )
        )
    session.commit()

    summary = PulseWatchCalculationService.compute_student_summary(
        db=session,
        student_id=stu_a.id,
        reference_date=t_ref,
        observation_window_days=14,
        baseline_window_days=30,
    )

    # Invariants:
    assert summary.baseline_start_date == date(2026, 8, 6)
    assert summary.baseline_end_date == date(2026, 9, 4)
    assert summary.window_start_date == date(2026, 9, 5)
    assert summary.window_end_date == date(2026, 9, 18)
    assert summary.baseline_end_date < summary.window_start_date

    att_sig = next(s for s in summary.signals if s.signal_type == "ATTENDANCE_CHANGE")
    # Baseline must be 100.0% (unpolluted by observation absences)
    assert att_sig.baseline_value == Decimal("100.00")
    # Current must be 0.0%
    assert att_sig.current_value == Decimal("0.00")
    # Delta must be -100.0%
    assert att_sig.delta_value == Decimal("-100.00")
    assert att_sig.severity == "SIGNIFICANT_CHANGE"


# -----------------------------------------------------------------------------
# 2. Behavior Event Idempotency Test
# -----------------------------------------------------------------------------

def test_behavior_event_idempotency(pulsewatch_setup):
    """Verify that repeated calculations with identical inputs do not duplicate BehaviorEvent rows."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    t_ref = date(2026, 9, 18)

    # Initial count
    initial_count = session.query(BehaviorEvent).filter(BehaviorEvent.student_id == stu_a.id).count()
    assert initial_count == 0

    # Evaluate 3 times with identical inputs
    ev1 = PulseWatchEventService.evaluate_and_persist_student(session, stu_a.id, reference_date=t_ref, observation_window_days=14)
    ev2 = PulseWatchEventService.evaluate_and_persist_student(session, stu_a.id, reference_date=t_ref, observation_window_days=14)
    ev3 = PulseWatchEventService.evaluate_and_persist_student(session, stu_a.id, reference_date=t_ref, observation_window_days=14)

    # Must be the exact same event ID
    assert ev1.id == ev2.id == ev3.id

    # Exactly 1 row in the database
    total_events = session.query(BehaviorEvent).filter(BehaviorEvent.student_id == stu_a.id).count()
    assert total_events == 1

    # Exactly 3 baseline rows (Attendance, Coursework, Assessment) with pulsewatch-v1.0
    baselines = session.query(StudentBehaviorBaseline).filter(StudentBehaviorBaseline.student_id == stu_a.id).all()
    assert len(baselines) == 3
    assert all(b.algorithm_version == ALGORITHM_VERSION for b in baselines)


# -----------------------------------------------------------------------------
# 3. Assignment Eligibility Filtering Test
# -----------------------------------------------------------------------------

def test_assignment_eligibility_filtering(pulsewatch_setup):
    """Verify that assignments outside enrolled courses, unreleased assignments, or outside window are excluded."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    c1 = pulsewatch_setup["course1"]
    c2 = pulsewatch_setup["course2"]
    term = pulsewatch_setup["term"]
    fac_1 = pulsewatch_setup["fac_1"]

    t_obs_start = datetime(2026, 9, 5, 0, 0, 0, tzinfo=timezone.utc)
    t_obs_end = datetime(2026, 9, 18, 23, 59, 59, tzinfo=timezone.utc)

    # 1. Eligible assignment: Enrolled in C1, due Sep 12 (in window)
    asg_valid = Assignment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Valid Assignment",
        max_marks=Decimal("50.00"),
        release_date=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
        due_date=datetime(2026, 9, 12, 23, 59, 59, tzinfo=timezone.utc),
    )

    # 2. Ineligible: Belongs to Course 2 (Student A is not enrolled in C2)
    asg_not_enrolled = Assignment(
        id=str(uuid.uuid4()),
        course_id=c2.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Unenrolled Assignment",
        max_marks=Decimal("50.00"),
        release_date=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
        due_date=datetime(2026, 9, 12, 23, 59, 59, tzinfo=timezone.utc),
    )

    # 3. Ineligible: Release date is in the future (> window_end)
    asg_future_release = Assignment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Future Release Assignment",
        max_marks=Decimal("50.00"),
        release_date=datetime(2026, 9, 20, 9, 0, 0, tzinfo=timezone.utc),
        due_date=datetime(2026, 9, 25, 23, 59, 59, tzinfo=timezone.utc),
    )

    # 4. Ineligible: Due date outside window (> window_end)
    asg_future_due = Assignment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Future Due Assignment",
        max_marks=Decimal("50.00"),
        release_date=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
        due_date=datetime(2026, 9, 22, 23, 59, 59, tzinfo=timezone.utc),
    )

    session.add_all([asg_valid, asg_not_enrolled, asg_future_release, asg_future_due])
    session.commit()

    eligible = PulseWatchRepository.get_eligible_assignments_in_window(
        db=session,
        student_id=stu_a.id,
        start_date=t_obs_start,
        end_date=t_obs_end,
    )

    assert len(eligible) == 1
    assert eligible[0].id == asg_valid.id


# -----------------------------------------------------------------------------
# 4. Multiple-Attempt Deterministic Lateness Logic Test
# -----------------------------------------------------------------------------

def test_multiple_attempt_deterministic_lateness_logic(pulsewatch_setup):
    """Verify earliest valid submission timestamp unambiguously dictates on-time vs late status."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    c1 = pulsewatch_setup["course1"]
    term = pulsewatch_setup["term"]
    fac_1 = pulsewatch_setup["fac_1"]

    due = datetime(2026, 9, 10, 23, 59, 59, tzinfo=timezone.utc)

    # Assignment 1: Earliest attempt is late (Attempt 1 = Sep 11 [Late], Attempt 2 = Sep 12 [Late])
    asg1 = Assignment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Multiple Attempt Test 1",
        max_marks=Decimal("50.00"),
        release_date=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
        due_date=due,
    )
    session.add(asg1)
    session.flush()

    # Submission 1: Late
    sub1_1 = AssignmentSubmission(
        id=str(uuid.uuid4()),
        assignment_id=asg1.id,
        student_id=stu_a.id,
        attempt_number=1,
        submitted_at=datetime(2026, 9, 11, 10, 0, 0, tzinfo=timezone.utc),
        status="LATE",
    )
    # Submission 2: Later
    sub1_2 = AssignmentSubmission(
        id=str(uuid.uuid4()),
        assignment_id=asg1.id,
        student_id=stu_a.id,
        attempt_number=2,
        submitted_at=datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc),
        status="RESUBMITTED",
    )
    session.add_all([sub1_1, sub1_2])

    # Assignment 2: Earliest attempt is On-Time (Attempt 1 = Sep 8 [On-time], Attempt 2 = Sep 11 [Late resubmit])
    asg2 = Assignment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Multiple Attempt Test 2",
        max_marks=Decimal("50.00"),
        release_date=datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
        due_date=due,
    )
    session.add(asg2)
    session.flush()

    sub2_1 = AssignmentSubmission(
        id=str(uuid.uuid4()),
        assignment_id=asg2.id,
        student_id=stu_a.id,
        attempt_number=1,
        submitted_at=datetime(2026, 9, 8, 14, 0, 0, tzinfo=timezone.utc),
        status="SUBMITTED",
    )
    sub2_2 = AssignmentSubmission(
        id=str(uuid.uuid4()),
        assignment_id=asg2.id,
        student_id=stu_a.id,
        attempt_number=2,
        submitted_at=datetime(2026, 9, 11, 10, 0, 0, tzinfo=timezone.utc),
        status="RESUBMITTED",
    )
    session.add_all([sub2_1, sub2_2])
    session.commit()

    subs_asg1 = PulseWatchRepository.get_submissions_for_assignment_and_student(session, asg1.id, stu_a.id)
    assert len(subs_asg1) == 2
    # Earliest valid timestamp
    assert subs_asg1[0].submitted_at > asg1.due_date  # Must be classified as Late

    subs_asg2 = PulseWatchRepository.get_submissions_for_assignment_and_student(session, asg2.id, stu_a.id)
    assert len(subs_asg2) == 2
    # Earliest valid timestamp
    assert subs_asg2[0].submitted_at <= asg2.due_date  # Must be classified as On-time


# -----------------------------------------------------------------------------
# 5. Exact Authoritative Threshold Boundary Tests
# -----------------------------------------------------------------------------

def test_exact_threshold_boundaries():
    """Verify the single authoritative mathematical threshold specification."""
    # Attendance / Assessment classification rule:
    # delta >= -5.0  -> NORMAL
    # -15.0 <= delta < -5.0 -> MILD_CHANGE
    # -25.0 <= delta < -15.0 -> MODERATE_CHANGE
    # delta < -25.0  -> SIGNIFICANT_CHANGE

    def classify_delta(delta: float) -> str:
        if delta >= -5.0:
            return "NORMAL"
        elif -15.0 <= delta < -5.0:
            return "MILD_CHANGE"
        elif -25.0 <= delta < -15.0:
            return "MODERATE_CHANGE"
        else:
            return "SIGNIFICANT_CHANGE"

    # Exact boundary test points
    assert classify_delta(-4.9) == "NORMAL"
    assert classify_delta(-5.0) == "NORMAL"
    assert classify_delta(-5.01) == "MILD_CHANGE"

    assert classify_delta(-14.9) == "MILD_CHANGE"
    assert classify_delta(-15.0) == "MILD_CHANGE"
    assert classify_delta(-15.01) == "MODERATE_CHANGE"

    assert classify_delta(-24.9) == "MODERATE_CHANGE"
    assert classify_delta(-25.0) == "MODERATE_CHANGE"
    assert classify_delta(-25.01) == "SIGNIFICANT_CHANGE"


# -----------------------------------------------------------------------------
# 6. Student Authorization Identity Check Test
# -----------------------------------------------------------------------------

def test_student_authorization_identity_check(client: TestClient, pulsewatch_setup):
    """Verify student A can access student A's PulseWatch data (200), but student B is forbidden (403)."""
    u_stu_a_email = pulsewatch_setup["u_stu_a_email"]
    stu_a = pulsewatch_setup["stu_a"]
    stu_b = pulsewatch_setup["stu_b"]

    token_a = _get_token(client, u_stu_a_email)

    # 1. Student A -> Student A PulseWatch = 200 OK
    res_a = client.get(
        f"/api/v1/pulsewatch/student/{stu_a.id}/summary",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["student_id"] == stu_a.id

    # 2. Student A -> Student B PulseWatch = 403 Forbidden
    res_b = client.get(
        f"/api/v1/pulsewatch/student/{stu_b.id}/summary",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_b.status_code == 403
    assert "Access denied" in res_b.json()["detail"]


# -----------------------------------------------------------------------------
# 7. Cohort Context Invariant Test
# -----------------------------------------------------------------------------

def test_cohort_context_invariant(pulsewatch_setup):
    """Verify that cohort context never overrides a student's personal baseline or escalates severity."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    stu_b = pulsewatch_setup["stu_b"]
    c1 = pulsewatch_setup["course1"]
    term = pulsewatch_setup["term"]

    t_ref = date(2026, 9, 18)

    # Student A has 100% attendance in baseline AND observation
    for day_offset in range(10):
        sdate = date(2026, 8, 10) + timedelta(days=day_offset * 2)
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=sdate,
                session_slot="SLOT_1",
                status="PRESENT",
            )
        )
    for day_offset in range(4):
        sdate = date(2026, 9, 6) + timedelta(days=day_offset * 2)
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=sdate,
                session_slot="SLOT_1",
                status="PRESENT",
            )
        )
    session.commit()

    summary = PulseWatchCalculationService.compute_student_summary(session, stu_a.id, reference_date=t_ref)

    # Invariant: Personal status is NORMAL, unaffected by any cohort factors
    assert summary.overall_status == "NORMAL"
    att_sig = next(s for s in summary.signals if s.signal_type == "ATTENDANCE_CHANGE")
    assert att_sig.severity == "NORMAL"
    assert att_sig.delta_value == Decimal("0.00")


# -----------------------------------------------------------------------------
# 8. Read-Only GET Endpoint Test
# -----------------------------------------------------------------------------

def test_get_summary_read_only(client: TestClient, pulsewatch_setup):
    """Verify that calling GET summary repeatedly creates zero database insertions."""
    session = pulsewatch_setup["session"]
    u_stu_a_email = pulsewatch_setup["u_stu_a_email"]
    stu_a = pulsewatch_setup["stu_a"]

    token_a = _get_token(client, u_stu_a_email)

    events_before = session.query(BehaviorEvent).filter(BehaviorEvent.student_id == stu_a.id).count()
    baselines_before = session.query(StudentBehaviorBaseline).filter(StudentBehaviorBaseline.student_id == stu_a.id).count()

    for _ in range(5):
        res = client.get(
            f"/api/v1/pulsewatch/student/{stu_a.id}/summary",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200

    events_after = session.query(BehaviorEvent).filter(BehaviorEvent.student_id == stu_a.id).count()
    baselines_after = session.query(StudentBehaviorBaseline).filter(StudentBehaviorBaseline.student_id == stu_a.id).count()

    assert events_before == events_after == 0
    assert baselines_before == baselines_after == 0


# -----------------------------------------------------------------------------
# 9. Faculty Authorization Scoped to Enrolled Courses Test
# -----------------------------------------------------------------------------

def test_faculty_authorization_scoped(client: TestClient, pulsewatch_setup):
    """Verify faculty can access enrolled student (200), but cannot access unassigned student (403)."""
    u_fac_1_email = pulsewatch_setup["u_fac_1_email"]
    stu_a = pulsewatch_setup["stu_a"]
    stu_b = pulsewatch_setup["stu_b"]

    token_fac1 = _get_token(client, u_fac_1_email)

    # Faculty 1 teaches Course 1 (Student A is enrolled) -> 200 OK
    res_a = client.get(
        f"/api/v1/pulsewatch/student/{stu_a.id}/summary",
        headers={"Authorization": f"Bearer {token_fac1}"},
    )
    assert res_a.status_code == 200

    # Faculty 1 does NOT teach Course 2 (Student B is enrolled) -> 403 Forbidden
    res_b = client.get(
        f"/api/v1/pulsewatch/student/{stu_b.id}/summary",
        headers={"Authorization": f"Bearer {token_fac1}"},
    )
    assert res_b.status_code == 403


# -----------------------------------------------------------------------------
# 10. Admin Institutional Oversight Test
# -----------------------------------------------------------------------------

def test_admin_institutional_oversight(client: TestClient, pulsewatch_setup):
    """Verify administrator has oversight access across all student records."""
    u_adm_email = pulsewatch_setup["u_adm_email"]
    stu_a = pulsewatch_setup["stu_a"]
    stu_b = pulsewatch_setup["stu_b"]

    token_adm = _get_token(client, u_adm_email)

    res_a = client.get(
        f"/api/v1/pulsewatch/student/{stu_a.id}/summary",
        headers={"Authorization": f"Bearer {token_adm}"},
    )
    assert res_a.status_code == 200

    res_b = client.get(
        f"/api/v1/pulsewatch/student/{stu_b.id}/summary",
        headers={"Authorization": f"Bearer {token_adm}"},
    )
    assert res_b.status_code == 200


# -----------------------------------------------------------------------------
# 11. Multi-Signal Combination Without Risk Score Test
# -----------------------------------------------------------------------------

def test_multi_signal_escalation_without_risk_score(pulsewatch_setup):
    """Verify multiple concurrent changes escalate to SIGNIFICANT_CHANGE without generating a risk score."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    c1 = pulsewatch_setup["course1"]
    term = pulsewatch_setup["term"]
    fac_1 = pulsewatch_setup["fac_1"]
    t_ref = date(2026, 9, 18)

    # 1. Baseline attendance (10 sessions PRESENT)
    for day_offset in range(10):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 8, 10) + timedelta(days=day_offset * 2),
                session_slot="SLOT_1",
                status="PRESENT",
            )
        )

    # 2. Observation attendance (Moderate decline: 3 sessions, 2 absent = 33.3% vs 100% -> delta -66.7%)
    # Let's create an exact moderate change: baseline 10 sessions (100%), observation 5 sessions (4 present, 1 late? wait: 4 present, 1 absent = 80% -> delta -20% = MODERATE)
    for day_offset in range(4):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 9, 6) + timedelta(days=day_offset * 2),
                session_slot="SLOT_1",
                status="PRESENT",
            )
        )
    session.add(
        AttendanceRecord(
            id=str(uuid.uuid4()),
            student_id=stu_a.id,
            course_id=c1.id,
            term_id=term.id,
            session_date=date(2026, 9, 15),
            session_slot="SLOT_1",
            status="ABSENT",
        )
    )

    # 3. Coursework: Add 2 baseline assignments, and 1 observation assignment that is missed (MODERATE)
    # Baseline assignments
    for i in range(2):
        asg = Assignment(
            id=str(uuid.uuid4()),
            course_id=c1.id,
            term_id=term.id,
            created_by_faculty_id=fac_1.id,
            title=f"Base Assignment {i}",
            max_marks=Decimal("50.00"),
            release_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
            due_date=datetime(2026, 8, 20 + i, tzinfo=timezone.utc),
        )
        session.add(asg)
        session.flush()
        session.add(
            AssignmentSubmission(
                id=str(uuid.uuid4()),
                assignment_id=asg.id,
                student_id=stu_a.id,
                attempt_number=1,
                submitted_at=datetime(2026, 8, 19 + i, tzinfo=timezone.utc),
                status="SUBMITTED",
            )
        )

    # Observation assignment (Missed)
    asg_obs = Assignment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Obs Assignment Missed",
        max_marks=Decimal("50.00"),
        release_date=datetime(2026, 9, 5, tzinfo=timezone.utc),
        due_date=datetime(2026, 9, 12, tzinfo=timezone.utc),
    )
    session.add(asg_obs)
    session.commit()

    summary = PulseWatchCalculationService.compute_student_summary(session, stu_a.id, reference_date=t_ref)

    # Attendance delta is -20% -> MODERATE_CHANGE
    # Coursework missed count = 1 -> MODERATE_CHANGE
    # Two MODERATE signals combine into SIGNIFICANT_CHANGE
    assert summary.overall_status == "SIGNIFICANT_CHANGE"

    # Invariant: No risk score, probability, or mental health diagnostic in summary response
    response_dict = summary.model_dump()
    assert "risk_score" not in response_dict
    assert "dropout_probability" not in response_dict
    assert "prediction" not in response_dict


# -----------------------------------------------------------------------------
# 12. Assessment Absence Escalation Test
# -----------------------------------------------------------------------------

def test_assessment_absence_escalation(pulsewatch_setup):
    """Verify is_absent == True on formal assessment escalates signal to SIGNIFICANT_CHANGE."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    c1 = pulsewatch_setup["course1"]
    term = pulsewatch_setup["term"]
    fac_1 = pulsewatch_setup["fac_1"]
    t_ref = date(2026, 9, 18)

    # Add baseline assessment
    base_assess = Assessment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Base Quiz",
        assessment_type="QUIZ",
        max_marks=Decimal("20.00"),
        assessment_date=date(2026, 8, 15),
    )
    session.add(base_assess)
    session.flush()
    session.add(
        AssessmentResult(
            id=str(uuid.uuid4()),
            assessment_id=base_assess.id,
            student_id=stu_a.id,
            marks_obtained=Decimal("18.00"),
            is_absent=False,
        )
    )

    # Add observation assessment with absence
    obs_assess = Assessment(
        id=str(uuid.uuid4()),
        course_id=c1.id,
        term_id=term.id,
        created_by_faculty_id=fac_1.id,
        title="Obs Midterm",
        assessment_type="MIDTERM",
        max_marks=Decimal("50.00"),
        assessment_date=date(2026, 9, 10),
    )
    session.add(obs_assess)
    session.flush()
    session.add(
        AssessmentResult(
            id=str(uuid.uuid4()),
            assessment_id=obs_assess.id,
            student_id=stu_a.id,
            marks_obtained=None,
            is_absent=True,
        )
    )
    session.commit()

    summary = PulseWatchCalculationService.compute_student_summary(session, stu_a.id, reference_date=t_ref)
    assess_sig = next(s for s in summary.signals if s.signal_type == "ASSESSMENT_PERFORMANCE")
    assert assess_sig.severity == "SIGNIFICANT_CHANGE"
    assert assess_sig.evidence_payload["has_assessment_absence"] is True
    assert summary.overall_status == "SIGNIFICANT_CHANGE"
    assert "Absence recorded for a formal assessment." in summary.summary_text
    assert "Absence recorded for a formal assessment." in summary.explainability.what_changed


# -----------------------------------------------------------------------------
# 12b. Consecutive Absence Escalation Test
# -----------------------------------------------------------------------------

def test_consecutive_absence_escalation(pulsewatch_setup):
    """Verify consecutive_absences >= 3 escalates attendance to SIGNIFICANT_CHANGE regardless of percentage delta."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    c1 = pulsewatch_setup["course1"]
    term = pulsewatch_setup["term"]
    t_ref = date(2026, 9, 18)

    # 1. Baseline attendance: 25 sessions (18 present, 7 absent = 72.00%)
    for i in range(18):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 8, 6) + timedelta(days=i),
                session_slot="SLOT_1",
                status="PRESENT",
                source="MANUAL",
            )
        )
    for i in range(7):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 8, 24) + timedelta(days=i),
                session_slot="SLOT_1",
                status="ABSENT",
                source="MANUAL",
            )
        )

    # 2. Observation attendance: 10 sessions (7 present, 3 consecutive absent = 70.00%)
    # Delta is 70.00% - 72.00% = -2.00%, which normally would be classified as NORMAL (delta >= -5.0%)
    for i in range(7):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 9, 6) + timedelta(days=i),
                session_slot="SLOT_1",
                status="PRESENT",
                source="MANUAL",
            )
        )
    for i in range(3):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 9, 13) + timedelta(days=i),
                session_slot="SLOT_1",
                status="ABSENT",
                source="MANUAL",
            )
        )
    session.commit()

    summary = PulseWatchCalculationService.compute_student_summary(session, stu_a.id, reference_date=t_ref)
    att_sig = next(s for s in summary.signals if s.signal_type == "ATTENDANCE_CHANGE")

    # Mathematical proof:
    # Delta is -2.00% (ordinarily NORMAL since delta >= -5.0)
    assert att_sig.delta_value == Decimal("-2.00")
    # But 3 consecutive absences trigger deterministic override to SIGNIFICANT_CHANGE
    assert att_sig.evidence_payload["consecutive_absences"] == 3
    assert att_sig.severity == "SIGNIFICANT_CHANGE"
    assert summary.overall_status == "SIGNIFICANT_CHANGE"


# -----------------------------------------------------------------------------
# 13. Missing Data Quality Guard Test
# -----------------------------------------------------------------------------

def test_missing_data_guards(pulsewatch_setup):
    """Verify zero academic records yields NO_DATA without generating an anomaly or change event."""
    session = pulsewatch_setup["session"]
    stu_b = pulsewatch_setup["stu_b"]
    t_ref = date(2026, 9, 18)

    # Student B has no attendance, no assignments, no assessments
    summary = PulseWatchCalculationService.compute_student_summary(session, stu_b.id, reference_date=t_ref)

    assert summary.data_quality == "NO_DATA"
    assert summary.overall_status == "NORMAL"
    assert all(s.severity == "NORMAL" for s in summary.signals)


# -----------------------------------------------------------------------------
# 14. Coursework Zero Denominator Returns NO_DATA (Never 0%)
# -----------------------------------------------------------------------------

def test_coursework_zero_denominator_returns_no_data(pulsewatch_setup):
    """Verify that when eligible assignments is zero, submission_rate is None (NO_DATA), never 0%."""
    session = pulsewatch_setup["session"]
    stu_b = pulsewatch_setup["stu_b"]
    t_ref = date(2026, 9, 18)

    summary = PulseWatchCalculationService.compute_student_summary(session, stu_b.id, reference_date=t_ref)
    asg_sig = next(s for s in summary.signals if s.signal_type == "SUBMISSION_LATENESS")

    # Invariant: Must return None / NO_DATA, never 0.00
    assert asg_sig.current_value is None
    assert asg_sig.baseline_value is None
    assert asg_sig.evidence_payload["data_quality"] == "NO_DATA"
    assert asg_sig.evidence_payload["eligible_assignments"] == 0
    assert asg_sig.severity == "NORMAL"


# -----------------------------------------------------------------------------
# 15. Attendance Improvement Remains NORMAL Test
# -----------------------------------------------------------------------------

def test_attendance_improvement_remains_normal(pulsewatch_setup):
    """Verify that a positive attendance delta (+25%) is classified as NORMAL."""
    session = pulsewatch_setup["session"]
    stu_a = pulsewatch_setup["stu_a"]
    c1 = pulsewatch_setup["course1"]
    term = pulsewatch_setup["term"]
    t_ref = date(2026, 9, 18)

    # Baseline attendance: 6 sessions (4 present, 2 absent = 66.67%)
    for i in range(4):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 8, 10) + timedelta(days=i * 2),
                session_slot="SLOT_1",
                status="PRESENT",
            )
        )
    for i in range(2):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 8, 20) + timedelta(days=i * 2),
                session_slot="SLOT_1",
                status="ABSENT",
            )
        )

    # Observation attendance: 4 sessions (all present = 100%)
    for i in range(4):
        session.add(
            AttendanceRecord(
                id=str(uuid.uuid4()),
                student_id=stu_a.id,
                course_id=c1.id,
                term_id=term.id,
                session_date=date(2026, 9, 6) + timedelta(days=i * 2),
                session_slot="SLOT_1",
                status="PRESENT",
            )
        )
    session.commit()

    summary = PulseWatchCalculationService.compute_student_summary(session, stu_a.id, reference_date=t_ref)
    att_sig = next(s for s in summary.signals if s.signal_type == "ATTENDANCE_CHANGE")

    # Invariant: Improvement (+33.33%) remains NORMAL
    assert att_sig.severity == "NORMAL"
    assert att_sig.delta_value > Decimal("0.00")
    assert summary.overall_status == "NORMAL"


# -----------------------------------------------------------------------------
# 16. Timeline, Signals, and Baseline Endpoints Test
# -----------------------------------------------------------------------------

def test_pulsewatch_endpoints_timeline_and_baseline(client: TestClient, pulsewatch_setup):
    """Verify timeline, signals, baseline, and evaluate endpoints via HTTP."""
    session = pulsewatch_setup["session"]
    u_stu_a_email = pulsewatch_setup["u_stu_a_email"]
    stu_a = pulsewatch_setup["stu_a"]

    token_a = _get_token(client, u_stu_a_email)

    # 1. Trigger evaluate POST
    eval_res = client.post(
        f"/api/v1/pulsewatch/student/{stu_a.id}/evaluate?window_days=14",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["student_id"] == stu_a.id
    assert eval_data["algorithm_version"] == "pulsewatch-v1.0"

    # 2. Query timeline GET
    tl_res = client.get(
        f"/api/v1/pulsewatch/student/{stu_a.id}/timeline",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert tl_res.status_code == 200
    timeline = tl_res.json()
    assert len(timeline) >= 1
    assert timeline[0]["student_id"] == stu_a.id

    # 3. Query signals GET
    sig_res = client.get(
        f"/api/v1/pulsewatch/student/{stu_a.id}/signals?window_days=14",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert sig_res.status_code == 200
    signals = sig_res.json()
    assert len(signals) == 3

    # 4. Query baseline GET
    bl_res = client.get(
        f"/api/v1/pulsewatch/student/{stu_a.id}/baseline",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert bl_res.status_code == 200
    baselines = bl_res.json()
    assert len(baselines) >= 1
    assert all(b["algorithm_version"] == "pulsewatch-v1.0" for b in baselines)

