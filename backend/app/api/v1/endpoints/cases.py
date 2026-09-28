"""PulseCase API endpoints for CampusPulse."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_active_user, require_permission
from app.core.database import get_db
from app.models.user import User
from app.repositories.pulsecase_repo import PulseCaseRepository
from app.schemas.pulsecase import (
    CaseAssignRequest,
    CaseCloseRequest,
    CaseCreateRequest,
    CaseFollowUpCreateRequest,
    CaseFollowUpResponse,
    CaseFollowUpUpdateRequest,
    CaseInterventionCreateRequest,
    CaseInterventionResponse,
    CaseInterventionUpdateRequest,
    CaseNoteCreateRequest,
    CaseNoteResponse,
    CaseResolveRequest,
    CaseStatusUpdateRequest,
    FacultyReferralCreateRequest,
    FacultyReferralReceiptResponse,
    StudentSupportSummaryResponse,
    SupportCaseDetailResponse,
    SupportCaseResponse,
)
from app.services.pulsecase_service import PulseCaseService

router = APIRouter()


@router.post("/", response_model=SupportCaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreateRequest,
    current_user: User = Depends(require_permission("cases:create")),
    db: Session = Depends(get_db),
):
    """Directly open an intervention case (Advisor or Admin)."""
    case = PulseCaseService.create_case(db, current_user, payload)
    return PulseCaseService.project_case_response(case, current_user)


@router.post("/referrals", response_model=FacultyReferralReceiptResponse, status_code=status.HTTP_201_CREATED)
def submit_referral(
    payload: FacultyReferralCreateRequest,
    current_user: User = Depends(require_permission("cases:refer")),
    db: Session = Depends(get_db),
):
    """Submit an academic advising referral (Faculty)."""
    case = PulseCaseService.create_referral(db, current_user, payload)
    return FacultyReferralReceiptResponse(
        id=case.id,
        case_number=case.case_number,
        student_id=case.student_id,
        student_name=case.student.user.full_name if case.student and case.student.user else None,
        case_type=case.case_type,
        status=case.status,
        priority=case.priority,
        created_at=case.created_at,
        closed_at=case.closed_at,
        resolution_outcome=case.resolution_outcome,
    )


@router.get("/referrals/my", response_model=List[FacultyReferralReceiptResponse])
def get_own_referrals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("cases:refer")),
    db: Session = Depends(get_db),
):
    """List advising referrals submitted by caller (Faculty view)."""
    return PulseCaseService.faculty_referral_projection(db, current_user, skip=skip, limit=limit)


@router.get("/student/my-support", response_model=StudentSupportSummaryResponse)
def get_student_support_summary(
    current_user: User = Depends(require_permission("cases:read_own")),
    db: Session = Depends(get_db),
):
    """Student self-service overview: action items and upcoming appointments only."""
    return PulseCaseService.student_support_projection(db, current_user)


@router.get("/students/{student_id}/history", response_model=List[SupportCaseResponse])
def get_student_case_history(
    student_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    """List historical cases for a student for recurrence tracking."""
    user_perms = current_user.permission_codes
    if "cases:read_all" not in user_perms and "cases:read_assigned" not in user_perms and "SUPER_ADMIN" not in current_user.role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires permission cases:read_all or cases:read_assigned.",
        )
    return PulseCaseService.get_student_case_history(db, current_user, student_id)


@router.get("/", response_model=List[SupportCaseResponse])
def list_cases(
    student_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    case_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_staff_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    """List intervention cases scoped by caller role and assignments."""
    user_perms = current_user.permission_codes
    has_read_all = "cases:read_all" in user_perms or "SUPER_ADMIN" in current_user.role_names
    has_read_assigned = "cases:read_assigned" in user_perms

    if not has_read_all and not has_read_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires permission cases:read_all or cases:read_assigned.",
        )

    inst_id = PulseCaseService._resolve_institution_id(db, current_user)

    staff_filter = assigned_staff_id
    if not has_read_all:
        staff_filter = current_user.id

    cases = PulseCaseRepository.list_cases(
        db=db,
        institution_id=inst_id,
        student_id=student_id,
        assigned_staff_id=staff_filter,
        status=status_filter,
        case_type=case_type,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    return [PulseCaseService.project_case_response(c, current_user) for c in cases]


@router.get("/{case_id}", response_model=SupportCaseDetailResponse)
def get_case_detail(
    case_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    """Get complete case detail with confidential notes filtered by caller authorization."""
    user_perms = current_user.permission_codes
    has_read_all = "cases:read_all" in user_perms or "SUPER_ADMIN" in current_user.role_names
    has_read_assigned = "cases:read_assigned" in user_perms

    if not has_read_all and not has_read_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires permission cases:read_all or cases:read_assigned.",
        )

    case = PulseCaseRepository.get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    # Scoped verification
    inst_id = PulseCaseService._resolve_institution_id(db, current_user)
    if case.institution_id != inst_id and "SUPER_ADMIN" not in current_user.role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden across institutions.",
        )

    if not has_read_all and case.assigned_staff_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are only authorized to view cases assigned to you.",
        )

    return PulseCaseService.project_case_detail_response(db, case, current_user)


@router.patch("/{case_id}/assign", response_model=SupportCaseResponse)
def assign_case_handler(
    case_id: str,
    payload: CaseAssignRequest,
    current_user: User = Depends(require_permission("cases:assign")),
    db: Session = Depends(get_db),
):
    """Assign or reassign staff handler to a case."""
    case = PulseCaseService.assign_case(db, current_user, case_id, payload)
    return PulseCaseService.project_case_response(case, current_user)


@router.patch("/{case_id}/status", response_model=SupportCaseResponse)
def update_case_status(
    case_id: str,
    payload: CaseStatusUpdateRequest,
    current_user: User = Depends(require_permission("cases:write_assigned")),
    db: Session = Depends(get_db),
):
    """Advance case lifecycle status."""
    case = PulseCaseService.transition_case(db, current_user, case_id, payload)
    return PulseCaseService.project_case_response(case, current_user)


@router.post("/{case_id}/resolve", response_model=SupportCaseResponse)
def resolve_case(
    case_id: str,
    payload: CaseResolveRequest,
    current_user: User = Depends(require_permission("cases:write_assigned")),
    db: Session = Depends(get_db),
):
    """Resolve case with documented outcome."""
    case = PulseCaseService.resolve_case(db, current_user, case_id, payload)
    return PulseCaseService.project_case_response(case, current_user)


@router.post("/{case_id}/close", response_model=SupportCaseResponse)
def close_case(
    case_id: str,
    payload: CaseCloseRequest,
    current_user: User = Depends(require_permission("cases:close")),
    db: Session = Depends(get_db),
):
    """Permanently close and archive a resolved case."""
    case = PulseCaseService.close_case(db, current_user, case_id, payload)
    return PulseCaseService.project_case_response(case, current_user)


# ============================================================================
# Notes Endpoints
# ============================================================================

@router.post("/{case_id}/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
def add_case_note(
    case_id: str,
    payload: CaseNoteCreateRequest,
    current_user: User = Depends(require_permission("cases:write_assigned")),
    db: Session = Depends(get_db),
):
    """Add timestamped note with confidentiality classification."""
    note = PulseCaseService.add_note(db, current_user, case_id, payload)
    return CaseNoteResponse(
        id=note.id,
        case_id=note.case_id,
        author_user_id=note.author_user_id,
        author_name=current_user.full_name,
        note_type=note.note_type,
        confidentiality_level=note.confidentiality_level,
        content=note.content,
        created_at=note.created_at,
    )


@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
def get_case_notes(
    case_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    """List case notes, redacting COUNSELOR_CONFIDENTIAL notes for unauthorized callers."""
    user_perms = current_user.permission_codes
    if "cases:read_all" not in user_perms and "cases:read_assigned" not in user_perms and "SUPER_ADMIN" not in current_user.role_names:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires permission cases:read_all or cases:read_assigned.",
        )
    notes = PulseCaseService.get_case_notes(db, current_user, case_id)
    return [
        CaseNoteResponse(
            id=n.id,
            case_id=n.case_id,
            author_user_id=n.author_user_id,
            author_name=n.author.full_name if n.author else None,
            note_type=n.note_type,
            confidentiality_level=n.confidentiality_level,
            content=n.content,
            created_at=n.created_at,
        )
        for n in notes
    ]


# ============================================================================
# Interventions Endpoints
# ============================================================================

@router.post("/{case_id}/interventions", response_model=CaseInterventionResponse, status_code=status.HTTP_201_CREATED)
def add_case_intervention(
    case_id: str,
    payload: CaseInterventionCreateRequest,
    current_user: User = Depends(require_permission("cases:write_assigned")),
    db: Session = Depends(get_db),
):
    """Add action plan item to case."""
    item = PulseCaseService.add_intervention(db, current_user, case_id, payload)
    return CaseInterventionResponse(
        id=item.id,
        case_id=item.case_id,
        intervention_type=item.intervention_type,
        title=item.title,
        description=item.description,
        assigned_to_user_id=item.assigned_to_user_id,
        target_completion_date=item.target_completion_date,
        status=item.status,
        completed_at=item.completed_at,
        outcome_notes=item.outcome_notes,
        created_at=item.created_at,
    )


@router.patch("/{case_id}/interventions/{item_id}", response_model=CaseInterventionResponse)
def update_case_intervention(
    case_id: str,
    item_id: str,
    payload: CaseInterventionUpdateRequest,
    current_user: User = Depends(require_permission("cases:write_assigned")),
    db: Session = Depends(get_db),
):
    """Update intervention status and completion notes."""
    item = PulseCaseService.update_intervention(db, current_user, item_id, payload)
    return CaseInterventionResponse(
        id=item.id,
        case_id=item.case_id,
        intervention_type=item.intervention_type,
        title=item.title,
        description=item.description,
        assigned_to_user_id=item.assigned_to_user_id,
        target_completion_date=item.target_completion_date,
        status=item.status,
        completed_at=item.completed_at,
        outcome_notes=item.outcome_notes,
        created_at=item.created_at,
    )


# ============================================================================
# Follow-Ups Endpoints
# ============================================================================

@router.post("/{case_id}/follow-ups", response_model=CaseFollowUpResponse, status_code=status.HTTP_201_CREATED)
def schedule_follow_up(
    case_id: str,
    payload: CaseFollowUpCreateRequest,
    current_user: User = Depends(require_permission("cases:write_assigned")),
    db: Session = Depends(get_db),
):
    """Schedule follow-up evaluation meeting."""
    follow_up = PulseCaseService.add_follow_up(db, current_user, case_id, payload)
    return CaseFollowUpResponse(
        id=follow_up.id,
        case_id=follow_up.case_id,
        scheduled_date=follow_up.scheduled_date,
        scheduled_time=follow_up.scheduled_time,
        follow_up_type=follow_up.follow_up_type,
        assigned_staff_id=follow_up.assigned_staff_id,
        status=follow_up.status,
        notes=follow_up.notes,
        completed_at=follow_up.completed_at,
        created_at=follow_up.created_at,
    )


@router.patch("/{case_id}/follow-ups/{follow_up_id}", response_model=CaseFollowUpResponse)
def update_follow_up(
    case_id: str,
    follow_up_id: str,
    payload: CaseFollowUpUpdateRequest,
    current_user: User = Depends(require_permission("cases:write_assigned")),
    db: Session = Depends(get_db),
):
    """Record follow-up session outcome."""
    follow_up = PulseCaseService.update_follow_up(db, current_user, follow_up_id, payload)
    return CaseFollowUpResponse(
        id=follow_up.id,
        case_id=follow_up.case_id,
        scheduled_date=follow_up.scheduled_date,
        scheduled_time=follow_up.scheduled_time,
        follow_up_type=follow_up.follow_up_type,
        assigned_staff_id=follow_up.assigned_staff_id,
        status=follow_up.status,
        notes=follow_up.notes,
        completed_at=follow_up.completed_at,
        created_at=follow_up.created_at,
    )
