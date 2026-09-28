"""Comprehensive integration tests for Academic Domain, constraints, validations, and lateness derivation.

Validates:
- Assessment marks boundaries (0 <= marks <= max_marks, negative rejected, absent handled).
- Scoped uniqueness (Course per institution, Dept per institution, Program per dept, Batch per program, Section per batch).
- Assignment submission attempt numbering, multiple attempts, and deterministic lateness.
- Student profile hierarchy consistency (batch.program_id, section.batch_id).
- Faculty course assignment partial unique indexes (course-wide vs section-specific).
- Date check constraints (term dates, assignment release/due/cutoff).
- Attendance recording enrollment integrity, duplicate slot rejection, and derived percentage calculation.
- RESTRICT delete integrity.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.academic import (
    AcademicTerm,
    Assessment,
    AssessmentResult,
    Assignment,
    AssignmentSubmission,
    AttendanceRecord,
    Batch,
    Course,
    Department,
    Enrollment,
    FacultyCourseAssignment,
    FacultyProfile,
    Institution,
    Program,
    Section,
    StudentProfile,
)
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.repositories.user_repo import UserRepository
from app.schemas.academic import (
    AssessmentCreate,
    AssessmentResultCreate,
    AssignmentCreate,
    AssignmentSubmissionCreate,
    AttendanceRecordCreate,
    EnrollmentCreate,
    FacultyProfileCreate,
    StudentProfileCreate,
    SubmissionGradeRequest,
)
from app.services.academic_service import AcademicService
from tests.conftest import get_test_session


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def db():
    """Provide an independent PostgreSQL session with expire_on_commit=False."""
    session = get_test_session()
    session.expire_on_commit = False
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def academic_setup(db: Session):
    """Fixture creating an isolated educational hierarchy for tests."""
    inst = Institution(
        id=str(uuid.uuid4()),
        name="Test Engineering Academy",
        code=f"TEA_{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(inst)
    db.flush()

    dept = Department(
        id=str(uuid.uuid4()),
        institution_id=inst.id,
        name="Computer Science",
        code=f"CS_{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(dept)
    db.flush()

    prog = Program(
        id=str(uuid.uuid4()),
        department_id=dept.id,
        name="B.Tech Computer Science",
        code=f"BTCS_{uuid.uuid4().hex[:6]}",
        degree_level="UG",
        duration_years=4,
        is_active=True,
    )
    db.add(prog)
    db.flush()

    batch = Batch(
        id=str(uuid.uuid4()),
        program_id=prog.id,
        name=f"2024-2028_{uuid.uuid4().hex[:4]}",
        start_year=2024,
        end_year=2028,
        current_semester=1,
        is_active=True,
    )
    db.add(batch)
    db.flush()

    sec = Section(
        id=str(uuid.uuid4()),
        batch_id=batch.id,
        name=f"Sec_A_{uuid.uuid4().hex[:4]}",
        capacity=60,
        is_active=True,
    )
    db.add(sec)
    db.flush()

    term = AcademicTerm(
        id=str(uuid.uuid4()),
        institution_id=inst.id,
        name=f"Fall_2026_{uuid.uuid4().hex[:4]}",
        term_type="SEMESTER",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 12, 15),
        is_current=True,
    )
    db.add(term)
    db.flush()

    course = Course(
        id=str(uuid.uuid4()),
        institution_id=inst.id,
        department_id=dept.id,
        code=f"CS101_{uuid.uuid4().hex[:6]}",
        title="Algorithms and Data Structures",
        credits=4,
        course_type="THEORY",
        is_active=True,
    )
    db.add(course)
    db.flush()

    f_user = UserRepository.create_user(
        db,
        email=f"prof_{uuid.uuid4().hex[:6]}@test.edu",
        password_hash=hash_password("CampusPulse@2026!"),
        full_name="Prof. Alan Turing",
        is_active=True,
        is_verified=True,
    )
    UserRepository.set_user_roles(db, f_user.id, ["FACULTY"])

    f_prof = FacultyProfile(
        id=str(uuid.uuid4()),
        user_id=f_user.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        department_id=dept.id,
        designation="Professor",
        joining_date=date(2020, 1, 1),
        is_active=True,
    )
    db.add(f_prof)
    db.flush()

    s_user = UserRepository.create_user(
        db,
        email=f"student_{uuid.uuid4().hex[:6]}@test.edu",
        password_hash=hash_password("CampusPulse@2026!"),
        full_name="Alice Lovelace",
        is_active=True,
        is_verified=True,
    )
    UserRepository.set_user_roles(db, s_user.id, ["STUDENT"])

    s_prof = StudentProfile(
        id=str(uuid.uuid4()),
        user_id=s_user.id,
        enrollment_number=f"ENR_{uuid.uuid4().hex[:6]}",
        program_id=prog.id,
        batch_id=batch.id,
        section_id=sec.id,
        current_semester=1,
        admission_date=date(2024, 8, 1),
        academic_status="ENROLLED",
    )
    db.add(s_prof)
    db.flush()

    assignment = FacultyCourseAssignment(
        id=str(uuid.uuid4()),
        faculty_id=f_prof.id,
        course_id=course.id,
        term_id=term.id,
        section_id=sec.id,
        role="PRIMARY_INSTRUCTOR",
    )
    db.add(assignment)
    db.flush()

    enrollment = Enrollment(
        id=str(uuid.uuid4()),
        student_id=s_prof.id,
        course_id=course.id,
        term_id=term.id,
        section_id=sec.id,
        enrollment_date=date(2026, 8, 1),
        status="ENROLLED",
    )
    db.add(enrollment)
    db.commit()

    return {
        "institution_id": inst.id,
        "institution_code": inst.code,
        "department_id": dept.id,
        "department_code": dept.code,
        "program_id": prog.id,
        "program_code": prog.code,
        "batch_id": batch.id,
        "batch_name": batch.name,
        "section_id": sec.id,
        "section_name": sec.name,
        "term_id": term.id,
        "term_name": term.name,
        "course_id": course.id,
        "course_code": course.code,
        "faculty_user_id": f_user.id,
        "faculty_prof_id": f_prof.id,
        "student_user_id": s_user.id,
        "student_prof_id": s_prof.id,
    }


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

def test_assessment_result_marks_validation(db: Session, academic_setup: dict):
    """Verify that:
    1. Negative marks are rejected by the database CHECK constraint.
    2. Marks above max_marks are rejected by service domain validation.
    3. Boundary marks (0 and max_marks) and valid intermediate marks are accepted.
    4. Absent student results cannot be awarded positive marks.
    """
    data = academic_setup
    course_id = data["course_id"]
    term_id = data["term_id"]
    faculty_prof_id = data["faculty_prof_id"]
    student_prof_id = data["student_prof_id"]
    faculty_user = UserRepository.get_by_id(db, data["faculty_user_id"])

    # Create assessment with max_marks = 50.00
    assessment = Assessment(
        id=str(uuid.uuid4()),
        course_id=course_id,
        term_id=term_id,
        created_by_faculty_id=faculty_prof_id,
        title=f"Midterm Exam_{uuid.uuid4().hex[:4]}",
        assessment_type="MIDTERM",
        max_marks=Decimal("50.00"),
        weightage_percentage=Decimal("20.00"),
        assessment_date=date(2026, 10, 1),
    )
    db.add(assessment)
    db.commit()

    # 1. DB CHECK rejects negative marks
    bad_res = AssessmentResult(
        id=str(uuid.uuid4()),
        assessment_id=assessment.id,
        student_id=student_prof_id,
        marks_obtained=Decimal("-5.00"),
        is_absent=False,
    )
    db.add(bad_res)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # 2. Service rejects marks exceeding max_marks
    with pytest.raises(HTTPException) as exc_info:
        AcademicService.record_assessment_result(
            db,
            assessment_id=assessment.id,
            payload=AssessmentResultCreate(
                student_id=student_prof_id,
                marks_obtained=Decimal("55.00"),
                is_absent=False,
            ),
            current_user=faculty_user,
        )
    assert exc_info.value.status_code == 422
    assert "exceeds maximum allowed" in exc_info.value.detail

    # 3. Service rejects negative marks
    with pytest.raises(HTTPException) as exc_info:
        AcademicService.record_assessment_result(
            db,
            assessment_id=assessment.id,
            payload=AssessmentResultCreate(
                student_id=student_prof_id,
                marks_obtained=Decimal("-1.00"),
                is_absent=False,
            ),
            current_user=faculty_user,
        )
    assert exc_info.value.status_code == 422
    assert "cannot be negative" in exc_info.value.detail

    # 4. Service rejects positive marks when is_absent=True
    with pytest.raises(HTTPException) as exc_info:
        AcademicService.record_assessment_result(
            db,
            assessment_id=assessment.id,
            payload=AssessmentResultCreate(
                student_id=student_prof_id,
                marks_obtained=Decimal("25.00"),
                is_absent=True,
            ),
            current_user=faculty_user,
        )
    assert exc_info.value.status_code == 422
    assert "Absent student cannot be awarded positive marks" in exc_info.value.detail

    # 5. Boundary value: 0.00 is accepted
    res_zero = AcademicService.record_assessment_result(
        db,
        assessment_id=assessment.id,
        payload=AssessmentResultCreate(
            student_id=student_prof_id,
            marks_obtained=Decimal("0.00"),
            is_absent=False,
            remarks="Attended but scored zero",
        ),
        current_user=faculty_user,
    )
    assert res_zero.marks_obtained == Decimal("0.00")

    # Clean up result for next check
    db.delete(res_zero)
    db.commit()

    # 6. Boundary value: max_marks (50.00) is accepted
    res_max = AcademicService.record_assessment_result(
        db,
        assessment_id=assessment.id,
        payload=AssessmentResultCreate(
            student_id=student_prof_id,
            marks_obtained=Decimal("50.00"),
            is_absent=False,
            remarks="Full marks",
        ),
        current_user=faculty_user,
    )
    assert res_max.marks_obtained == Decimal("50.00")


def test_course_code_uniqueness_and_institution_scoping(db: Session, academic_setup: dict):
    """Verify:
    1. Course code is unique within the same institution.
    2. Same course code in a DIFFERENT institution is accepted.
    3. Course department institution mismatch is rejected by service validation.
    """
    data = academic_setup
    inst1_id = data["institution_id"]
    dept1_id = data["department_id"]
    existing_code = data["course_code"]

    # 1. Duplicate course code within inst1 rejected by DB
    duplicate_course = Course(
        id=str(uuid.uuid4()),
        institution_id=inst1_id,
        department_id=dept1_id,
        code=existing_code,
        title="Duplicate Code Course",
        credits=3,
    )
    db.add(duplicate_course)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # 2. Same course code in a DIFFERENT institution is allowed
    inst2 = Institution(
        id=str(uuid.uuid4()),
        name="Second Campus Institute",
        code=f"SCI_{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(inst2)
    db.flush()

    dept2 = Department(
        id=str(uuid.uuid4()),
        institution_id=inst2.id,
        name="CS Department 2",
        code=f"CS2_{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(dept2)
    db.flush()

    course_in_inst2 = Course(
        id=str(uuid.uuid4()),
        institution_id=inst2.id,
        department_id=dept2.id,
        code=existing_code,  # Same code, different institution!
        title="Valid Course in Other Campus",
        credits=4,
    )
    db.add(course_in_inst2)
    db.commit()
    assert course_in_inst2.id is not None

    # 3. Service rejects course when department institution != course institution
    with pytest.raises(HTTPException) as exc_info:
        AcademicService.create_course(
            db,
            institution_id=inst1_id,
            department_id=dept2.id,  # belongs to inst2!
            code=f"ERR_{uuid.uuid4().hex[:4]}",
            title="Mismatched Institution Course",
        )
    assert exc_info.value.status_code == 422
    assert "does not match department institution" in exc_info.value.detail


def test_scoped_uniqueness_constraints(db: Session, academic_setup: dict):
    """Verify scoped composite unique constraints:
    - Department: UNIQUE(institution_id, code)
    - Program: UNIQUE(department_id, code)
    - Batch: UNIQUE(program_id, name)
    - Section: UNIQUE(batch_id, name)
    - AcademicTerm: UNIQUE(institution_id, name)
    """
    data = academic_setup
    inst_id = data["institution_id"]
    dept_id = data["department_id"]
    dept_code = data["department_code"]
    prog_id = data["program_id"]
    prog_code = data["program_code"]
    batch_id = data["batch_id"]
    batch_name = data["batch_name"]
    sec_name = data["section_name"]
    term_name = data["term_name"]

    # Duplicate Department code in same institution
    d_dup = Department(id=str(uuid.uuid4()), institution_id=inst_id, name="Dept Dup", code=dept_code)
    db.add(d_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Duplicate Program code in same department
    p_dup = Program(id=str(uuid.uuid4()), department_id=dept_id, name="Prog Dup", code=prog_code)
    db.add(p_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Duplicate Batch name in same program
    b_dup = Batch(id=str(uuid.uuid4()), program_id=prog_id, name=batch_name, start_year=2024, end_year=2028)
    db.add(b_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Duplicate Section name in same batch
    s_dup = Section(id=str(uuid.uuid4()), batch_id=batch_id, name=sec_name, capacity=50)
    db.add(s_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Duplicate AcademicTerm name in same institution
    t_dup = AcademicTerm(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        name=term_name,
        term_type="SEMESTER",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 12, 15),
    )
    db.add(t_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_assignment_submission_attempt_tracking_and_lateness(db: Session, academic_setup: dict):
    """Verify:
    1. First submission has attempt_number=1.
    2. Second submission has attempt_number=2.
    3. Duplicate attempt numbers rejected by UNIQUE constraint.
    4. Deterministic lateness derivation (LATE if submitted_at > due_date).
    5. Cutoff deadline rejection.
    """
    data = academic_setup
    course_id = data["course_id"]
    term_id = data["term_id"]
    student_prof_id = data["student_prof_id"]
    faculty_user = UserRepository.get_by_id(db, data["faculty_user_id"])
    student_user = UserRepository.get_by_id(db, data["student_user_id"])

    now = datetime.now(timezone.utc)
    due_date = now + timedelta(hours=2)
    cutoff_date = now + timedelta(days=2)

    # 1. Create assignment
    asg = AcademicService.create_assignment(
        db,
        payload=AssignmentCreate(
            course_id=course_id,
            term_id=term_id,
            title=f"Lab Assignment 1_{uuid.uuid4().hex[:4]}",
            max_marks=Decimal("100.00"),
            weightage_percentage=Decimal("10.00"),
            release_date=now - timedelta(days=1),
            due_date=due_date,
            cutoff_date=cutoff_date,
            allow_late_submission=True,
        ),
        current_user=faculty_user,
    )

    # 2. First submission (on-time)
    sub1 = AcademicService.submit_assignment(
        db,
        assignment_id=asg.id,
        payload=AssignmentSubmissionCreate(submission_content="Attempt 1 source code"),
        current_user=student_user,
    )
    assert sub1.attempt_number == 1
    assert sub1.status == "SUBMITTED"

    # 3. Second submission (re-submission)
    sub2 = AcademicService.submit_assignment(
        db,
        assignment_id=asg.id,
        payload=AssignmentSubmissionCreate(submission_content="Attempt 2 revised code"),
        current_user=student_user,
    )
    assert sub2.attempt_number == 2

    # 4. Duplicate attempt number rejected by DB constraint
    sub_dup = AssignmentSubmission(
        id=str(uuid.uuid4()),
        assignment_id=asg.id,
        student_id=student_prof_id,
        attempt_number=1,  # Already exists!
        submitted_at=now,
        status="SUBMITTED",
    )
    db.add(sub_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # 5. Late submission derivation
    past_asg = AcademicService.create_assignment(
        db,
        payload=AssignmentCreate(
            course_id=course_id,
            term_id=term_id,
            title=f"Past Due Assignment_{uuid.uuid4().hex[:4]}",
            max_marks=Decimal("50.00"),
            release_date=now - timedelta(days=5),
            due_date=now - timedelta(days=1),  # Past due!
            cutoff_date=now + timedelta(days=2),
            allow_late_submission=True,
        ),
        current_user=faculty_user,
    )

    sub_late = AcademicService.submit_assignment(
        db,
        assignment_id=past_asg.id,
        payload=AssignmentSubmissionCreate(submission_content="Late attempt"),
        current_user=student_user,
    )
    assert sub_late.status == "LATE"

    # 6. Past cutoff rejection
    closed_asg = AcademicService.create_assignment(
        db,
        payload=AssignmentCreate(
            course_id=course_id,
            term_id=term_id,
            title=f"Closed Assignment_{uuid.uuid4().hex[:4]}",
            max_marks=Decimal("50.00"),
            release_date=now - timedelta(days=10),
            due_date=now - timedelta(days=5),
            cutoff_date=now - timedelta(days=1),  # Cutoff passed!
            allow_late_submission=True,
        ),
        current_user=faculty_user,
    )
    with pytest.raises(HTTPException) as exc_info:
        AcademicService.submit_assignment(
            db,
            assignment_id=closed_asg.id,
            payload=AssignmentSubmissionCreate(submission_content="Attempt after cutoff"),
            current_user=student_user,
        )
    assert exc_info.value.status_code == 400
    assert "cutoff deadline has passed" in exc_info.value.detail


def test_student_profile_consistency_and_hierarchy_validation(db: Session, academic_setup: dict):
    """Verify that student profile creation validates:
    - batch belongs to program
    - section belongs to batch
    """
    data = academic_setup
    dept_id = data["department_id"]
    prog1_id = data["program_id"]

    prog2 = Program(
        id=str(uuid.uuid4()),
        department_id=dept_id,
        name="Program 2",
        code=f"P2_{uuid.uuid4().hex[:4]}",
    )
    db.add(prog2)
    db.flush()

    batch2 = Batch(
        id=str(uuid.uuid4()),
        program_id=prog2.id,
        name=f"Batch 2_{uuid.uuid4().hex[:4]}",
        start_year=2025,
        end_year=2029,
    )
    db.add(batch2)
    db.flush()

    test_user = UserRepository.create_user(
        db,
        email=f"candidate_{uuid.uuid4().hex[:4]}@test.edu",
        password_hash=hash_password("CampusPulse@2026!"),
        full_name="Candidate Student",
    )

    # 1. Inconsistent: batch2 does not belong to prog1
    with pytest.raises(HTTPException) as exc_info:
        AcademicService.create_student_profile(
            db,
            payload=StudentProfileCreate(
                user_id=test_user.id,
                enrollment_number=f"ENR_{uuid.uuid4().hex[:6]}",
                program_id=prog1_id,
                batch_id=batch2.id,  # mismatch!
            ),
        )
    assert exc_info.value.status_code == 422
    assert "Batch does not belong to the specified program" in exc_info.value.detail


def test_faculty_course_assignment_partial_indexes(db: Session, academic_setup: dict):
    """Verify that PostgreSQL partial indexes enforce:
    1. Only one course-wide assignment (section_id IS NULL) per (faculty, course, term).
    2. Only one section assignment (section_id IS NOT NULL) per (faculty, course, term, section).
    """
    data = academic_setup
    course_id = data["course_id"]
    term_id = data["term_id"]
    sec_id = data["section_id"]
    f_prof_id = data["faculty_prof_id"]

    # 1. Create course-wide assignment (section_id = None)
    ca1 = FacultyCourseAssignment(
        id=str(uuid.uuid4()),
        faculty_id=f_prof_id,
        course_id=course_id,
        term_id=term_id,
        section_id=None,
        role="PRIMARY_INSTRUCTOR",
    )
    db.add(ca1)
    db.commit()

    # 2. Duplicate course-wide assignment must fail under uq_faculty_assignment_course_wide
    ca1_dup = FacultyCourseAssignment(
        id=str(uuid.uuid4()),
        faculty_id=f_prof_id,
        course_id=course_id,
        term_id=term_id,
        section_id=None,
        role="CO_INSTRUCTOR",
    )
    db.add(ca1_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # 3. Duplicate section assignment must fail under uq_faculty_assignment_section
    ca_sec_dup = FacultyCourseAssignment(
        id=str(uuid.uuid4()),
        faculty_id=f_prof_id,
        course_id=course_id,
        term_id=term_id,
        section_id=sec_id,
        role="LAB_INSTRUCTOR",
    )
    db.add(ca_sec_dup)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_date_integrity_check_constraints(db: Session, academic_setup: dict):
    """Verify database CHECK constraints on academic dates:
    - AcademicTerm: start_date < end_date
    - Assignment: release_date <= due_date
    - Assignment: due_date <= cutoff_date
    """
    data = academic_setup
    inst_id = data["institution_id"]
    course_id = data["course_id"]
    term_id = data["term_id"]
    f_prof_id = data["faculty_prof_id"]

    # 1. AcademicTerm start_date >= end_date rejected
    bad_term = AcademicTerm(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        name=f"Bad Term_{uuid.uuid4().hex[:4]}",
        term_type="SEMESTER",
        start_date=date(2026, 12, 1),
        end_date=date(2026, 8, 1),
    )
    db.add(bad_term)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # 2. Assignment release_date > due_date rejected
    now = datetime.now(timezone.utc)
    bad_asg1 = Assignment(
        id=str(uuid.uuid4()),
        course_id=course_id,
        term_id=term_id,
        created_by_faculty_id=f_prof_id,
        title=f"Bad Asg 1_{uuid.uuid4().hex[:4]}",
        max_marks=Decimal("100.00"),
        release_date=now + timedelta(days=5),
        due_date=now + timedelta(days=2),
    )
    db.add(bad_asg1)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # 3. Assignment due_date > cutoff_date rejected
    bad_asg2 = Assignment(
        id=str(uuid.uuid4()),
        course_id=course_id,
        term_id=term_id,
        created_by_faculty_id=f_prof_id,
        title=f"Bad Asg 2_{uuid.uuid4().hex[:4]}",
        max_marks=Decimal("100.00"),
        release_date=now,
        due_date=now + timedelta(days=5),
        cutoff_date=now + timedelta(days=3),
    )
    db.add(bad_asg2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_attendance_integrity_and_derived_summary(db: Session, academic_setup: dict):
    """Verify:
    1. Attendance rejected for student not enrolled in course.
    2. Attendance accepted for enrolled student.
    3. Duplicate attendance on same date and slot rejected.
    4. Derived attendance percentage calculated accurately.
    """
    data = academic_setup
    course_id = data["course_id"]
    term_id = data["term_id"]
    student_prof_id = data["student_prof_id"]
    faculty_user = UserRepository.get_by_id(db, data["faculty_user_id"])
    prog_id = data["program_id"]
    batch_id = data["batch_id"]

    # 1. Create a non-enrolled student
    non_enrolled_user = UserRepository.create_user(
        db,
        email=f"other_{uuid.uuid4().hex[:4]}@test.edu",
        password_hash=hash_password("CampusPulse@2026!"),
        full_name="Non Enrolled Student",
    )
    non_enrolled_prof = AcademicRepository.create_student_profile(
        db,
        user_id=non_enrolled_user.id,
        enrollment_number=f"ENR_{uuid.uuid4().hex[:6]}",
        program_id=prog_id,
        batch_id=batch_id,
    )

    with pytest.raises(HTTPException) as exc_info:
        AcademicService.record_attendance(
            db,
            payload=AttendanceRecordCreate(
                student_id=non_enrolled_prof.id,
                course_id=course_id,
                term_id=term_id,
                session_date=date(2026, 9, 1),
                session_slot="SLOT_1",
                status="PRESENT",
            ),
            current_user=faculty_user,
        )
    assert exc_info.value.status_code == 422
    assert "not actively enrolled" in exc_info.value.detail

    # 2. Record attendance for enrolled student
    att1 = AcademicService.record_attendance(
        db,
        payload=AttendanceRecordCreate(
            student_id=student_prof_id,
            course_id=course_id,
            term_id=term_id,
            session_date=date(2026, 9, 1),
            session_slot="SLOT_1",
            status="PRESENT",
        ),
        current_user=faculty_user,
    )
    assert att1.id is not None

    # 3. Duplicate attendance for same slot and date rejected
    with pytest.raises(HTTPException) as exc_info:
        AcademicService.record_attendance(
            db,
            payload=AttendanceRecordCreate(
                student_id=student_prof_id,
                course_id=course_id,
                term_id=term_id,
                session_date=date(2026, 9, 1),
                session_slot="SLOT_1",
                status="ABSENT",
            ),
            current_user=faculty_user,
        )
    assert exc_info.value.status_code == 409

    # Record 3 more sessions: 1 PRESENT, 1 LATE, 1 ABSENT
    AcademicService.record_attendance(
        db,
        payload=AttendanceRecordCreate(
            student_id=student_prof_id,
            course_id=course_id,
            term_id=term_id,
            session_date=date(2026, 9, 3),
            session_slot="SLOT_1",
            status="PRESENT",
        ),
        current_user=faculty_user,
    )
    AcademicService.record_attendance(
        db,
        payload=AttendanceRecordCreate(
            student_id=student_prof_id,
            course_id=course_id,
            term_id=term_id,
            session_date=date(2026, 9, 5),
            session_slot="SLOT_1",
            status="LATE",
        ),
        current_user=faculty_user,
    )
    AcademicService.record_attendance(
        db,
        payload=AttendanceRecordCreate(
            student_id=student_prof_id,
            course_id=course_id,
            term_id=term_id,
            session_date=date(2026, 9, 8),
            session_slot="SLOT_1",
            status="ABSENT",
        ),
        current_user=faculty_user,
    )

    # 4. Derived summary: 4 total, 2 PRESENT, 1 LATE, 1 ABSENT -> 3/4 = 75.0%
    summary = AcademicRepository.calculate_student_attendance_summary(
        db,
        student_id=student_prof_id,
        course_id=course_id,
        term_id=term_id,
    )
    assert summary["total_sessions"] == 4
    assert summary["present_count"] == 2
    assert summary["late_count"] == 1
    assert summary["absent_count"] == 1
    assert summary["attendance_percentage"] == 75.0


def test_restrict_delete_integrity(db: Session, academic_setup: dict):
    """Verify that RESTRICT foreign key deletion policies prevent accidental deletion of parent records."""
    data = academic_setup
    s_user = UserRepository.get_by_id(db, data["student_user_id"])
    course = AcademicRepository.get_course_by_id(db, data["course_id"])

    # Trying to delete User with linked StudentProfile must be rejected by RESTRICT
    db.delete(s_user)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    # Trying to delete Course with linked Enrollment must be rejected by RESTRICT
    db.delete(course)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_strict_attendance_enum_validation(db: Session, academic_setup: dict):
    """Verify strict Literal enum validation on AttendanceRecordCreate."""
    from pydantic import ValidationError

    data = academic_setup
    student_id = data["student_prof_id"]
    course_id = data["course_id"]
    term_id = data["term_id"]
    faculty_user = UserRepository.get_by_id(db, data["faculty_user_id"])

    # 1. Valid statuses: PRESENT, ABSENT, LATE, EXCUSED must all be accepted
    for idx, valid_status in enumerate(["PRESENT", "ABSENT", "LATE", "EXCUSED"]):
        rec = AcademicService.record_attendance(
            db,
            payload=AttendanceRecordCreate(
                student_id=student_id,
                course_id=course_id,
                term_id=term_id,
                session_date=date(2026, 10, 1 + idx),
                session_slot="SLOT_ENUM",
                status=valid_status,
                source="MANUAL",
            ),
            current_user=faculty_user,
        )
        assert rec.status == valid_status

    # 2. Invalid status must raise ValidationError (HTTP 422 at API layer)
    with pytest.raises(ValidationError) as exc_info:
        AttendanceRecordCreate(
            student_id=student_id,
            course_id=course_id,
            term_id=term_id,
            session_date=date(2026, 10, 10),
            session_slot="SLOT_ENUM",
            status="MAYBE",  # type: ignore[arg-type]
            source="MANUAL",
        )
    assert "status" in str(exc_info.value)

    # 3. Invalid source must raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        AttendanceRecordCreate(
            student_id=student_id,
            course_id=course_id,
            term_id=term_id,
            session_date=date(2026, 10, 11),
            session_slot="SLOT_ENUM",
            status="PRESENT",
            source="CARRIER_PIGEON",  # type: ignore[arg-type]
        )
    assert "source" in str(exc_info.value)


def test_enrollment_course_state_and_cross_institution_guards(db: Session, academic_setup: dict):
    """Verify enrollment invariant guards: active course and matching institution."""
    data = academic_setup

    # Setup a new student for enrollment tests
    new_user = UserRepository.create_user(
        db,
        email=f"guard_student_{uuid.uuid4().hex[:6]}@test.edu",
        password_hash=hash_password("SecurePass123!"),
        full_name="Guard Student",
    )
    student = AcademicRepository.create_student_profile(
        db,
        user_id=new_user.id,
        enrollment_number=f"ENR_{uuid.uuid4().hex[:8]}",
        program_id=data["program_id"],
        batch_id=data["batch_id"],
        section_id=data["section_id"],
        current_semester=1,
        admission_date=date(2026, 8, 1),
        academic_status="ENROLLED",
    )

    # 1. Active course + matching institution -> ACCEPT
    active_course = Course(
        id=str(uuid.uuid4()),
        institution_id=data["institution_id"],
        department_id=data["department_id"],
        code=f"ACT_{uuid.uuid4().hex[:6]}",
        title="Active Course",
        credits=3,
        is_active=True,
    )
    db.add(active_course)
    db.commit()

    enrollment = AcademicService.enroll_student(
        db,
        payload=EnrollmentCreate(
            student_id=student.id,
            course_id=active_course.id,
            term_id=data["term_id"],
            enrollment_date=date(2026, 8, 15),
        ),
        actor_user=None,
    )
    assert enrollment.id is not None
    assert enrollment.status == "ENROLLED"

    # 2. Inactive course -> REJECT with HTTP 422
    inactive_course = Course(
        id=str(uuid.uuid4()),
        institution_id=data["institution_id"],
        department_id=data["department_id"],
        code=f"INACT_{uuid.uuid4().hex[:6]}",
        title="Inactive Course",
        credits=3,
        is_active=False,
    )
    db.add(inactive_course)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        AcademicService.enroll_student(
            db,
            payload=EnrollmentCreate(
                student_id=student.id,
                course_id=inactive_course.id,
                term_id=data["term_id"],
                enrollment_date=date(2026, 8, 15),
            ),
            actor_user=None,
        )
    assert exc_info.value.status_code == 422
    assert "Cannot enroll in an inactive course" in exc_info.value.detail

    # 3. Active course + different institution term -> REJECT with HTTP 422
    other_inst = Institution(
        id=str(uuid.uuid4()),
        name=f"Other Institution {uuid.uuid4().hex[:6]}",
        code=f"OTHER_{uuid.uuid4().hex[:6]}",
        is_active=True,
    )
    db.add(other_inst)
    db.flush()

    other_term = AcademicTerm(
        id=str(uuid.uuid4()),
        institution_id=other_inst.id,
        name=f"Fall 2026 {uuid.uuid4().hex[:4]}",
        term_type="SEMESTER",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 12, 15),
        is_current=True,
    )
    db.add(other_term)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        AcademicService.enroll_student(
            db,
            payload=EnrollmentCreate(
                student_id=student.id,
                course_id=active_course.id,
                term_id=other_term.id,
                enrollment_date=date(2026, 8, 15),
            ),
            actor_user=None,
        )
    assert exc_info.value.status_code == 422
    assert "Course and academic term must belong to the same institution" in exc_info.value.detail

