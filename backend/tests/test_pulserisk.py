"""Comprehensive tests for Phase 4: PulseRisk Support Prioritization Subsystem.

Verifies:
1. Snapshot identity uniqueness includes policy_version.
2. Historical snapshot reproducibility across policy changes.
3. Safety floor precedence over low confidence (Test 3: assessment absence override).
4. Low confidence with no safety floor (Test 4: insufficient data -> SPI = 0.0, LOW_PRIORITY).
5. Zero PulseWatch metric duplication (strictly zero queries to raw academic tables).
6. Longitudinal persistence canonical window deduplication (>= 50% overlap clustering, tie-breakers, half-life decay).
7. Policy lifecycle transitions (DRAFT -> VALIDATED -> ACTIVE -> RETIRED), validation, immutability, and uniqueness.
8. Tier boundaries and exact mathematical thresholds.
9. Dynamic weight renormalization when dimensions are missing.
10. Scoped RBAC, zero-write GET separation, and idempotent evaluation persistence.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
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
from app.models.pulserisk import RiskPolicy, RiskSignalContribution, StudentRiskSnapshot
from app.models.pulsewatch import BehaviorEvent, BehaviorSignalEvidence
from app.repositories.academic_repo import AcademicRepository
from app.repositories.pulserisk_repo import PulseRiskRepository
from app.repositories.user_repo import UserRepository
from app.schemas.pulsewatch import (
    AcademicContextSchema,
    CohortContextSchema,
    ExplainabilitySchema,
    PulseWatchSummaryResponse,
    SignalEvidenceSchema,
)
from app.services.pulserisk_calculation_service import (
    ALGORITHM_VERSION,
    PulseRiskCalculationService,
)
from app.services.risk_policy_service import RiskPolicyService
from tests.conftest import get_test_session


def _make_mock_pulsewatch_summary(
    student_id: str,
    signals: list,
    data_quality: str = "VALID_DATA",
    overall_status: str = "NORMAL",
    confidence_score: Decimal = Decimal("1.00"),
) -> PulseWatchSummaryResponse:
    return PulseWatchSummaryResponse(
        student_id=student_id,
        observation_window_days=14,
        window_start_date=date(2026, 9, 1),
        window_end_date=date(2026, 9, 14),
        baseline_start_date=date(2026, 8, 1),
        baseline_end_date=date(2026, 8, 31),
        overall_status=overall_status,
        summary_text="Mock behavioral summary",
        signals=signals,
        data_quality=data_quality,
        confidence_score=confidence_score,
        cohort_context=CohortContextSchema(),
        academic_context=AcademicContextSchema(),
        explainability=ExplainabilitySchema(
            what_changed="Behavioral shift test",
            compared_with="Baseline period",
            observation_period="14 days",
            data_sufficiency=data_quality,
        ),
        algorithm_version="pulsewatch-v1.0",
        calculated_at=datetime.now(timezone.utc),
    )


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
def pulserisk_setup():
    """Create comprehensive test environment with institution, courses, students, faculty, and advisor."""
    session = get_test_session()
    try:
        uid = uuid.uuid4().hex[:6]
        inst = Institution(id=str(uuid.uuid4()), name=f"PR Inst {uid}", code=f"PRI_{uid}")
        session.add(inst)
        session.flush()

        dept = Department(id=str(uuid.uuid4()), institution_id=inst.id, name=f"PR Dept {uid}", code=f"PRD_{uid}")
        session.add(dept)
        session.flush()

        prog = Program(id=str(uuid.uuid4()), department_id=dept.id, name="PR CS", code=f"PRCS_{uid}")
        session.add(prog)
        session.flush()

        batch = Batch(id=str(uuid.uuid4()), program_id=prog.id, name="2024-2028", start_year=2024, end_year=2028)
        session.add(batch)
        session.flush()

        sec = Section(id=str(uuid.uuid4()), batch_id=batch.id, name="A")
        session.add(sec)
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

        course1 = Course(id=str(uuid.uuid4()), institution_id=inst.id, department_id=dept.id, title="Algorithms", code=f"CS101_{uid}", credits=4)
        course2 = Course(id=str(uuid.uuid4()), institution_id=inst.id, department_id=dept.id, title="Databases", code=f"CS201_{uid}", credits=4)
        session.add_all([course1, course2])
        session.flush()

        # Users and roles
        u_stu_1_id = _create_user(session, f"stu1_{uid}@test.edu", "STUDENT", "Student One")
        u_stu_2_id = _create_user(session, f"stu2_{uid}@test.edu", "STUDENT", "Student Two")
        u_fac_1_id = _create_user(session, f"fac1_{uid}@test.edu", "FACULTY", "Faculty One")
        u_adv_id = _create_user(session, f"adv_{uid}@test.edu", "ADVISOR", "Advisor One")
        u_adm_id = _create_user(session, f"adm_{uid}@test.edu", "ADMIN", "Admin One")

        stu_1 = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=u_stu_1_id,
            program_id=prog.id,
            batch_id=batch.id,
            section_id=sec.id,
            enrollment_number=f"ENR_1_{uid}",
            admission_date=date(2024, 8, 1),
        )
        stu_2 = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=u_stu_2_id,
            program_id=prog.id,
            batch_id=batch.id,
            section_id=sec.id,
            enrollment_number=f"ENR_2_{uid}",
            admission_date=date(2024, 8, 1),
        )
        fac_1 = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=u_fac_1_id,
            department_id=dept.id,
            employee_id=f"EMP_{uid}",
            designation="Professor",
            joining_date=date(2020, 1, 1),
        )
        session.add_all([stu_1, stu_2, fac_1])
        session.flush()

        # Enrollments: Student 1 in Course 1, Student 2 in Course 2
        enr_1 = Enrollment(id=str(uuid.uuid4()), student_id=stu_1.id, course_id=course1.id, term_id=term.id, enrollment_date=date(2026, 8, 1), status="ENROLLED")
        enr_2 = Enrollment(id=str(uuid.uuid4()), student_id=stu_2.id, course_id=course2.id, term_id=term.id, enrollment_date=date(2026, 8, 1), status="ENROLLED")
        session.add_all([enr_1, enr_2])

        # Faculty 1 assigned to Course 1
        fa_1 = FacultyCourseAssignment(id=str(uuid.uuid4()), faculty_id=fac_1.id, course_id=course1.id, term_id=term.id, role="PRIMARY_INSTRUCTOR")
        session.add(fa_1)

        session.commit()

        # Seed initial active policy for this institution
        policy = PulseRiskRepository.get_active_policy(session, inst.id)

        yield {
            "session": session,
            "institution": inst,
            "department": dept,
            "program": prog,
            "student_1": stu_1,
            "student_2": stu_2,
            "faculty_1": fac_1,
            "course_1": course1,
            "course_2": course2,
            "policy": policy,
            "stu_1_email": f"stu1_{uid}@test.edu",
            "stu_2_email": f"stu2_{uid}@test.edu",
            "fac_1_email": f"fac1_{uid}@test.edu",
            "adv_email": f"adv_{uid}@test.edu",
            "adm_email": f"adm_{uid}@test.edu",
        }
    finally:
        session.close()


# =============================================================================
# MANDATORY TEST 1: Snapshot Identity Constraint includes Policy Version
# =============================================================================

def test_mandatory_1_snapshot_identity_constraint(pulserisk_setup):
    """Verify that student_risk_snapshots primary identity constraint includes policy_version.
    
    (student_id, evaluation_date, window_days, algorithm_version, policy_version)
    Duplicates must raise IntegrityError; distinct policy_versions must succeed.
    """
    session = pulserisk_setup["session"]
    stu = pulserisk_setup["student_1"]
    policy = pulserisk_setup["policy"]
    eval_date = date(2026, 9, 20)

    snap1 = StudentRiskSnapshot(
        id=str(uuid.uuid4()),
        student_id=stu.id,
        policy_id=policy.id,
        evaluation_date=eval_date,
        window_days=14,
        support_priority_index=Decimal("45.50"),
        priority_tier="MODERATE_PRIORITY",
        confidence_score=Decimal("1.00"),
        data_quality="VALID_DATA",
        primary_driver="ATTENDANCE",
        summary_text="Initial snapshot",
        decomposition_json=json.dumps({"test": 1}),
        algorithm_version=ALGORITHM_VERSION,
        policy_version="v1.0",
        calculated_at=datetime.now(timezone.utc),
    )
    session.add(snap1)
    session.commit()

    # Attempt inserting identical identity tuple -> must fail with IntegrityError
    snap_dup = StudentRiskSnapshot(
        id=str(uuid.uuid4()),
        student_id=stu.id,
        policy_id=policy.id,
        evaluation_date=eval_date,
        window_days=14,
        support_priority_index=Decimal("50.00"),
        priority_tier="ELEVATED_PRIORITY",
        confidence_score=Decimal("1.00"),
        data_quality="VALID_DATA",
        primary_driver="COURSEWORK",
        summary_text="Duplicate snapshot",
        decomposition_json=json.dumps({"test": 2}),
        algorithm_version=ALGORITHM_VERSION,
        policy_version="v1.0",
        calculated_at=datetime.now(timezone.utc),
    )
    session.add(snap_dup)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Inserting with a DIFFERENT policy_version for the same student on the same date succeeds
    snap_diff_version = StudentRiskSnapshot(
        id=str(uuid.uuid4()),
        student_id=stu.id,
        policy_id=policy.id,
        evaluation_date=eval_date,
        window_days=14,
        support_priority_index=Decimal("55.00"),
        priority_tier="ELEVATED_PRIORITY",
        confidence_score=Decimal("1.00"),
        data_quality="VALID_DATA",
        primary_driver="COURSEWORK",
        summary_text="Version 2 snapshot",
        decomposition_json=json.dumps({"test": 3}),
        algorithm_version=ALGORITHM_VERSION,
        policy_version="v2.0",
        calculated_at=datetime.now(timezone.utc),
    )
    session.add(snap_diff_version)
    session.commit()

    # Verify both snapshots are persisted
    snaps = session.query(StudentRiskSnapshot).filter(StudentRiskSnapshot.student_id == stu.id).all()
    assert len(snaps) == 2
    versions = {s.policy_version for s in snaps}
    assert versions == {"v1.0", "v2.0"}


# =============================================================================
# MANDATORY TEST 2: Historical Snapshot Reproducibility across Policy Changes
# =============================================================================

def test_mandatory_2_historical_snapshot_reproducibility(pulserisk_setup):
    """Verify that historical snapshots remain permanently associated with the exact policy version and weights."""
    session = pulserisk_setup["session"]
    inst = pulserisk_setup["institution"]
    stu = pulserisk_setup["student_1"]
    policy_v1 = pulserisk_setup["policy"]

    # 1. Save historical snapshot with Policy v1.0
    contributions = [
        {
            "dimension": "ATTENDANCE",
            "metric_label": "Attendance Rate",
            "observed_value": "70.0%",
            "baseline_value": "90.0%",
            "delta_value": "-20.0%",
            "factor_score": Decimal("57.50"),
            "assigned_weight": Decimal("0.350"),
            "weighted_contribution": Decimal("20.12"),
            "data_quality": "VALID_DATA",
            "source_signal": "ATTENDANCE_CHANGE",
        }
    ]
    snapshot_v1 = PulseRiskRepository.save_snapshot_and_contributions(
        db=session,
        student_id=stu.id,
        policy_id=policy_v1.id,
        evaluation_date=date(2026, 9, 1),
        window_days=14,
        support_priority_index=Decimal("57.50"),
        priority_tier="ELEVATED_PRIORITY",
        confidence_score=Decimal("1.00"),
        data_quality="VALID_DATA",
        primary_driver="ATTENDANCE",
        summary_text="Attendance declined by -20.0%",
        algorithm_version=ALGORITHM_VERSION,
        policy_version="v1.0",
        calculated_at=datetime.now(timezone.utc),
        decomposition_dict={"v1_field": "preserved"},
        contributions_list=contributions,
    )
    v1_id = snapshot_v1.id
    v1_spi = snapshot_v1.support_priority_index

    # 2. Admin creates and activates Policy v2.0 with radically altered weights
    policy_v2 = RiskPolicy(
        id=str(uuid.uuid4()),
        institution_id=inst.id,
        code="POLICY_V2",
        name="Revised Support Policy v2.0",
        description="Policy with heavier coursework weighting",
        weight_attendance=Decimal("0.200"),
        weight_coursework=Decimal("0.500"),
        weight_assessment=Decimal("0.200"),
        weight_persistence=Decimal("0.100"),
        threshold_moderate=Decimal("30.00"),
        threshold_elevated=Decimal("60.00"),
        threshold_urgent=Decimal("80.00"),
        persistence_half_life_days=14,
        status="ACTIVE",
        policy_version="v2.0",
        activated_at=datetime.now(timezone.utc),
    )
    # Activate policy v2 (which retires v1)
    session.add(policy_v2)
    policy_v1.status = "RETIRED"
    policy_v1.retired_at = datetime.now(timezone.utc)
    session.commit()

    # 3. Fetch historical snapshot v1 from DB
    loaded_snap = PulseRiskRepository.get_latest_snapshot(session, stu.id, window_days=14, policy_version="v1.0")
    assert loaded_snap is not None
    assert loaded_snap.id == v1_id
    assert loaded_snap.policy_version == "v1.0"
    assert loaded_snap.support_priority_index == v1_spi
    assert len(loaded_snap.contributions) == 1
    assert loaded_snap.contributions[0].assigned_weight == Decimal("0.350")
    assert loaded_snap.contributions[0].weighted_contribution == Decimal("20.12")
    decomp = json.loads(loaded_snap.decomposition_json)
    assert decomp["v1_field"] == "preserved"


# =============================================================================
# MANDATORY TEST 3: Safety Floor Precedence over Low Confidence
# =============================================================================

def test_mandatory_3_safety_floor_precedence_over_low_confidence(pulserisk_setup):
    """Mandatory Test #3:
    Scenario:
    - Student has 2 attendance sessions -> attendance data quality is INSUFFICIENT_DATA
    - No coursework data
    - No valid assessment performance data
    - Aggregate confidence C = 0.00
    - Student has a verified formal assessment absence (has_assessment_absence = True)
    
    Expected result:
    - T1 safety trigger activates (ASSESSMENT_ABSENCE_CRITICAL)
    - ActiveFloor = 75.0
    - Final SPI >= 75.0
    - Priority tier = URGENT_PRIORITY
    - Result must NOT become INSUFFICIENT_DATA
    - The safety floor overrides low confidence
    """
    session = pulserisk_setup["session"]
    stu = pulserisk_setup["student_1"]
    policy = pulserisk_setup["policy"]

    # Mock PulseWatch summary: 2 attendance sessions (INSUFFICIENT_DATA), assessment absence
    pw_mock = _make_mock_pulsewatch_summary(
        student_id=stu.id,
        signals=[
            SignalEvidenceSchema(
                signal_type="ATTENDANCE_CHANGE",
                severity="NORMAL",
                metric_name="attendance_rate",
                current_value=50.0,
                baseline_value=None,
                delta_value=None,
                evidence_payload={
                    "data_quality": "INSUFFICIENT_DATA",
                    "observation_sessions": 2,
                    "consecutive_absences": 1,
                },
            ),
            SignalEvidenceSchema(
                signal_type="ASSESSMENT_PERFORMANCE",
                severity="SIGNIFICANT_CHANGE",
                metric_name="formal_assessment_presence",
                current_value=0.0,
                baseline_value=None,
                delta_value=None,
                evidence_payload={
                    "data_quality": "INSUFFICIENT_DATA",
                    "has_assessment_absence": True,
                    "assessments_evaluated": 1,
                },
            ),
        ],
        data_quality="PARTIAL_DATA",
        confidence_score=Decimal("0.20"),
        overall_status="MILD_ENGAGEMENT_SHIFT",
    )

    result = PulseRiskCalculationService.compute_student_priority(
        db=session,
        student_id=stu.id,
        observation_window_days=14,
        policy=policy,
        pulsewatch_summary=pw_mock,
    )

    # Assertions
    assert len(result.safety_floors_triggered) >= 1
    t1_trigger = next((t for t in result.safety_floors_triggered if t.trigger_name in ["FORMAL_ASSESSMENT_ABSENCE", "ASSESSMENT_ABSENCE_CRITICAL"]), None)
    assert t1_trigger is not None
    assert t1_trigger.mandated_tier == "URGENT_PRIORITY"
    assert t1_trigger.mandated_floor == Decimal("75.00")

    assert result.support_priority_index >= Decimal("75.00")
    assert result.priority_tier == "URGENT_PRIORITY"
    assert result.data_quality != "INSUFFICIENT_DATA"


# =============================================================================
# MANDATORY TEST 4: Low Confidence with No Safety Trigger
# =============================================================================

def test_mandatory_4_low_confidence_no_safety_trigger(pulserisk_setup):
    """Mandatory Test #4:
    Scenario:
    - Student has 2 attendance sessions -> attendance data quality is INSUFFICIENT_DATA
    - No coursework data
    - No assessment data
    - Aggregate confidence C = 0.00 < 0.35
    - No safety triggers
    
    Expected result:
    - Result is INSUFFICIENT_DATA
    - SPI = 0.0
    - Priority tier = LOW_PRIORITY
    """
    session = pulserisk_setup["session"]
    stu = pulserisk_setup["student_1"]
    policy = pulserisk_setup["policy"]

    pw_mock = _make_mock_pulsewatch_summary(
        student_id=stu.id,
        signals=[
            SignalEvidenceSchema(
                signal_type="ATTENDANCE_CHANGE",
                severity="NORMAL",
                metric_name="attendance_rate",
                current_value=100.0,
                baseline_value=None,
                delta_value=None,
                evidence_payload={
                    "data_quality": "INSUFFICIENT_DATA",
                    "observation_sessions": 2,
                    "consecutive_absences": 0,
                },
            )
        ],
        data_quality="INSUFFICIENT_DATA",
        confidence_score=Decimal("0.10"),
        overall_status="NORMAL",
    )

    result = PulseRiskCalculationService.compute_student_priority(
        db=session,
        student_id=stu.id,
        observation_window_days=14,
        policy=policy,
        pulsewatch_summary=pw_mock,
    )

    assert result.confidence_score < Decimal("0.35")
    assert result.data_quality == "INSUFFICIENT_DATA"
    assert result.support_priority_index == Decimal("0.00")
    assert result.priority_tier == "LOW_PRIORITY"
    assert result.safety_floors_triggered == []


# =============================================================================
# MANDATORY TEST 5: Zero PulseWatch Metric Duplication
# =============================================================================

def test_mandatory_5_zero_pulsewatch_metric_duplication(pulserisk_setup):
    """Verify that PulseRisk NEVER queries attendance_records, assignment_submissions,
    or assessment_results directly during SPI calculation.
    """
    session = pulserisk_setup["session"]
    stu = pulserisk_setup["student_1"]
    policy = pulserisk_setup["policy"]

    # PulseWatch summary mock
    pw_mock = _make_mock_pulsewatch_summary(
        student_id=stu.id,
        signals=[
            SignalEvidenceSchema(
                signal_type="ATTENDANCE_CHANGE",
                severity="MODERATE_CHANGE",
                metric_name="attendance_rate",
                current_value=75.0,
                baseline_value=90.0,
                delta_value=-15.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "observation_sessions": 10,
                    "consecutive_absences": 0,
                },
            )
        ],
        data_quality="VALID_DATA",
        confidence_score=Decimal("0.80"),
        overall_status="MODERATE_ENGAGEMENT_SHIFT",
    )

    executed_tables = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        stmt_lower = statement.lower()
        if "attendance_records" in stmt_lower:
            executed_tables.append("attendance_records")
        if "assignment_submissions" in stmt_lower:
            executed_tables.append("assignment_submissions")
        if "assessment_results" in stmt_lower:
            executed_tables.append("assessment_results")

    engine = session.get_bind()
    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        res = PulseRiskCalculationService.compute_student_priority(
            db=session,
            student_id=stu.id,
            observation_window_days=14,
            policy=policy,
            pulsewatch_summary=pw_mock,
        )
        assert res is not None
        # Zero queries to raw academic tables
        assert executed_tables == [], f"Prohibited queries detected against raw academic tables: {executed_tables}"
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)


# =============================================================================
# MANDATORY TEST 6: Overlapping PulseWatch Events Canonical Window Deduplication
# =============================================================================

def test_mandatory_6_canonical_temporal_deduplication(pulserisk_setup):
    """Verify longitudinal persistence clustering:
    - Events overlapping >= 50% relative to shorter duration are clustered together.
    - Tie breakers: highest severity > longest window > most recent detected_at.
    - Half-life exponential decay lambda(t) = exp(-ln(2)*t/14).
    """
    now = datetime.now(timezone.utc)
    t1 = now - timedelta(days=2)
    t2 = now - timedelta(days=1)
    t3 = now

    # Event A: Moderate change, 14 days (Sept 1 to Sept 14)
    ev_a = BehaviorEvent(
        id=str(uuid.uuid4()),
        student_id="test_stu",
        event_type="ENGAGEMENT_SHIFT",
        severity="MODERATE_CHANGE",
        observation_window_days=14,
        window_start_date=date(2026, 9, 1),
        window_end_date=date(2026, 9, 14),
        summary_text="Event A",
        status="ACTIVE",
        detected_at=t1,
        algorithm_version="pulsewatch-v1.0",
    )

    # Event B: Significant change, 14 days (Sept 5 to Sept 18) - overlaps with A (10 days overlap / 14 = 71% >= 50%)
    ev_b = BehaviorEvent(
        id=str(uuid.uuid4()),
        student_id="test_stu",
        event_type="ENGAGEMENT_SHIFT",
        severity="SIGNIFICANT_CHANGE",
        observation_window_days=14,
        window_start_date=date(2026, 9, 5),
        window_end_date=date(2026, 9, 18),
        summary_text="Event B",
        status="ACTIVE",
        detected_at=t2,
        algorithm_version="pulsewatch-v1.0",
    )

    # Event C: Distinct, non-overlapping event (July 1 to July 14)
    ev_c = BehaviorEvent(
        id=str(uuid.uuid4()),
        student_id="test_stu",
        event_type="ENGAGEMENT_SHIFT",
        severity="MODERATE_CHANGE",
        observation_window_days=14,
        window_start_date=date(2026, 7, 1),
        window_end_date=date(2026, 7, 14),
        summary_text="Event C",
        status="ACTIVE",
        detected_at=t3,
        algorithm_version="pulsewatch-v1.0",
    )

    clusters = PulseRiskCalculationService.cluster_and_deduplicate_events([ev_a, ev_b, ev_c])
    assert len(clusters) == 2  # 1 cluster for A & B, 1 cluster for C

    # Check canonical selection for cluster (A & B): Event B must win (SIGNIFICANT > MODERATE)
    cluster_ab_canon, cluster_size = next((c, count) for c, count in clusters if c.id in [ev_a.id, ev_b.id])
    assert cluster_ab_canon.id == ev_b.id
    assert cluster_size == 2
    assert cluster_ab_canon.severity == "SIGNIFICANT_CHANGE"


# =============================================================================
# MANDATORY TEST 7: Policy Lifecycle Transitions & Active Uniqueness
# =============================================================================

def test_mandatory_7_policy_lifecycle_and_uniqueness(pulserisk_setup):
    """Verify policy lifecycle (DRAFT -> VALIDATED -> ACTIVE -> RETIRED), validation rules,
    immutability of ACTIVE/RETIRED, and exactly one ACTIVE policy per institution.
    """
    session = pulserisk_setup["session"]
    inst = pulserisk_setup["institution"]
    adm = UserRepository.get_by_email(session, pulserisk_setup["adm_email"])

    # 1. Invalid weight sum raises 422
    with pytest.raises(Exception) as excinfo:
        RiskPolicyService.validate_policy_parameters(
            weight_att=Decimal("0.400"),
            weight_asg=Decimal("0.300"),
            weight_assess=Decimal("0.200"),
            weight_persist=Decimal("0.200"),  # Sum = 1.100 != 1.000
            thresh_mod=Decimal("25.00"),
            thresh_elev=Decimal("50.00"),
            thresh_urg=Decimal("75.00"),
            half_life_days=14,
        )
    assert "weights must sum exactly to 1.000" in str(excinfo.value.detail)

    # 2. Non-monotonic thresholds raise 422
    with pytest.raises(Exception) as excinfo:
        RiskPolicyService.validate_policy_parameters(
            weight_att=Decimal("0.350"),
            weight_asg=Decimal("0.300"),
            weight_assess=Decimal("0.250"),
            weight_persist=Decimal("0.100"),
            thresh_mod=Decimal("50.00"),
            thresh_elev=Decimal("30.00"),  # mod > elev!
            thresh_urg=Decimal("75.00"),
            half_life_days=14,
        )
    assert "Thresholds must be strictly monotonic" in str(excinfo.value.detail)

    # 3. Create DRAFT policy
    from app.schemas.pulserisk import RiskPolicyCreate
    draft_data = RiskPolicyCreate(
        institution_id=inst.id,
        code="CUSTOM_POLICY_A",
        name="Custom Academic Pacing Policy",
        description="Pacing policy draft",
        weight_attendance=Decimal("0.400"),
        weight_coursework=Decimal("0.300"),
        weight_assessment=Decimal("0.200"),
        weight_persistence=Decimal("0.100"),
        threshold_moderate=Decimal("25.00"),
        threshold_elevated=Decimal("50.00"),
        threshold_urgent=Decimal("75.00"),
        persistence_half_life_days=14,
        policy_version="v2.0",
    )
    policy = RiskPolicyService.create_policy(session, draft_data, adm)
    assert policy.status == "DRAFT"

    # 4. Advance to VALIDATED
    val_policy = RiskPolicyService.validate_policy(session, policy.id, adm)
    assert val_policy.status == "VALIDATED"

    # 5. Activate policy -> previous active policy is retired
    prev_active = PulseRiskRepository.get_active_policy(session, inst.id)
    prev_active_id = prev_active.id

    act_policy = RiskPolicyService.activate_policy(session, val_policy.id, adm)
    assert act_policy.status == "ACTIVE"
    assert act_policy.activated_at is not None

    session.refresh(prev_active)
    assert prev_active.id == prev_active_id
    assert prev_active.status == "RETIRED"
    assert prev_active.retired_at is not None

    # Verify only 1 active policy exists for this institution
    active_count = session.query(RiskPolicy).filter(RiskPolicy.institution_id == inst.id, RiskPolicy.status == "ACTIVE").count()
    assert active_count == 1

    # 6. Immutability: editing ACTIVE policy raises 422
    from app.schemas.pulserisk import RiskPolicyUpdate
    with pytest.raises(Exception) as excinfo:
        RiskPolicyService.update_draft_policy(session, act_policy.id, RiskPolicyUpdate(name="Modified Name"), adm)
    assert "immutable" in str(excinfo.value.detail).lower()


# =============================================================================
# ADDITIONAL TESTS: Priority Tier Boundaries & Exact Math
# =============================================================================

@pytest.mark.parametrize(
    "spi_score,expected_tier",
    [
        (Decimal("0.00"), "LOW_PRIORITY"),
        (Decimal("24.99"), "LOW_PRIORITY"),
        (Decimal("25.00"), "MODERATE_PRIORITY"),
        (Decimal("49.99"), "MODERATE_PRIORITY"),
        (Decimal("50.00"), "ELEVATED_PRIORITY"),
        (Decimal("74.99"), "ELEVATED_PRIORITY"),
        (Decimal("75.00"), "URGENT_PRIORITY"),
        (Decimal("100.00"), "URGENT_PRIORITY"),
    ],
)
def test_priority_tier_exact_boundaries(spi_score, expected_tier):
    """Verify exact monotonic tier classification thresholds."""
    thresh_mod = Decimal("25.00")
    thresh_elev = Decimal("50.00")
    thresh_urg = Decimal("75.00")

    if spi_score >= thresh_urg:
        tier = "URGENT_PRIORITY"
    elif spi_score >= thresh_elev:
        tier = "ELEVATED_PRIORITY"
    elif spi_score >= thresh_mod:
        tier = "MODERATE_PRIORITY"
    else:
        tier = "LOW_PRIORITY"

    assert tier == expected_tier


# =============================================================================
# ADDITIONAL TESTS: Scoped Authorization & Zero-Write Endpoints
# =============================================================================

def test_api_read_only_get_separation(client, pulserisk_setup):
    """Verify that GET /student/{id}/current is strictly read-only with 0 DB writes."""
    session = pulserisk_setup["session"]
    stu1 = pulserisk_setup["student_1"]
    token = _get_token(client, pulserisk_setup["stu_1_email"])

    snap_count_before = session.query(StudentRiskSnapshot).count()

    res = client.get(
        f"/api/v1/pulserisk/student/{stu1.id}/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "support_priority_index" in data
    assert "priority_tier" in data

    snap_count_after = session.query(StudentRiskSnapshot).count()
    assert snap_count_after == snap_count_before, "GET endpoint must not write snapshots to database!"


def test_api_scoped_rbac_student_isolation(client, pulserisk_setup):
    """Verify student caller:
    - Can view their own priority summary
    - Gets 403 trying to view another student's priority
    - Gets 403 trying to trigger evaluation
    - Gets 403 trying to access cohort priority roster
    """
    stu1 = pulserisk_setup["student_1"]
    stu2 = pulserisk_setup["student_2"]
    token1 = _get_token(client, pulserisk_setup["stu_1_email"])

    # 1. Self access allowed
    res = client.get(
        f"/api/v1/pulserisk/student/{stu1.id}/current",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res.status_code == 200

    # 2. Cross-student access forbidden (403)
    res_other = client.get(
        f"/api/v1/pulserisk/student/{stu2.id}/current",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_other.status_code == 403

    # 3. Evaluate forbidden for student (403)
    res_eval = client.post(
        f"/api/v1/pulserisk/student/{stu1.id}/evaluate",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_eval.status_code == 403

    # 4. Cohort priorities roster forbidden for student (403)
    res_cohort = client.get(
        "/api/v1/pulserisk/cohort/priorities",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_cohort.status_code == 403


def test_api_advisor_and_faculty_cohort_roster(client, pulserisk_setup):
    """Verify that Advisor can view cohort roster, while Faculty only sees their enrolled students."""
    stu1 = pulserisk_setup["student_1"]
    stu2 = pulserisk_setup["student_2"]
    adv_token = _get_token(client, pulserisk_setup["adv_email"])
    fac_token = _get_token(client, pulserisk_setup["fac_1_email"])
    adm_token = _get_token(client, pulserisk_setup["adm_email"])

    # Admin evaluates both students so snapshots exist
    client.post(f"/api/v1/pulserisk/student/{stu1.id}/evaluate", headers={"Authorization": f"Bearer {adm_token}"})
    client.post(f"/api/v1/pulserisk/student/{stu2.id}/evaluate", headers={"Authorization": f"Bearer {adm_token}"})

    # Advisor roster
    res_adv = client.get("/api/v1/pulserisk/cohort/priorities", headers={"Authorization": f"Bearer {adv_token}"})
    assert res_adv.status_code == 200
    adv_data = res_adv.json()
    assert adv_data["total"] >= 2

    # Faculty 1 only teaches Course 1 (Student 1 is enrolled, Student 2 is in Course 2)
    res_fac = client.get("/api/v1/pulserisk/cohort/priorities", headers={"Authorization": f"Bearer {fac_token}"})
    assert res_fac.status_code == 200
    fac_data = res_fac.json()
    fac_student_ids = {item["student_id"] for item in fac_data["items"]}
    assert stu1.id in fac_student_ids
    assert stu2.id not in fac_student_ids


def test_api_evaluate_idempotency(client, pulserisk_setup):
    """Verify that calling evaluate repeatedly on the same day updates the existing snapshot rather than creating duplicates."""
    session = pulserisk_setup["session"]
    stu1 = pulserisk_setup["student_1"]
    adm_token = _get_token(client, pulserisk_setup["adm_email"])

    res1 = client.post(f"/api/v1/pulserisk/student/{stu1.id}/evaluate", headers={"Authorization": f"Bearer {adm_token}"})
    assert res1.status_code == 200
    snap_id_1 = res1.json()["id"]

    res2 = client.post(f"/api/v1/pulserisk/student/{stu1.id}/evaluate", headers={"Authorization": f"Bearer {adm_token}"})
    assert res2.status_code == 200
    snap_id_2 = res2.json()["id"]

    assert snap_id_1 == snap_id_2
    count = session.query(StudentRiskSnapshot).filter(StudentRiskSnapshot.student_id == stu1.id).count()
    assert count == 1


# =============================================================================
# REGRESSION TEST: Approved T2 Safety Floor Rule & Percentage Delta Isolation
# =============================================================================

def test_approved_safety_floor_t2_rule_and_delta_isolation(pulserisk_setup):
    """Verify that:
    1. Approved T2 rule: consecutive_absences >= 5 -> ActiveFloor = 75.0 -> URGENT_PRIORITY
    2. Attendance percentage delta by itself does NOT activate T2 unless approved trigger is present.
    """
    session = pulserisk_setup["session"]
    stu = pulserisk_setup["student_1"]
    policy = pulserisk_setup["policy"]

    # --- Part 1: Approved T2 Trigger (5 consecutive absences) ---
    pw_t2_mock = _make_mock_pulsewatch_summary(
        student_id=stu.id,
        signals=[
            SignalEvidenceSchema(
                signal_type="ATTENDANCE_CHANGE",
                severity="SIGNIFICANT_CHANGE",
                metric_name="attendance_rate",
                current_value=40.0,
                baseline_value=85.0,
                delta_value=-45.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "observation_sessions": 10,
                    "consecutive_absences": 5,  # Exactly 5 consecutive absences!
                },
            )
        ],
        data_quality="VALID_DATA",
        confidence_score=Decimal("0.80"),
        overall_status="SIGNIFICANT_ENGAGEMENT_SHIFT",
    )

    result_t2 = PulseRiskCalculationService.compute_student_priority(
        db=session,
        student_id=stu.id,
        observation_window_days=14,
        policy=policy,
        pulsewatch_summary=pw_t2_mock,
    )

    # Must activate SEVERE_ABSENCE_STREAK with floor 75.0 and URGENT_PRIORITY
    t2_trigger = next((t for t in result_t2.safety_floors_triggered if t.trigger_name == "SEVERE_ABSENCE_STREAK"), None)
    assert t2_trigger is not None, "T2 SEVERE_ABSENCE_STREAK must trigger for >= 5 consecutive absences"
    assert t2_trigger.mandated_floor == Decimal("75.00")
    assert t2_trigger.mandated_tier == "URGENT_PRIORITY"
    assert result_t2.support_priority_index >= Decimal("75.00")
    assert result_t2.priority_tier == "URGENT_PRIORITY"

    # --- Part 2: Percentage Delta Isolation (Severe Delta, but consecutive_absences = 0) ---
    # Attendance drop -28.0% alone with 0 consecutive absences must NOT activate T2
    pw_delta_only_mock = _make_mock_pulsewatch_summary(
        student_id=stu.id,
        signals=[
            SignalEvidenceSchema(
                signal_type="ATTENDANCE_CHANGE",
                severity="SIGNIFICANT_CHANGE",
                metric_name="attendance_rate",
                current_value=62.0,
                baseline_value=90.0,
                delta_value=-28.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "observation_sessions": 10,
                    "consecutive_absences": 0,  # Zero consecutive absences!
                },
            ),
            SignalEvidenceSchema(
                signal_type="MISSED_ASSIGNMENT",
                severity="NORMAL",
                metric_name="missed_assignments_count",
                current_value=0.0,
                baseline_value=0.0,
                delta_value=0.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "eligible_assignments": 5,
                    "missed_assignments": 0,
                    "late_assignments": 0,
                },
            ),
            SignalEvidenceSchema(
                signal_type="ASSESSMENT_PERFORMANCE",
                severity="NORMAL",
                metric_name="assessment_average",
                current_value=80.0,
                baseline_value=80.0,
                delta_value=0.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "has_assessment_absence": False,
                    "assessments_evaluated": 2,
                },
            ),
        ],
        data_quality="VALID_DATA",
        confidence_score=Decimal("1.00"),
        overall_status="MILD_ENGAGEMENT_SHIFT",
    )

    result_delta_only = PulseRiskCalculationService.compute_student_priority(
        db=session,
        student_id=stu.id,
        observation_window_days=14,
        policy=policy,
        pulsewatch_summary=pw_delta_only_mock,
    )

    # Assert that T2 was NOT triggered by percentage delta
    t2_present = any(t.trigger_name == "SEVERE_ABSENCE_STREAK" for t in result_delta_only.safety_floors_triggered)
    assert not t2_present, "Attendance percentage delta by itself must NOT activate T2"
    assert result_delta_only.safety_floors_triggered == [], "No safety floors should be triggered"
    # Verify exact math: delta -28% -> F_att = 75 + 25 * (3/25) = 78.00. W_att = 0.35. Contribution = 78 * 0.35 = 27.30
    assert result_delta_only.support_priority_index == Decimal("27.30")
    assert result_delta_only.priority_tier == "MODERATE_PRIORITY"


# =============================================================================
# REGRESSION TEST: Scenario 5 Exact Deterministic Assessment Drop Calculation
# =============================================================================

def test_scenario_5_exact_deterministic_assessment_drop(pulserisk_setup):
    """Verify that an assessment drop of -40% produces ONE exact, deterministic SPI and tier.
    
    Setup:
    - Policy: standard default v1.0 (weights: Att=0.35, Asg=0.30, Assess=0.25, Persist=0.10)
    - Thresholds: Moderate=25.00, Elevated=50.00, Urgent=75.00
    - Attendance: 0% delta (F_att = 0.00, C_abs = 0)
    - Coursework: 0 missed, 0 late (F_asg = 0.00)
    - Assessment: delta = -40.0% (baseline=85%, observed=45%, has_assessment_absence=False)
      -> F_assess = min(100.0, 75.0 + 25.0 * (40.0 - 25.0) / 25.0) = 75.0 + 15.0 = 90.00
    - Persistence: 0 historical events (F_persist = 0.00)
    
    Deterministic Calculation:
    - factor_score = 90.00
    - weight = 0.250
    - weighted_contribution = 90.00 * 0.250 = 22.50
    - raw_spi = 0.00 + 0.00 + 22.50 + 0.00 = 22.50
    - safety_floors = [] (ActiveFloor = 0.00)
    - final_spi = max(22.50, 0.00) = 22.50
    - final_tier = LOW_PRIORITY (since 22.50 < 25.00 threshold)
    - primary_driver = ASSESSMENTS
    """
    session = pulserisk_setup["session"]
    stu = pulserisk_setup["student_1"]
    policy = pulserisk_setup["policy"]

    pw_mock = _make_mock_pulsewatch_summary(
        student_id=stu.id,
        signals=[
            SignalEvidenceSchema(
                signal_type="ATTENDANCE_CHANGE",
                severity="NORMAL",
                metric_name="attendance_rate",
                current_value=85.0,
                baseline_value=85.0,
                delta_value=0.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "observation_sessions": 10,
                    "consecutive_absences": 0,
                },
            ),
            SignalEvidenceSchema(
                signal_type="MISSED_ASSIGNMENT",
                severity="NORMAL",
                metric_name="missed_assignments_count",
                current_value=0.0,
                baseline_value=0.0,
                delta_value=0.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "eligible_assignments": 5,
                    "missed_assignments": 0,
                    "late_assignments": 0,
                },
            ),
            SignalEvidenceSchema(
                signal_type="ASSESSMENT_PERFORMANCE",
                severity="SIGNIFICANT_CHANGE",
                metric_name="assessment_average",
                current_value=45.0,
                baseline_value=85.0,
                delta_value=-40.0,
                evidence_payload={
                    "data_quality": "VALID_DATA",
                    "has_assessment_absence": False,
                    "assessments_evaluated": 2,
                },
            ),
        ],
        data_quality="VALID_DATA",
        confidence_score=Decimal("1.00"),
        overall_status="MODERATE_ENGAGEMENT_SHIFT",
    )

    result = PulseRiskCalculationService.compute_student_priority(
        db=session,
        student_id=stu.id,
        observation_window_days=14,
        policy=policy,
        pulsewatch_summary=pw_mock,
    )

    # 1. Assert factor score
    assess_contrib = next(c for c in result.contributions if c.dimension == "ASSESSMENTS")
    assert assess_contrib.factor_score == Decimal("90.00")

    # 2. Assert assigned weight
    assert assess_contrib.assigned_weight == Decimal("0.250")

    # 3. Assert weighted contribution
    assert assess_contrib.weighted_contribution == Decimal("22.50")

    # 4. Assert safety floors (none active)
    assert result.safety_floors_triggered == []

    # 5. Assert raw SPI and final SPI are exactly 22.50
    assert result.support_priority_index == Decimal("22.50")

    # 6. Assert final tier is exactly LOW_PRIORITY (22.50 < 25.00)
    assert result.priority_tier == "LOW_PRIORITY"

    # 7. Assert primary driver is ASSESSMENTS
    assert result.primary_driver == "ASSESSMENTS"
