"""PulseRisk API Endpoints.

Provides scoped, auditable endpoints for Support Priority Index (SPI) summaries,
historical snapshot trajectories, cohort triage rosters, and institutional risk policy governance.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.academic_deps import verify_student_record_access
from app.core.auth_deps import get_current_user, require_role
from app.core.database import get_db
from app.models.pulserisk import RiskPolicy, StudentRiskSnapshot
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.repositories.pulserisk_repo import PulseRiskRepository
from app.schemas.pulserisk import (
    CohortPrioritiesPageResponse,
    CohortPriorityItemResponse,
    PulseRiskSummaryResponse,
    RiskPolicyCreate,
    RiskPolicyResponse,
    RiskPolicyUpdate,
    RiskSignalContributionSchema,
    StudentRiskSnapshotResponse,
)
from app.services.pulserisk_calculation_service import (
    ALGORITHM_VERSION,
    PulseRiskCalculationService,
)
from app.services.risk_policy_service import RiskPolicyService

router = APIRouter()


def _map_snapshot_to_response(snapshot: StudentRiskSnapshot) -> StudentRiskSnapshotResponse:
    """Helper to convert StudentRiskSnapshot ORM model and child contributions into response schema."""
    contrib_schemas = []
    for c in snapshot.contributions:
        details = None
        if c.evidence_payload_json:
            try:
                details = json.loads(c.evidence_payload_json)
            except Exception:
                details = None
        contrib_schemas.append(
            RiskSignalContributionSchema(
                dimension=c.dimension,
                metric_label=c.metric_label,
                observed_value=c.observed_value,
                baseline_value=c.baseline_value,
                delta_value=c.delta_value,
                factor_score=c.factor_score,
                assigned_weight=c.assigned_weight,
                weighted_contribution=c.weighted_contribution,
                data_quality=c.data_quality,
                source_signal=c.source_signal,
                context_details=details,
            )
        )
    return StudentRiskSnapshotResponse(
        id=snapshot.id,
        student_id=snapshot.student_id,
        policy_id=snapshot.policy_id,
        evaluation_date=snapshot.evaluation_date,
        window_days=snapshot.window_days,
        support_priority_index=snapshot.support_priority_index,
        priority_tier=snapshot.priority_tier,
        confidence_score=snapshot.confidence_score,
        data_quality=snapshot.data_quality,
        primary_driver=snapshot.primary_driver,
        summary_text=snapshot.summary_text,
        status=snapshot.status,
        algorithm_version=snapshot.algorithm_version,
        policy_version=snapshot.policy_version,
        calculated_at=snapshot.calculated_at,
        contributions=contrib_schemas,
    )


def _resolve_caller_institution_id(db: Session, current_user: User) -> str:
    """Resolve institution ID for the caller or fallback to the primary active institution."""
    role_names = set(current_user.role_names)
    if "STUDENT" in role_names:
        prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if prof and prof.program and prof.program.department_id:
            dept = AcademicRepository.get_department_by_id(db, prof.program.department_id)
            if dept:
                return dept.institution_id
    elif "FACULTY" in role_names:
        fac = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if fac and fac.department_id:
            dept = AcademicRepository.get_department_by_id(db, fac.department_id)
            if dept:
                return dept.institution_id

    institutions = AcademicRepository.get_institutions(db)
    if institutions:
        return institutions[0].id
    return "default_inst"


# -----------------------------------------------------------------------------
# 1. Student Support Priority Summary (Read-Only)
# -----------------------------------------------------------------------------

@router.get(
    "/student/{student_id}/current",
    response_model=PulseRiskSummaryResponse,
    summary="Get current student Support Priority Index decomposition (Read-Only)",
)
def get_student_current_pulserisk(
    student_id: str,
    window_days: int = Query(14, ge=7, le=60, description="Observation window duration in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PulseRiskSummaryResponse:
    """Compute current deterministic SPI decomposition for an authorized student.
    
    Strictly read-only with zero database write side-effects.
    """
    verify_student_record_access(current_user, student_id, db)

    student = AcademicRepository.get_student_profile_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    return PulseRiskCalculationService.compute_student_priority(
        db=db,
        student_id=student_id,
        observation_window_days=window_days,
    )


# -----------------------------------------------------------------------------
# 2. Historical Snapshots Trajectory
# -----------------------------------------------------------------------------

@router.get(
    "/student/{student_id}/history",
    response_model=List[StudentRiskSnapshotResponse],
    summary="Get student historical SPI snapshots",
)
def get_student_pulserisk_history(
    student_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum snapshots to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[StudentRiskSnapshotResponse]:
    """Retrieve chronological history of persisted SPI snapshots for trajectory analysis."""
    verify_student_record_access(current_user, student_id, db)

    student = AcademicRepository.get_student_profile_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    snapshots = PulseRiskRepository.get_snapshots_history(db, student_id=student_id, limit=limit)
    return [_map_snapshot_to_response(s) for s in snapshots]


# -----------------------------------------------------------------------------
# 3. Idempotent Priority Evaluation & Persistence
# -----------------------------------------------------------------------------

@router.post(
    "/student/{student_id}/evaluate",
    response_model=StudentRiskSnapshotResponse,
    summary="Evaluate and idempotently persist SPI snapshot",
)
def evaluate_and_persist_student_priority(
    student_id: str,
    window_days: int = Query(14, ge=7, le=60, description="Observation window duration in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentRiskSnapshotResponse:
    """Compute and persist an SPI evaluation snapshot with full auditable JSON decomposition.
    
    Authorized for Advisors, Administrators, and assigned Faculty only.
    """
    role_names = set(current_user.role_names)
    if "STUDENT" in role_names and not any(r in role_names for r in ["SUPER_ADMIN", "ADMIN", "ADVISOR", "FACULTY"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students may not trigger formal evaluation runs",
        )

    verify_student_record_access(current_user, student_id, db)

    student = AcademicRepository.get_student_profile_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    # Compute priority
    summary = PulseRiskCalculationService.compute_student_priority(
        db=db,
        student_id=student_id,
        observation_window_days=window_days,
    )

    institution_id = _resolve_caller_institution_id(db, current_user)
    active_policy = PulseRiskRepository.get_active_policy(db, institution_id)

    contributions_data = [
        {
            "dimension": c.dimension,
            "metric_label": c.metric_label,
            "observed_value": c.observed_value,
            "baseline_value": c.baseline_value,
            "delta_value": c.delta_value,
            "factor_score": c.factor_score,
            "assigned_weight": c.assigned_weight,
            "weighted_contribution": c.weighted_contribution,
            "data_quality": c.data_quality,
            "source_signal": c.source_signal,
            "context_details": c.context_details,
        }
        for c in summary.contributions
    ]

    decomposition_dict = {
        "support_priority_index": float(summary.support_priority_index),
        "priority_tier": summary.priority_tier,
        "confidence_score": float(summary.confidence_score),
        "data_quality": summary.data_quality,
        "primary_driver": summary.primary_driver,
        "contributions": [c.model_dump(mode="json") for c in summary.contributions],
        "safety_floors_triggered": [sf.model_dump(mode="json") for sf in summary.safety_floors_triggered],
        "explainability": summary.explainability.model_dump(mode="json"),
    }

    snapshot = PulseRiskRepository.save_snapshot_and_contributions(
        db=db,
        student_id=student_id,
        policy_id=active_policy.id,
        evaluation_date=summary.evaluation_date,
        window_days=summary.observation_window_days,
        support_priority_index=summary.support_priority_index,
        priority_tier=summary.priority_tier,
        confidence_score=summary.confidence_score,
        data_quality=summary.data_quality,
        primary_driver=summary.primary_driver,
        summary_text=summary.explainability.summary,
        algorithm_version=summary.algorithm_version,
        policy_version=summary.policy_version,
        calculated_at=summary.calculated_at,
        decomposition_dict=decomposition_dict,
        contributions_list=contributions_data,
        input_snapshot_dict=None,
    )

    return _map_snapshot_to_response(snapshot)


# -----------------------------------------------------------------------------
# 4. Advisor / Cohort Support Priority Roster
# -----------------------------------------------------------------------------

@router.get(
    "/cohort/priorities",
    response_model=CohortPrioritiesPageResponse,
    summary="Get paginated cohort support priority triage roster",
)
def get_cohort_priorities(
    priority_tier: Optional[str] = Query(None, description="Filter by priority tier"),
    primary_driver: Optional[str] = Query(None, description="Filter by primary driver dimension"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CohortPrioritiesPageResponse:
    """Retrieve paginated support priority roster for advisors and academic staff.
    
    Students are strictly forbidden (403). Faculty receive only students enrolled in their courses.
    """
    role_names = set(current_user.role_names)

    if "STUDENT" in role_names and not any(r in role_names for r in ["SUPER_ADMIN", "ADMIN", "ADVISOR", "FACULTY"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students are not permitted to access cohort priority rosters",
        )

    student_ids: Optional[List[str]] = None

    if "FACULTY" in role_names and not any(r in role_names for r in ["SUPER_ADMIN", "ADMIN", "ADVISOR"]):
        fac_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not fac_prof:
            return CohortPrioritiesPageResponse(items=[], total=0, page=page, limit=limit, pages=0)

        assignments = AcademicRepository.get_faculty_assignments(db, faculty_id=fac_prof.id)
        if not assignments:
            return CohortPrioritiesPageResponse(items=[], total=0, page=page, limit=limit, pages=0)

        student_ids_set = set()
        for a in assignments:
            enrollments = AcademicRepository.get_enrollments(db, course_id=a.course_id)
            for e in enrollments:
                student_ids_set.add(e.student_id)

        student_ids = list(student_ids_set)
        if not student_ids:
            return CohortPrioritiesPageResponse(items=[], total=0, page=page, limit=limit, pages=0)

    items_data, total = PulseRiskRepository.get_cohort_priorities(
        db=db,
        student_ids=student_ids,
        priority_tier=priority_tier,
        primary_driver=primary_driver,
        page=page,
        limit=limit,
    )

    pages = (total + limit - 1) // limit if total > 0 else 0
    return CohortPrioritiesPageResponse(
        items=[CohortPriorityItemResponse(**d) for d in items_data],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


# -----------------------------------------------------------------------------
# 5. Risk Policy Governance
# -----------------------------------------------------------------------------

@router.get(
    "/policies/active",
    response_model=RiskPolicyResponse,
    summary="Get active institutional risk policy (Read-Only)",
)
def get_active_policy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskPolicyResponse:
    """Retrieve the currently active institutional risk policy.
    
    Accessible to all authenticated users for algorithmic transparency and explainability.
    """
    institution_id = _resolve_caller_institution_id(db, current_user)
    policy = PulseRiskRepository.get_active_policy(db, institution_id)
    return RiskPolicyResponse.model_validate(policy)


@router.post(
    "/policies",
    response_model=RiskPolicyResponse,
    summary="Create a new risk policy in DRAFT status",
)
def create_policy(
    data: RiskPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> RiskPolicyResponse:
    """Create a new risk policy in DRAFT status. Restricted to Administrators."""
    policy = RiskPolicyService.create_policy(db, data, current_user)
    return RiskPolicyResponse.model_validate(policy)


@router.post(
    "/policies/{policy_id}/activate",
    response_model=RiskPolicyResponse,
    summary="Activate a risk policy",
)
def activate_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "SUPER_ADMIN")),
) -> RiskPolicyResponse:
    """Activate a validated policy and atomically retire the previous active policy.
    
    Restricted to Administrators.
    """
    policy = RiskPolicyService.activate_policy(db, policy_id, current_user)
    return RiskPolicyResponse.model_validate(policy)
